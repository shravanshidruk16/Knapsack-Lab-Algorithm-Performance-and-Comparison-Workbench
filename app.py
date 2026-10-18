"""
Knapsack Lab — Flask Web Application
Algorithm Performance and Comparison Workbench for 0/1 Knapsack: DP vs. Branch and Bound.
"""

import os
import platform
import subprocess
from flask import Flask, render_template, request, jsonify

import config
from services.validation import validate_solver_request, validate_benchmark_request
from services.benchmark import solve_both_algorithms, run_benchmark_suite, generate_dataset

app = Flask(__name__)
app.config.from_object(config)


@app.route("/")
def index():
    """Renders the main single-page algorithm laboratory application."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """
    Checks the status of the Flask backend, host platform, and compiled C++ runner.
    """
    runner_exists = config.RUNNER_PATH.exists()
    runner_responsive = False
    runner_details = "Not found"

    if runner_exists:
        try:
            res = subprocess.run([str(config.RUNNER_PATH), "--health"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                runner_responsive = True
                runner_details = res.stdout.strip()
            else:
                runner_details = f"Exit code {res.returncode}: {res.stderr.strip()}"
        except Exception as e:
            runner_details = f"Execution error: {str(e)}"

    return jsonify({
        "status": "healthy" if (runner_exists and runner_responsive) else "degraded",
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "runner_path": str(config.RUNNER_PATH),
        "runner_exists": runner_exists,
        "runner_responsive": runner_responsive,
        "runner_details": runner_details,
        "max_capacity": config.MAX_CAPACITY,
        "max_items": config.MAX_ITEMS
    })


@app.route("/api/solve", methods=["POST"])
def solve():
    """
    Solves 0/1 Knapsack using both Dynamic Programming and Branch and Bound,
    cross-validates results, and returns comparative performance metrics.
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    is_valid, err_msg, sanitized = validate_solver_request(data)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    try:
        result = solve_both_algorithms(
            items=sanitized["items"],
            capacity=sanitized["capacity"],
            trials=sanitized["trials"],
            timeout=config.DEFAULT_EXECUTION_TIMEOUT
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal execution failure: {str(e)}"
        }), 500


@app.route("/api/benchmark", methods=["POST"])
def benchmark():
    """
    Runs an empirical benchmark sweep over configured problem sizes.
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    is_valid, err_msg, params = validate_benchmark_request(data)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    try:
        benchmark_results = run_benchmark_suite(params)
        return jsonify(benchmark_results), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Benchmark suite failed: {str(e)}"
        }), 500


@app.route("/api/samples", methods=["GET"])
def samples():
    """
    Returns curated, documented sample datasets demonstrating specific algorithmic behaviors.
    """
    presets = [
        {
            "id": "clrs_classic",
            "name": "Classic Textbook Instance (4 items)",
            "description": "Standard pedagogical 4-item problem with known optimum V* = 220, W = 50.",
            "capacity": 50,
            "items": [
                {"id": 1, "name": "Item 1", "weight": 10, "value": 60},
                {"id": 2, "name": "Item 2", "weight": 20, "value": 100},
                {"id": 3, "name": "Item 3", "weight": 30, "value": 120},
                {"id": 4, "name": "Item 4", "weight": 15, "value": 70}
            ]
        },
        {
            "id": "bb_dominates",
            "name": "High Capacity & Distinct Ratios (B&B Dominates)",
            "description": "Capacity W = 80,000 creates 800,000+ DP table cells, while B&B's fractional bound prunes in microseconds.",
            "capacity": 80000,
            "items": [
                {"id": 1, "name": "Gold Alloy", "weight": 15000, "value": 45000},
                {"id": 2, "name": "Platinum Catalyst", "weight": 22000, "value": 55000},
                {"id": 3, "name": "Titanium Ingot", "weight": 30000, "value": 66000},
                {"id": 4, "name": "Silver Bar", "weight": 18000, "value": 36000},
                {"id": 5, "name": "Rare Earth Sample", "weight": 25000, "value": 42000},
                {"id": 6, "name": "Cobalt Canister", "weight": 12000, "value": 28000},
                {"id": 7, "name": "Lithium Cell", "weight": 20000, "value": 41000},
                {"id": 8, "name": "Silicon Wafer", "weight": 16000, "value": 31000}
            ]
        },
        {
            "id": "dp_dominates",
            "name": "Dense Small Capacity (DP Dominates)",
            "description": "Capacity is tiny (W = 60), meaning DP table is very small (O(nW)), whereas B&B must branch frequently due to similar item ratios.",
            "capacity": 60,
            "items": [
                {"id": 1, "name": "Component A", "weight": 12, "value": 24},
                {"id": 2, "name": "Component B", "weight": 14, "value": 28},
                {"id": 3, "name": "Component C", "weight": 16, "value": 32},
                {"id": 4, "name": "Component D", "weight": 18, "value": 36},
                {"id": 5, "name": "Component E", "weight": 20, "value": 40},
                {"id": 6, "name": "Component F", "weight": 22, "value": 44},
                {"id": 7, "name": "Component G", "weight": 24, "value": 48},
                {"id": 8, "name": "Component H", "weight": 26, "value": 52},
                {"id": 9, "name": "Component I", "weight": 10, "value": 20},
                {"id": 10, "name": "Component J", "weight": 15, "value": 30}
            ]
        },
        {
            "id": "heavy_exclusion",
            "name": "Heavy High-Value Trap",
            "description": "Tests an instance where a single high-value item exceeds capacity, testing boundary and pruning behavior.",
            "capacity": 40,
            "items": [
                {"id": 1, "name": "Oversized Diamond", "weight": 45, "value": 1000},
                {"id": 2, "name": "Ruby Ring", "weight": 15, "value": 180},
                {"id": 3, "name": "Sapphire Pendant", "weight": 20, "value": 240},
                {"id": 4, "name": "Emerald Brooch", "weight": 18, "value": 210}
            ]
        }
    ]
    return jsonify({"presets": presets})


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Generates a reproducible random dataset for inspection and direct solver population.
    """
    data = request.get_json(silent=True) or {}
    try:
        item_count = int(data.get("item_count", 10))
        capacity = int(data.get("capacity", 100))
        min_w = int(data.get("min_weight", 10))
        max_w = int(data.get("max_weight", 50))
        min_v = int(data.get("min_value", 20))
        max_v = int(data.get("max_value", 200))
        seed = int(data.get("seed", 42))

        if item_count < 1 or item_count > config.MAX_ITEMS:
            return jsonify({"success": False, "error": f"Item count must be between 1 and {config.MAX_ITEMS}."}), 400
        if capacity < 1 or capacity > config.MAX_CAPACITY:
            return jsonify({"success": False, "error": f"Capacity must be between 1 and {config.MAX_CAPACITY}."}), 400

        dataset = generate_dataset(item_count, capacity, min_w, max_w, min_v, max_v, seed)
        return jsonify({"success": True, "dataset": dataset}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    # Ensure runner is compiled
    if not config.RUNNER_PATH.exists():
        print(f"[WARN] Runner binary not found at {config.RUNNER_PATH}. Please compile before running.")
    print(f"Starting Knapsack Lab on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
