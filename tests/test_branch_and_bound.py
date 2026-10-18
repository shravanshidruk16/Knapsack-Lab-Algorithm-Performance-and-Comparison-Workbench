"""
Tests for C++17 Branch and Bound state-space tree search.
"""

import pytest
from services.benchmark import execute_runner_isolated

def test_bb_single_item_fits():
    items = [{"id": 1, "name": "Item 1", "weight": 10, "value": 50, "original_index": 0}]
    res = execute_runner_isolated("bb", items, capacity=15)
    assert res["success"] is True
    assert res["optimal_value"] == 50
    assert res["total_weight"] == 10
    assert res["selected_indices"] == [0]

def test_bb_single_item_exceeds():
    items = [{"id": 1, "name": "Item 1", "weight": 20, "value": 50, "original_index": 0}]
    res = execute_runner_isolated("bb", items, capacity=10)
    assert res["success"] is True
    assert res["optimal_value"] == 0
    assert res["total_weight"] == 0
    assert res["selected_indices"] == []

def test_bb_classic_textbook(sample_items):
    res = execute_runner_isolated("bb", sample_items, capacity=50)
    assert res["success"] is True
    assert res["optimal_value"] == 230
    assert res["total_weight"] == 45
    assert set(res["selected_indices"]) == {0, 1, 3}

def test_bb_node_pruning_and_tracking():
    # Instance with multiple items to observe non-zero pruning
    items = [
        {"id": 1, "name": "A", "weight": 10, "value": 60, "original_index": 0},
        {"id": 2, "name": "B", "weight": 20, "value": 100, "original_index": 1},
        {"id": 3, "name": "C", "weight": 30, "value": 120, "original_index": 2},
        {"id": 4, "name": "D", "weight": 15, "value": 70, "original_index": 3},
        {"id": 5, "name": "E", "weight": 25, "value": 90, "original_index": 4}
    ]
    res = execute_runner_isolated("bb", items, capacity=50)
    assert res["success"] is True
    assert res["nodes_expanded"] > 0
    assert res["nodes_generated"] > 0
    assert res["max_frontier_size"] >= 1
    assert "algorithm_workspace_bytes" in res
