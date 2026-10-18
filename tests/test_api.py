"""
End-to-end Flask API route tests.
"""

import json
import pytest

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ["healthy", "degraded"]
    assert "platform" in data
    assert data["runner_exists"] is True

def test_api_index_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Knapsack Lab" in res.data
    assert b"Dynamic Programming" in res.data
    assert b"Branch and Bound" in res.data

def test_api_samples(client):
    res = client.get("/api/samples")
    assert res.status_code == 200
    data = res.get_json()
    assert "presets" in data
    assert len(data["presets"]) >= 3

def test_api_solve_success(client):
    payload = {
        "capacity": 50,
        "trials": 1,
        "items": [
            {"id": 1, "name": "Item 1", "weight": 10, "value": 60},
            {"id": 2, "name": "Item 2", "weight": 20, "value": 100},
            {"id": 3, "name": "Item 3", "weight": 30, "value": 120}
        ]
    }
    res = client.post("/api/solve", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["verification"]["verified"] is True
    assert data["verification"]["agreement"] is True
    assert data["dp"]["optimal_value"] == 220
    assert data["branch_and_bound"]["optimal_value"] == 220

def test_api_solve_invalid_capacity(client):
    payload = {"capacity": -10, "items": [{"id": 1, "weight": 10, "value": 50}]}
    res = client.post("/api/solve", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "positive integer" in data["error"]

def test_api_generate(client):
    payload = {
        "item_count": 8,
        "capacity": 70,
        "min_weight": 10,
        "max_weight": 30,
        "min_value": 20,
        "max_value": 100,
        "seed": 55
    }
    res = client.post("/api/generate", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["dataset"]["items"]) == 8

def test_api_benchmark_endpoint(client):
    payload = {
        "min_items": 5,
        "max_items": 10,
        "step_items": 5,
        "capacity": 60,
        "seed": 42,
        "trials": 1
    }
    res = client.post("/api/benchmark", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["points"]) == 2
