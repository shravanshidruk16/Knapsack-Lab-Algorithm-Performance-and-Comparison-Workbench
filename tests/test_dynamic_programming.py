"""
Tests for C++17 Dynamic Programming implementation.
"""

import pytest
from services.benchmark import execute_runner_isolated

def test_dp_single_item_fits():
    items = [{"id": 1, "name": "Item 1", "weight": 10, "value": 50, "original_index": 0}]
    res = execute_runner_isolated("dp", items, capacity=15)
    assert res["success"] is True
    assert res["optimal_value"] == 50
    assert res["total_weight"] == 10
    assert res["selected_indices"] == [0]

def test_dp_single_item_exceeds():
    items = [{"id": 1, "name": "Item 1", "weight": 20, "value": 50, "original_index": 0}]
    res = execute_runner_isolated("dp", items, capacity=10)
    assert res["success"] is True
    assert res["optimal_value"] == 0
    assert res["total_weight"] == 0
    assert res["selected_indices"] == []

def test_dp_classic_textbook(sample_items):
    res = execute_runner_isolated("dp", sample_items, capacity=50)
    assert res["success"] is True
    # In classic 4-item instance: weights [10, 20, 30, 15], values [60, 100, 120, 70], W=50
    # Items 1, 2, 4 have weight 10+20+15 = 45, value 60+100+70 = 230! Or 2+3 (20+30=50, 100+120=220).
    # Let's check: 60+100+70 = 230 with weight 45 <= 50!
    assert res["optimal_value"] == 230
    assert res["total_weight"] == 45
    assert set(res["selected_indices"]) == {0, 1, 3}

def test_dp_all_items_fit():
    items = [
        {"id": 1, "name": "A", "weight": 5, "value": 10, "original_index": 0},
        {"id": 2, "name": "B", "weight": 5, "value": 20, "original_index": 1}
    ]
    res = execute_runner_isolated("dp", items, capacity=50)
    assert res["success"] is True
    assert res["optimal_value"] == 30
    assert res["total_weight"] == 10
    assert set(res["selected_indices"]) == {0, 1}

def test_dp_table_metrics():
    items = [
        {"id": 1, "name": "A", "weight": 5, "value": 10, "original_index": 0},
        {"id": 2, "name": "B", "weight": 10, "value": 20, "original_index": 1}
    ]
    res = execute_runner_isolated("dp", items, capacity=30)
    assert res["dp_rows"] == 3
    assert res["dp_cols"] == 31
    assert res["dp_table_entries"] == 93
    assert res["algorithm_workspace_bytes"] == 93 * 8
