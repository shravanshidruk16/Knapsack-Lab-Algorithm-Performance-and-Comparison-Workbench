"""
Tests for input validation and memory bounds in services/validation.py.
"""

import pytest
import config
from services.validation import validate_solver_request, validate_benchmark_request

def test_valid_solver_input():
    payload = {
        "capacity": 50,
        "trials": 3,
        "items": [
            {"id": 1, "name": "Item 1", "weight": 10, "value": 60},
            {"id": 2, "name": "Item 2", "weight": 20, "value": 100}
        ]
    }
    is_valid, err, sanitized = validate_solver_request(payload)
    assert is_valid is True
    assert err is None
    assert sanitized["capacity"] == 50
    assert len(sanitized["items"]) == 2

def test_zero_capacity_rejected():
    payload = {"capacity": 0, "items": [{"id": 1, "weight": 10, "value": 60}]}
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False
    assert "positive integer greater than zero" in err

def test_negative_capacity_rejected():
    payload = {"capacity": -20, "items": [{"id": 1, "weight": 10, "value": 60}]}
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False

def test_negative_item_weight_rejected():
    payload = {"capacity": 50, "items": [{"id": 1, "weight": -5, "value": 60}]}
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False
    assert "positive integer" in err

def test_negative_item_value_rejected():
    payload = {"capacity": 50, "items": [{"id": 1, "weight": 10, "value": -100}]}
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False
    assert "positive integer" in err

def test_duplicate_item_id_rejected():
    payload = {
        "capacity": 50,
        "items": [
            {"id": "duplicate_id", "weight": 10, "value": 60},
            {"id": "duplicate_id", "weight": 20, "value": 100}
        ]
    }
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False
    assert "Duplicate item identifier" in err

def test_empty_items_accepted_as_zero_instance():
    payload = {"capacity": 50, "items": []}
    is_valid, err, sanitized = validate_solver_request(payload)
    assert is_valid is True
    assert len(sanitized["items"]) == 0

def test_dp_cell_memory_guard():
    # Capacity that would produce > 30 million cells
    payload = {
        "capacity": 2_000_000,
        "items": [{"id": i, "weight": 100, "value": 200} for i in range(25)]
    }
    is_valid, err, _ = validate_solver_request(payload)
    assert is_valid is False
    assert "exceeding the safety limit" in err

def test_benchmark_validation_bounds():
    # Valid
    ok, err, _ = validate_benchmark_request({
        "min_items": 5,
        "max_items": 20,
        "step_items": 5,
        "capacity": 100
    })
    assert ok is True

    # Min > Max
    ok, err, _ = validate_benchmark_request({
        "min_items": 30,
        "max_items": 10,
        "step_items": 5,
        "capacity": 100
    })
    assert ok is False
