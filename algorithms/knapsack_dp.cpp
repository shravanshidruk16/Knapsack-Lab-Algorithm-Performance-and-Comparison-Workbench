#include "knapsack_algorithms.h"
#include <algorithm>
#include <vector>
#include <iostream>
#include <stdexcept>

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#include <psapi.h>
#elif defined(__linux__) || defined(__APPLE__)
#include <sys/resource.h>
#include <unistd.h>
#endif

namespace knapsack {

// Maximum allowed cells in 2D DP table to prevent out-of-memory aborts (~240 MB for 64-bit integers)
constexpr size_t MAX_DP_TABLE_ENTRIES = 30000000ULL;

size_t get_peak_memory_bytes() {
#if defined(_WIN32) || defined(_WIN64)
    PROCESS_MEMORY_COUNTERS pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) {
        return static_cast<size_t>(pmc.PeakWorkingSetSize);
    }
    return 0;
#elif defined(__linux__)
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        // ru_maxrss is in kilobytes on Linux
        return static_cast<size_t>(usage.ru_maxrss) * 1024ULL;
    }
    return 0;
#elif defined(__APPLE__)
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        // ru_maxrss is in bytes on macOS
        return static_cast<size_t>(usage.ru_maxrss);
    }
    return 0;
#else
    return 0;
#endif
}

std::string get_memory_source_description() {
#if defined(_WIN32) || defined(_WIN64)
    return "Windows GetProcessMemoryInfo (PeakWorkingSet)";
#elif defined(__linux__)
    return "Linux getrusage (ru_maxrss * 1024 bytes)";
#elif defined(__APPLE__)
    return "macOS getrusage (ru_maxrss bytes)";
#else
    return "Platform Process Memory Measurement Unavailable";
#endif
}

KnapsackResult solve_dynamic_programming(const std::vector<Item>& items, long long capacity, int trials) {
    KnapsackResult result;
    result.algorithm_name = "Dynamic Programming";
    result.trials_conducted = std::max(1, trials);

    if (capacity < 0) {
        result.success = false;
        result.error_message = "Knapsack capacity cannot be negative.";
        return result;
    }

    const size_t n = items.size();
    const size_t cap = static_cast<size_t>(capacity);
    result.dp_rows = n + 1;
    result.dp_cols = cap + 1;

    // Safety guard against memory overflow
    unsigned long long total_cells = static_cast<unsigned long long>(n + 1) * static_cast<unsigned long long>(cap + 1);
    if (total_cells > MAX_DP_TABLE_ENTRIES) {
        result.success = false;
        result.error_message = "Requested DP table (" + std::to_string(total_cells) +
                               " cells) exceeds the safe memory allocation limit of " +
                               std::to_string(MAX_DP_TABLE_ENTRIES) + " cells.";
        return result;
    }

    result.dp_table_entries = static_cast<size_t>(total_cells);
    result.algorithm_workspace_bytes = result.dp_table_entries * sizeof(long long);

    // Handle edge case: empty items or capacity == 0
    if (n == 0 || capacity == 0) {
        result.success = true;
        result.optimal_value = 0;
        result.total_weight = 0;
        result.selected_count = 0;
        result.selected_indices.clear();
        result.execution_time_us = 0.5;
        result.execution_time_ms = 0.0005;
        result.peak_working_set_bytes = get_peak_memory_bytes();
        result.memory_source = get_memory_source_description();
        return result;
    }

    std::vector<double> trial_times_us;
    trial_times_us.reserve(result.trials_conducted);

    // Pre-allocate flat 2D DP table: dp[i * (cap + 1) + w]
    std::vector<long long> dp(total_cells, 0);

    for (int t = 0; t < result.trials_conducted; ++t) {
        MonotonicTimer timer;

        // Initialize table to 0
        std::fill(dp.begin(), dp.end(), 0LL);

        // Core DP Recurrence:
        // dp[i][w] = max(dp[i-1][w], dp[i-1][w - weight_i] + value_i)
        for (size_t i = 1; i <= n; ++i) {
            const long long item_weight = items[i - 1].weight;
            const long long item_value = items[i - 1].value;
            const size_t prev_row = (i - 1) * (cap + 1);
            const size_t curr_row = i * (cap + 1);

            for (size_t w = 0; w <= cap; ++w) {
                if (item_weight > static_cast<long long>(w)) {
                    dp[curr_row + w] = dp[prev_row + w];
                } else {
                    long long without_item = dp[prev_row + w];
                    long long with_item = dp[prev_row + (w - static_cast<size_t>(item_weight))] + item_value;
                    dp[curr_row + w] = (with_item > without_item) ? with_item : without_item;
                }
            }
        }

        double elapsed_us = timer.elapsed_microseconds();
        trial_times_us.push_back(elapsed_us);
    }

    // Compute median execution time across trials
    std::sort(trial_times_us.begin(), trial_times_us.end());
    result.execution_time_us = trial_times_us[trial_times_us.size() / 2];
    result.execution_time_ms = result.execution_time_us / 1000.0;

    // Backtrack to reconstruct selected items
    result.optimal_value = dp[n * (cap + 1) + cap];
    long long remaining_cap = capacity;
    std::vector<int> selected_rev;

    for (size_t i = n; i > 0 && remaining_cap > 0; --i) {
        size_t prev_row = (i - 1) * (cap + 1);
        size_t curr_row = i * (cap + 1);
        long long current_cell = dp[curr_row + remaining_cap];
        long long above_cell = dp[prev_row + remaining_cap];

        if (current_cell != above_cell) {
            // Item i-1 was included in the optimal knapsack subset
            selected_rev.push_back(items[i - 1].original_index);
            remaining_cap -= items[i - 1].weight;
        }
    }

    // Reverse to retain natural original order
    std::reverse(selected_rev.begin(), selected_rev.end());
    result.selected_indices = selected_rev;
    result.selected_count = result.selected_indices.size();

    // Calculate actual total weight of selected items
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
