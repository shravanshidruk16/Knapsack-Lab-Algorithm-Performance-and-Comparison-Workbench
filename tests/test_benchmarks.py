"""
Tests for benchmark sweep generator and execution pipeline.
"""

import pytest
from services.benchmark import generate_dataset, run_benchmark_suite
from services.validation import validate_benchmark_request

def test_dataset_reproducibility():
    """Verifies that the same seed produces identical items and weights."""
    ds1 = generate_dataset(15, 100, 10, 40, 20, 150, seed=12345)
    ds2 = generate_dataset(15, 100, 10, 40, 20, 150, seed=12345)
    assert ds1 == ds2
    assert len(ds1["items"]) == 15
    assert ds1["items"][0]["weight"] == ds2["items"][0]["weight"]

def test_different_seeds_produce_different_data():
    ds1 = generate_dataset(10, 100, 10, 40, 20, 150, seed=111)
    ds2 = generate_dataset(10, 100, 10, 40, 20, 150, seed=222)
    assert ds1["items"][0] != ds2["items"][0]

def test_benchmark_suite_execution():
    """Runs a small benchmark sweep and verifies collected points."""
    params = {
        "min_items": 5,
        "max_items": 15,
        "step_items": 5,
        "capacity": 80,
        "min_weight": 10,
        "max_weight": 35,
        "min_value": 20,
        "max_value": 100,
        "seed": 999,
        "trials": 1
    }
    res = run_benchmark_suite(params)
    assert res["success"] is True
    assert res["point_count"] == 3
    for pt in res["points"]:
        assert pt["dp_success"] is True
        assert pt["bb_success"] is True
        assert pt["agreement"] is True
        assert pt["dp_time_ms"] >= 0.0
        assert pt["bb_time_ms"] >= 0.0
