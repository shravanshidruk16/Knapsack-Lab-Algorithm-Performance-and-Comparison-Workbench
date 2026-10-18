# Verification and Test Plan: Knapsack Lab

## 1. Test Strategy Overview

Knapsack Lab employs a multi-tiered test strategy ensuring mathematical algorithm correctness, input sanitization, and benchmark stability:
1. **Mathematical Ground Truth via Brute-Force Oracle:** Compares both C++ algorithms against an independent $2^N$ combinatorial search on small problem sizes ($N \le 12$).
2. **Dual-Algorithm Cross-Validation:** Confirms that DP and Branch & Bound output identical optimal objective values ($V^*_{\text{DP}} == V^*_{\text{BB}}$).
3. **Feasibility Checks:** Verifies that no item is duplicated, total selected weight $\le W$, and sum of selected values equals the reported optimum.
4. **Edge and Boundary Case Analysis:** Tests capacities of 0, 1, items exceeding capacity, all items fitting, identical item ratios, and empty item sets.
5. **Security and Memory Guard Testing:** Confirms that negative numbers, malformed JSON, duplicate IDs, and massive memory allocations are rejected with clear error messages.
6. **End-to-End API Route Testing:** Tests Flask health, solve, benchmark, and generator endpoints.

---

## 2. Test Cases and Execution Results

All 35 automated tests are executed using `pytest -v`:

| Category | Test Function | Purpose | Result |
| :--- | :--- | :--- | :--- |
| **Correctness Oracle** | `test_oracle_vs_both_algorithms[10]` | Ground truth comparison with Seed 10 | **PASSED** |
| **Correctness Oracle** | `test_oracle_vs_both_algorithms[42]` | Ground truth comparison with Seed 42 | **PASSED** |
| **Correctness Oracle** | `test_oracle_vs_both_algorithms[99]` | Ground truth comparison with Seed 99 | **PASSED** |
| **Correctness Oracle** | `test_oracle_vs_both_algorithms[123]` | Ground truth comparison with Seed 123 | **PASSED** |
| **Correctness Oracle** | `test_oracle_vs_both_algorithms[777]` | Ground truth comparison with Seed 777 | **PASSED** |
| **Corner Cases** | `test_heavy_item_exclusion_trap` | Correctly excludes oversized high-value item | **PASSED** |
| **Corner Cases** | `test_identical_ratio_items` | Stable tie-breaking for equal ratio items | **PASSED** |
| **Dynamic Programming** | `test_dp_single_item_fits` | Base case: single fitting item | **PASSED** |
| **Dynamic Programming** | `test_dp_single_item_exceeds` | Base case: single oversized item | **PASSED** |
| **Dynamic Programming** | `test_dp_classic_textbook` | Standard 4-item Cormen/CLRS instance | **PASSED** |
| **Dynamic Programming** | `test_dp_all_items_fit` | Boundary: all items included | **PASSED** |
| **Dynamic Programming** | `test_dp_table_metrics` | Validates DP table row/col and cell counts | **PASSED** |
| **Branch and Bound** | `test_bb_single_item_fits` | Base case: single fitting item | **PASSED** |
| **Branch and Bound** | `test_bb_single_item_exceeds` | Base case: single oversized item | **PASSED** |
| **Branch and Bound** | `test_bb_classic_textbook` | Standard 4-item instance | **PASSED** |
| **Branch and Bound** | `test_bb_node_pruning_and_tracking` | Confirms nodes expanded, generated, and pruned | **PASSED** |
| **Validation** | `test_valid_solver_input` | Validates acceptable JSON structure | **PASSED** |
| **Validation** | `test_zero_capacity_rejected` | Rejects capacity = 0 with descriptive error | **PASSED** |
| **Validation** | `test_negative_capacity_rejected` | Rejects capacity < 0 | **PASSED** |
| **Validation** | `test_negative_item_weight_rejected`| Rejects negative item weights | **PASSED** |
| **Validation** | `test_negative_item_value_rejected` | Rejects negative item values | **PASSED** |
| **Validation** | `test_duplicate_item_id_rejected` | Enforces unique item identifiers | **PASSED** |
| **Validation** | `test_empty_items_accepted` | Empty items returns optimal value 0 | **PASSED** |
| **Validation** | `test_dp_cell_memory_guard` | Rejects tables > 30M cells | **PASSED** |
| **Validation** | `test_benchmark_validation_bounds`| Rejects invalid benchmark ranges | **PASSED** |
| **Benchmarks** | `test_dataset_reproducibility` | Seed 12345 produces identical datasets | **PASSED** |
| **Benchmarks** | `test_different_seeds_distinct` | Different seeds yield distinct datasets | **PASSED** |
| **Benchmarks** | `test_benchmark_suite_execution` | Multi-size sweep collects valid metrics | **PASSED** |
| **Flask API** | `test_api_health` | Confirms C++17 runner health check | **PASSED** |
| **Flask API** | `test_api_index_html` | Confirms HTML shell rendering | **PASSED** |
| **Flask API** | `test_api_samples` | Confirms preset catalog delivery | **PASSED** |
| **Flask API** | `test_api_solve_success` | Full solve workflow execution | **PASSED** |
| **Flask API** | `test_api_solve_invalid_capacity`| 400 Bad Request on invalid capacity | **PASSED** |
| **Flask API** | `test_api_generate` | Endpoint returns random dataset | **PASSED** |
| **Flask API** | `test_api_benchmark_endpoint` | Endpoint runs parameter sweep | **PASSED** |

**Summary: 35 Tests Executed, 35 Passed (100% Success Rate).**
