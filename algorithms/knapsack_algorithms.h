#ifndef KNAPSACK_ALGORITHMS_H
#define KNAPSACK_ALGORITHMS_H

#include <string>
#include <vector>
#include <cstddef>
#include <chrono>

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#endif

namespace knapsack {

// High-resolution cross-platform monotonic timer
// Uses QueryPerformanceCounter on Windows for sub-microsecond resolution,
// and std::chrono::steady_clock on POSIX platforms.
class MonotonicTimer {
private:
#if defined(_WIN32) || defined(_WIN64)
    long long start_count;
    long long frequency;
#else
    std::chrono::time_point<std::chrono::steady_clock> start_tp;
#endif

public:
    MonotonicTimer() {
        reset();
    }

    void reset() {
#if defined(_WIN32) || defined(_WIN64)
        LARGE_INTEGER freq, count;
        QueryPerformanceFrequency(&freq);
        QueryPerformanceCounter(&count);
        frequency = freq.QuadPart;
        start_count = count.QuadPart;
#else
        start_tp = std::chrono::steady_clock::now();
#endif
    }

    double elapsed_microseconds() const {
#if defined(_WIN32) || defined(_WIN64)
        LARGE_INTEGER count;
        QueryPerformanceCounter(&count);
        if (frequency <= 0) return 0.0;
        return static_cast<double>(count.QuadPart - start_count) * 1000000.0 / static_cast<double>(frequency);
#else
        auto now = std::chrono::steady_clock::now();
        return std::chrono::duration<double, std::micro>(now - start_tp).count();
#endif
    }

    double elapsed_milliseconds() const {
        return elapsed_microseconds() / 1000.0;
    }
};

// Representation of a knapsack item
struct Item {
    int id;                     // 1-based or user identifier
    std::string name;           // Human readable label
    long long weight;           // Positive integer weight
    long long value;            // Positive integer value
    int original_index;         // 0-based index in the original input vector
    double ratio;               // value / weight

    Item() : id(0), name(""), weight(0), value(0), original_index(0), ratio(0.0) {}
    Item(int id_, const std::string& name_, long long w, long long v, int orig_idx)
        : id(id_), name(name_), weight(w), value(v), original_index(orig_idx) {
        ratio = (w > 0) ? (static_cast<double>(v) / static_cast<double>(w)) : 0.0;
    }
};

// Result structure capturing all required metrics and algorithm statistics
struct KnapsackResult {
    std::string algorithm_name;
    bool success;
    std::string error_message;

    long long optimal_value;
    long long total_weight;
    std::vector<int> selected_indices;   // Original 0-based indices of chosen items
    size_t selected_count;

    // High resolution timing
    double execution_time_us;            // Microseconds
    double execution_time_ms;            // Milliseconds
    int trials_conducted;

    // Memory measurements
    size_t peak_working_set_bytes;       // OS process peak working set / resident set
    size_t algorithm_workspace_bytes;    // Explicitly tracked algorithm data structures
    std::string memory_source;

    // Dynamic Programming specific metrics
    size_t dp_rows;                      // N + 1
    size_t dp_cols;                      // W + 1
    size_t dp_table_entries;             // Total cells computed

    // Branch and Bound specific metrics
    size_t nodes_expanded;               // Nodes popped and evaluated
    size_t nodes_generated;              // Feasible nodes pushed to frontier
    size_t nodes_pruned;                 // Infeasible or unpromising nodes pruned
    size_t max_frontier_size;            // Peak priority queue capacity used

    KnapsackResult()
        : algorithm_name(""), success(false), error_message(""),
          optimal_value(0), total_weight(0), selected_count(0),
          execution_time_us(0.0), execution_time_ms(0.0), trials_conducted(1),
          peak_working_set_bytes(0), algorithm_workspace_bytes(0), memory_source(""),
          dp_rows(0), dp_cols(0), dp_table_entries(0),
          nodes_expanded(0), nodes_generated(0), nodes_pruned(0), max_frontier_size(0) {}
};

// Memory utility returning peak working set size in bytes across platforms
size_t get_peak_memory_bytes();
std::string get_memory_source_description();

// Dynamic Programming 0/1 Knapsack Solver
// Time complexity: O(N * W), Space complexity: O(N * W)
KnapsackResult solve_dynamic_programming(const std::vector<Item>& items, long long capacity, int trials = 1);

// Branch and Bound 0/1 Knapsack Solver
// Best-first search with fractional knapsack relaxation heuristic
KnapsackResult solve_branch_and_bound(const std::vector<Item>& items, long long capacity, int trials = 1);

} // namespace knapsack

#endif // KNAPSACK_ALGORITHMS_H
