"""
Exhaustive correctness verification and brute-force oracle cross-validation.
Validates DP and Branch and Bound against mathematical ground truth across multiple instances.
"""

import itertools
import pytest
from services.benchmark import solve_both_algorithms, generate_dataset

def brute_force_oracle(items, capacity):
    """
    Independent test oracle that checks all 2^N combinations
    to determine the provable exact optimal 0/1 knapsack objective value.
    """
    n = len(items)
    best_value = 0
    best_weight = 0
    best_indices = []

    for r in range(n + 1):
        for combo in itertools.combinations(range(n), r):
            tot_w = sum(items[i]["weight"] for i in combo)
            tot_v = sum(items[i]["value"] for i in combo)
            if tot_w <= capacity:
                if tot_v > best_value:
                    best_value = tot_v
                    best_weight = tot_w
                    best_indices = list(combo)

    return best_value, best_weight, best_indices


@pytest.mark.parametrize("seed", [10, 42, 99, 123, 777])
def test_oracle_vs_both_algorithms(seed):
    """
    Tests both DP and B&B against the 2^N brute-force oracle across 5 distinct pseudo-random seeds.
    """
    capacity = 80
    data = generate_dataset(
        item_count=10,
        capacity=capacity,
        min_weight=10,
        max_weight=45,
        min_value=20,
        max_value=120,
        seed=seed
    )
    items = data["items"]

    oracle_val, oracle_w, oracle_sel = brute_force_oracle(items, capacity)

    res = solve_both_algorithms(items, capacity, trials=1)
    assert res["success"] is True

    ver = res["verification"]
    assert ver["verified"] is True
    assert ver["agreement"] is True
    assert ver["dp_valid"] is True
    assert ver["bb_valid"] is True

    dp_opt = res["dp"]["optimal_value"]
    bb_opt = res["branch_and_bound"]["optimal_value"]

    # Verify against independent oracle
    assert dp_opt == oracle_val, f"DP returned {dp_opt}, oracle computed {oracle_val}"
    assert bb_opt == oracle_val, f"BB returned {bb_opt}, oracle computed {oracle_val}"


def test_heavy_item_exclusion_trap():
    """
    Tests an instance where a single high-value item exceeds capacity.
    """
    items = [
        {"id": 1, "name": "Heavy Gold Ingot", "weight": 60, "value": 500, "original_index": 0},
        {"id": 2, "name": "Silver Coin", "weight": 20, "value": 150, "original_index": 1},
        {"id": 3, "name": "Bronze Cup", "weight": 25, "value": 160, "original_index": 2}
    ]
    res = solve_both_algorithms(items, capacity=50, trials=1)
    assert res["verification"]["verified"] is True
    assert res["dp"]["optimal_value"] == 310
    assert res["branch_and_bound"]["optimal_value"] == 310
    assert set(res["dp"]["selected_indices"]) == {1, 2}
    assert set(res["branch_and_bound"]["selected_indices"]) == {1, 2}


def test_identical_ratio_items():
    """
    Tests items with identical value/weight ratios to ensure stable tie-breaking.
    """
    items = [
        {"id": 1, "name": "Item A", "weight": 10, "value": 50, "original_index": 0},
        {"id": 2, "name": "Item B", "weight": 20, "value": 100, "original_index": 1},
        {"id": 3, "name": "Item C", "weight": 30, "value": 150, "original_index": 2}
    ]
    res = solve_both_algorithms(items, capacity=35, trials=1)
    assert res["verification"]["verified"] is True
    assert res["dp"]["optimal_value"] == 150
    assert res["branch_and_bound"]["optimal_value"] == 150
