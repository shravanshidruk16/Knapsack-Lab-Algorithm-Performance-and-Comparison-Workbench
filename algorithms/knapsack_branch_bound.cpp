#include "knapsack_algorithms.h"
#include <algorithm>
#include <vector>
#include <queue>
#include <cmath>

namespace knapsack {

struct BBNode {
    int level;                      // Index of item to consider next (0 to n)
    long long weight;               // Total weight of selected items
    long long value;                // Total value of selected items
    double bound;                   // Upper bound estimate (fractional relaxation)
    std::vector<int> selected;      // Original item indices included in this node

    // Priority queue max-heap comparator: highest bound has highest priority
    bool operator<(const BBNode& other) const {
        if (std::abs(bound - other.bound) > 1e-9) {
            return bound < other.bound; // Max-heap on bound
        }
        if (value != other.value) {
            return value < other.value; // Tie-breaker: prefer higher current value
        }
        return level < other.level;     // Tie-breaker: deeper node
    }
};

// Calculate optimistic upper bound using fractional knapsack relaxation on remaining items
static double compute_fractional_bound(
    int level,
    long long current_weight,
    long long current_value,
    long long capacity,
    const std::vector<Item>& sorted_items) {

    if (current_weight > capacity) {
        return 0.0;
    }

    double bound = static_cast<double>(current_value);
    long long total_weight = current_weight;
    const int n = static_cast<int>(sorted_items.size());

    for (int i = level; i < n; ++i) {
        if (total_weight + sorted_items[i].weight <= capacity) {
            total_weight += sorted_items[i].weight;
            bound += static_cast<double>(sorted_items[i].value);
        } else {
            // Take fractional proportion of the next item to saturate capacity
            long long remaining_capacity = capacity - total_weight;
            if (sorted_items[i].weight > 0) {
                bound += static_cast<double>(remaining_capacity) * sorted_items[i].ratio;
            }
            break;
        }
    }
    return bound;
}

KnapsackResult solve_branch_and_bound(const std::vector<Item>& items, long long capacity, int trials) {
    KnapsackResult result;
    result.algorithm_name = "Branch and Bound";
    result.trials_conducted = std::max(1, trials);

    if (capacity < 0) {
        result.success = false;
        result.error_message = "Knapsack capacity cannot be negative.";
        return result;
    }

    const size_t n = items.size();

    // Handle edge case: empty items or capacity == 0
    if (n == 0 || capacity == 0) {
        result.success = true;
        result.optimal_value = 0;
        result.total_weight = 0;
        result.selected_count = 0;
        result.selected_indices.clear();
        result.execution_time_us = 0.5;
        result.execution_time_ms = 0.0005;
        result.nodes_expanded = 0;
        result.nodes_generated = 0;
        result.nodes_pruned = 0;
        result.max_frontier_size = 0;
        result.peak_working_set_bytes = get_peak_memory_bytes();
        result.memory_source = get_memory_source_description();
        return result;
    }

    // Sort items by value/weight ratio descending, with deterministic tie-breakers
    std::vector<Item> sorted_items = items;
    std::sort(sorted_items.begin(), sorted_items.end(), [](const Item& a, const Item& b) {
        if (std::abs(a.ratio - b.ratio) > 1e-9) {
            return a.ratio > b.ratio; // Descending order of ratio
        }
        if (a.value != b.value) {
            return a.value > b.value; // Tie-breaker: higher value first
        }
        if (a.weight != b.weight) {
            return a.weight < b.weight; // Tie-breaker: lighter weight first
        }
        return a.original_index < b.original_index; // Preserve deterministic ordering
    });

    std::vector<double> trial_times_us;
    trial_times_us.reserve(result.trials_conducted);

    long long final_best_value = 0;
    std::vector<int> final_best_selected;
    size_t final_nodes_expanded = 0;
    size_t final_nodes_generated = 0;
    size_t final_nodes_pruned = 0;
    size_t final_max_frontier = 0;

    for (int t = 0; t < result.trials_conducted; ++t) {
        MonotonicTimer timer;

        // 1. Initial feasible solution via greedy ratio-based selection
        long long greedy_w = 0;
        long long greedy_v = 0;
        std::vector<int> greedy_selected;
        for (const auto& itm : sorted_items) {
            if (greedy_w + itm.weight <= capacity) {
                greedy_w += itm.weight;
                greedy_v += itm.value;
                greedy_selected.push_back(itm.original_index);
            }
        }

        long long best_value = greedy_v;
        std::vector<int> best_selected = greedy_selected;

        size_t nodes_expanded = 0;
        size_t nodes_generated = 0;
        size_t nodes_pruned = 0;
        size_t max_frontier = 0;

        // 2. Best-First Search Priority Queue (Max-Heap)
        std::priority_queue<BBNode> pq;

        // Root Node
        BBNode root;
        root.level = 0;
        root.weight = 0;
        root.value = 0;
        root.bound = compute_fractional_bound(0, 0, 0, capacity, sorted_items);
        root.selected.clear();

        // Check if root bound already proves the greedy solution is optimal
        if (root.bound <= static_cast<double>(best_value) + 1e-9) {
            // Greedy solution is provably optimal immediately!
            nodes_expanded = 1;
            nodes_generated = 1;
            nodes_pruned = 0;
            max_frontier = 0;
        } else {
            pq.push(root);
            nodes_generated = 1;
            max_frontier = 1;

            while (!pq.empty()) {
                max_frontier = std::max(max_frontier, pq.size());

                BBNode u = pq.top();
                pq.pop();

                // If upper bound of top node cannot beat best known value, prune entire remaining queue
                if (u.bound <= static_cast<double>(best_value) + 1e-9) {
                    nodes_pruned += (1 + pq.size());
                    break;
                }

                nodes_expanded++;

                if (u.level == static_cast<int>(n)) {
                    continue;
                }

                const Item& next_item = sorted_items[u.level];

                // --- Branch 1: Include next_item ---
                if (u.weight + next_item.weight <= capacity) {
                    BBNode left;
                    left.level = u.level + 1;
                    left.weight = u.weight + next_item.weight;
                    left.value = u.value + next_item.value;
                    left.selected = u.selected;
                    left.selected.push_back(next_item.original_index);

                    // Update best known feasible solution
                    if (left.value > best_value) {
                        best_value = left.value;
                        best_selected = left.selected;
                    }

                    left.bound = compute_fractional_bound(left.level, left.weight, left.value, capacity, sorted_items);

                    if (left.bound > static_cast<double>(best_value) + 1e-9) {
                        pq.push(left);
                        nodes_generated++;
                    } else {
                        nodes_pruned++;
                    }
                }

                // --- Branch 2: Exclude next_item ---
                BBNode right;
                right.level = u.level + 1;
                right.weight = u.weight;
                right.value = u.value;
                right.selected = u.selected;
                right.bound = compute_fractional_bound(right.level, right.weight, right.value, capacity, sorted_items);

                if (right.bound > static_cast<double>(best_value) + 1e-9) {
                    pq.push(right);
                    nodes_generated++;
                } else {
                    nodes_pruned++;
                }
            }
        }

        double elapsed_us = timer.elapsed_microseconds();
        trial_times_us.push_back(elapsed_us);

        final_best_value = best_value;
        final_best_selected = best_selected;
        final_nodes_expanded = nodes_expanded;
        final_nodes_generated = nodes_generated;
        final_nodes_pruned = nodes_pruned;
        final_max_frontier = max_frontier;
    }

    // Compute median execution time across trials
    std::sort(trial_times_us.begin(), trial_times_us.end());
    result.execution_time_us = trial_times_us[trial_times_us.size() / 2];
    result.execution_time_ms = result.execution_time_us / 1000.0;

    result.optimal_value = final_best_value;
    result.nodes_expanded = final_nodes_expanded;
    result.nodes_generated = final_nodes_generated;
    result.nodes_pruned = final_nodes_pruned;
    result.max_frontier_size = final_max_frontier;

    // Estimate algorithm workspace: peak queue footprint + items array
    result.algorithm_workspace_bytes = (final_max_frontier * sizeof(BBNode)) + (n * sizeof(Item));

    // Sort selected indices in natural ascending input order
    std::sort(final_best_selected.begin(), final_best_selected.end());
    result.selected_indices = final_best_selected;
    result.selected_count = result.selected_indices.size();

    // Compute total weight of selected items
    long long total_w = 0;
    for (int orig_idx : result.selected_indices) {
        for (const auto& itm : items) {
            if (itm.original_index == orig_idx) {
                total_w += itm.weight;
                break;
            }
        }
    }
    result.total_weight = total_w;
    result.peak_working_set_bytes = get_peak_memory_bytes();
    result.memory_source = get_memory_source_description();
    result.success = true;

    return result;
}

} // namespace knapsack
