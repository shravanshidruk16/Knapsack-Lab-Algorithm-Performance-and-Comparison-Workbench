"""
Knapsack Lab Benchmark and Subprocess Execution Engine
Orchestrates isolated C++ runner execution, dataset generation, timing, and empirical benchmarks.
"""

import json
import random
import subprocess
import time
from typing import Dict, Any, List, Optional
import config
from services.result_validation import verify_dual_results

def generate_dataset(
    item_count: int,
    capacity: int,
    min_weight: int,
    max_weight: int,
    min_value: int,
    max_value: int,
    seed: int
) -> Dict[str, Any]:
    """
    Generates a reproducible knapsack dataset using a seeded pseudo-random number generator.
    """
    rng = random.Random(seed)
    items = []

    for i in range(item_count):
        w = rng.randint(min_weight, max_weight)
        v = rng.randint(min_value, max_value)
        items.append({
            "id": i + 1,
            "name": f"Item {i + 1}",
            "weight": w,
            "value": v,
            "original_index": i
        })

    return {
        "capacity": capacity,
        "items": items,
        "seed": seed,
        "item_count": item_count
    }


def execute_runner_isolated(
    algorithm: str,
    items: List[Dict[str, Any]],
    capacity: int,
    trials: int = 1,
    timeout: int = config.DEFAULT_EXECUTION_TIMEOUT
) -> Dict[str, Any]:
    """
    Executes a single algorithm in a fresh, isolated C++ process to ensure
    memory measurements and thread states do not contaminate each other.
    """
    if not config.RUNNER_PATH.exists():
        return {
            "success": False,
            "error_message": f"Compiled C++ runner not found at '{config.RUNNER_PATH}'. Please compile the runner first."
        }

    payload = {
        "capacity": capacity,
        "trials": trials,
        "items": items
    }
    input_json = json.dumps(payload)

    cmd = [str(config.RUNNER_PATH), "--mode", algorithm]

    try:
        proc = subprocess.run(
            cmd,
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if proc.returncode != 0:
            err = proc.stderr.strip() or f"Process exited with non-zero code {proc.returncode}"
            return {
                "success": False,
                "error_message": f"Runner execution failed: {err}"
            }

        try:
            res_json = json.loads(proc.stdout)
            # Extract specific algorithm result
            if algorithm == "dp":
                return res_json.get("dp", {"success": False, "error_message": "Missing DP section"})
            elif algorithm == "bb":
                return res_json.get("branch_and_bound", {"success": False, "error_message": "Missing B&B section"})
            return res_json
        except json.JSONDecodeError as jde:
            return {
                "success": False,
                "error_message": f"Malformed JSON output from C++ runner: {jde}. Raw stdout: {proc.stdout[:200]}"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "timed_out": True,
            "error_message": f"Algorithm execution exceeded configured timeout limit of {timeout}s."
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"System error invoking C++ runner: {str(e)}"
        }


def solve_both_algorithms(
    items: List[Dict[str, Any]],
    capacity: int,
    trials: int = 1,
    timeout: int = config.DEFAULT_EXECUTION_TIMEOUT
) -> Dict[str, Any]:
    """
    Executes both DP and B&B in separate subprocesses, cross-validates results,
    and computes speedup and comparative statistics.
    """
    start_total = time.perf_counter()

    # 1. Run Dynamic Programming in dedicated process
    dp_res = execute_runner_isolated("dp", items, capacity, trials=trials, timeout=timeout)

    # 2. Run Branch and Bound in dedicated process
    bb_res = execute_runner_isolated("bb", items, capacity, trials=trials, timeout=timeout)

    total_wall_time_ms = (time.perf_counter() - start_total) * 1000.0

    # 3. Cross-validate feasibility, item sums, and objective agreement
    verification = verify_dual_results(dp_res, bb_res, items, capacity)

    # 4. Compute performance comparison
    comparison: Dict[str, Any] = {
        "optimal_values_match": verification["agreement"],
        "faster_algorithm": "N/A",
        "speedup": 1.0,
        "runtime_difference_ms": 0.0,
        "speedup_summary": "Comparison could not be completed."
    }

    dp_ok = dp_res.get("success", False)
    bb_ok = bb_res.get("success", False)

    if dp_ok and bb_ok and verification["agreement"]:
        dp_time = dp_res.get("execution_time_ms", 0.0)
        bb_time = bb_res.get("execution_time_ms", 0.0)
        diff_ms = abs(dp_time - bb_time)
        comparison["runtime_difference_ms"] = round(diff_ms, 6)

        # Baseline definitions:
        # If BB faster: speedup = DP runtime / BB runtime
        # If DP faster: speedup = BB runtime / DP runtime
        min_reliable_timer = 0.0001 # 0.1 microseconds in ms

        if dp_time < min_reliable_timer and bb_time < min_reliable_timer:
            comparison["faster_algorithm"] = "Identical"
            comparison["speedup"] = 1.0
            comparison["speedup_summary"] = "Runtimes are beneath timer resolution threshold; both completed almost instantaneously."
        elif bb_time < dp_time * 0.95 and bb_time > 0:
            comparison["faster_algorithm"] = "Branch and Bound"
            comparison["speedup"] = round(dp_time / bb_time, 2) if bb_time > 0 else 1.0
            comparison["speedup_summary"] = f"Branch and Bound was {comparison['speedup']}x faster than Dynamic Programming."
        elif dp_time < bb_time * 0.95 and dp_time > 0:
            comparison["faster_algorithm"] = "Dynamic Programming"
            comparison["speedup"] = round(bb_time / dp_time, 2) if dp_time > 0 else 1.0
            comparison["speedup_summary"] = f"Dynamic Programming was {comparison['speedup']}x faster than Branch and Bound."
        else:
            comparison["faster_algorithm"] = "Virtually Identical"
            comparison["speedup"] = 1.0
            comparison["speedup_summary"] = "Both algorithms exhibited nearly identical measured execution times."

    return {
        "success": True,
        "capacity": capacity,
        "item_count": len(items),
        "total_wall_time_ms": round(total_wall_time_ms, 3),
        "dp": dp_res,
        "branch_and_bound": bb_res,
        "verification": verification,
        "comparison": comparison
    }


def run_benchmark_suite(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes an empirical benchmark sweep over problem sizes with reproducible seeds.
    """
    min_items = params["min_items"]
    max_items = params["max_items"]
    step_items = params["step_items"]
    capacity = params["capacity"]
    min_w = params["min_weight"]
    max_w = params["max_weight"]
    min_v = params["min_value"]
    max_v = params["max_value"]
    base_seed = params["seed"]
    trials = params["trials"]

    points: List[Dict[str, Any]] = []

    for item_count in range(min_items, max_items + 1, step_items):
        # Generate independent reproducible instance per size
        current_seed = base_seed + (item_count * 1337)
        dataset = generate_dataset(
            item_count=item_count,
            capacity=capacity,
            min_weight=min_w,
            max_weight=max_w,
            min_value=min_v,
            max_value=max_v,
            seed=current_seed
        )

        dp_res = execute_runner_isolated("dp", dataset["items"], capacity, trials=trials)
        bb_res = execute_runner_isolated("bb", dataset["items"], capacity, trials=trials)

        point_data: Dict[str, Any] = {
            "item_count": item_count,
            "capacity": capacity,
            "seed": current_seed,
            "dp_success": dp_res.get("success", False),
            "bb_success": bb_res.get("success", False),
            "dp_timed_out": dp_res.get("timed_out", False),
            "bb_timed_out": bb_res.get("timed_out", False),
            "dp_optimal_value": dp_res.get("optimal_value"),
            "bb_optimal_value": bb_res.get("optimal_value"),
            "dp_time_us": dp_res.get("execution_time_us", 0.0),
            "dp_time_ms": dp_res.get("execution_time_ms", 0.0),
            "bb_time_us": bb_res.get("execution_time_us", 0.0),
            "bb_time_ms": bb_res.get("execution_time_ms", 0.0),
            "dp_peak_memory_kb": round(dp_res.get("peak_working_set_bytes", 0) / 1024, 1),
            "bb_peak_memory_kb": round(bb_res.get("peak_working_set_bytes", 0) / 1024, 1),
            "dp_workspace_kb": round(dp_res.get("algorithm_workspace_bytes", 0) / 1024, 2),
            "bb_workspace_kb": round(bb_res.get("algorithm_workspace_bytes", 0) / 1024, 2),
            "nodes_expanded": bb_res.get("nodes_expanded", 0),
            "nodes_generated": bb_res.get("nodes_generated", 0),
            "nodes_pruned": bb_res.get("nodes_pruned", 0),
            "max_frontier_size": bb_res.get("max_frontier_size", 0),
            "agreement": (
                dp_res.get("success", False) and
                bb_res.get("success", False) and
                dp_res.get("optimal_value") == bb_res.get("optimal_value")
            )
        }
        points.append(point_data)

    return {
        "success": True,
        "parameters": params,
        "point_count": len(points),
        "points": points
    }
