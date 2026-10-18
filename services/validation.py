"""
Input validation service for Knapsack Lab.
Enforces strict type checks, positive integers, unique IDs, and safe memory bounds.
"""

from typing import Dict, Any, Tuple, List, Optional
import html
import config

def validate_solver_request(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates custom knapsack solver input.
    Returns (is_valid, error_message, sanitized_data).
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object.", None

    if "capacity" not in data:
        return False, "Knapsack capacity is required.", None

    try:
        capacity = int(data["capacity"])
    except (ValueError, TypeError):
        return False, "Capacity must be a valid integer.", None

    if capacity <= 0:
        return False, f"Capacity must be a positive integer greater than zero (received {capacity}).", None

    if capacity > config.MAX_CAPACITY:
        return False, f"Capacity ({capacity}) exceeds maximum supported limit of {config.MAX_CAPACITY:,}.", None

    trials = 1
    if "trials" in data:
        try:
            trials = int(data["trials"])
            if trials < 1:
                trials = 1
            elif trials > config.MAX_BENCHMARK_REPETITIONS:
                trials = config.MAX_BENCHMARK_REPETITIONS
        except (ValueError, TypeError):
            trials = 1

    items_raw = data.get("items")
    if items_raw is None:
        return False, "Field 'items' is required in payload.", None

    if not isinstance(items_raw, list):
        return False, "Items must be a JSON list.", None

    if len(items_raw) > config.MAX_ITEMS:
        return False, f"Item count ({len(items_raw)}) exceeds the maximum limit of {config.MAX_ITEMS}.", None

    sanitized_items: List[Dict[str, Any]] = []
    seen_ids = set()

    for idx, raw_item in enumerate(items_raw):
        if not isinstance(raw_item, dict):
            return False, f"Item at index {idx} must be a JSON object.", None

        # Item ID
        raw_id = raw_item.get("id", idx + 1)
        if raw_id in seen_ids:
            return False, f"Duplicate item identifier '{raw_id}' detected at row {idx + 1}.", None
        seen_ids.add(raw_id)

        # Name
        raw_name = str(raw_item.get("name", f"Item {idx + 1}")).strip()
        name = html.escape(raw_name[:50]) or f"Item {idx + 1}"

        # Weight
        if "weight" not in raw_item:
            return False, f"Item '{name}' is missing the 'weight' attribute.", None
        try:
            weight = int(raw_item["weight"])
        except (ValueError, TypeError):
            return False, f"Item '{name}' weight must be an integer.", None

        if weight <= 0:
            return False, f"Item '{name}' weight must be a positive integer (received {weight}).", None
        if weight > config.MAX_ITEM_WEIGHT:
            return False, f"Item '{name}' weight ({weight}) exceeds max limit of {config.MAX_ITEM_WEIGHT:,}.", None

        # Value
        if "value" not in raw_item:
            return False, f"Item '{name}' is missing the 'value' attribute.", None
        try:
            value = int(raw_item["value"])
        except (ValueError, TypeError):
            return False, f"Item '{name}' value must be an integer.", None

        if value <= 0:
            return False, f"Item '{name}' value must be a positive integer (received {value}).", None
        if value > config.MAX_ITEM_VALUE:
            return False, f"Item '{name}' value ({value}) exceeds max limit of {config.MAX_ITEM_VALUE:,}.", None

        sanitized_items.append({
            "id": raw_id,
            "name": name,
            "weight": weight,
            "value": value,
            "original_index": idx
        })

    # Check DP table bounds
    dp_cells = (len(sanitized_items) + 1) * (capacity + 1)
    if dp_cells > config.MAX_DP_CELLS:
        return False, (
            f"Requested problem dimensions (N={len(sanitized_items)}, W={capacity:,}) "
            f"require {dp_cells:,} DP cells, exceeding the safety limit of {config.MAX_DP_CELLS:,} cells. "
            "Please reduce the capacity or item count."
        ), None

    sanitized_data = {
        "capacity": capacity,
        "trials": trials,
        "items": sanitized_items
    }
    return True, None, sanitized_data


def validate_benchmark_request(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates benchmark suite execution parameters.
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object.", None

    try:
        min_items = int(data.get("min_items", 5))
        max_items = int(data.get("max_items", 25))
        step_items = int(data.get("step_items", 5))
        capacity = int(data.get("capacity", 100))
        min_weight = int(data.get("min_weight", 10))
        max_weight = int(data.get("max_weight", 50))
        min_value = int(data.get("min_value", 20))
        max_value = int(data.get("max_value", 200))
        seed = int(data.get("seed", 42))
        trials = int(data.get("trials", 3))
    except (ValueError, TypeError) as e:
        return False, f"Invalid numerical parameter in benchmark request: {str(e)}", None

    if min_items < config.MIN_BENCHMARK_ITEMS:
        return False, f"Minimum items must be at least {config.MIN_BENCHMARK_ITEMS}.", None
    if max_items > config.MAX_BENCHMARK_ITEMS:
        return False, f"Maximum items cannot exceed {config.MAX_BENCHMARK_ITEMS} for safe benchmarking.", None
    if min_items > max_items:
        return False, f"min_items ({min_items}) cannot be greater than max_items ({max_items}).", None
    if step_items < 1:
        return False, "step_items must be at least 1.", None

    num_cases = len(range(min_items, max_items + 1, step_items))
    if num_cases > config.MAX_BENCHMARK_CASES:
        return False, f"Configured parameters generate {num_cases} cases, exceeding the limit of {config.MAX_BENCHMARK_CASES}.", None

    if capacity < 1 or capacity > config.MAX_CAPACITY:
        return False, f"Capacity must be between 1 and {config.MAX_CAPACITY:,}.", None

    if min_weight < 1 or max_weight < min_weight or max_weight > config.MAX_ITEM_WEIGHT:
        return False, "Invalid item weight range specified.", None

    if min_value < 1 or max_value < min_value or max_value > config.MAX_ITEM_VALUE:
        return False, "Invalid item value range specified.", None

    if trials < 1 or trials > config.MAX_BENCHMARK_REPETITIONS:
        return False, f"Trials per point must be between 1 and {config.MAX_BENCHMARK_REPETITIONS}.", None

    return True, None, {
        "min_items": min_items,
        "max_items": max_items,
        "step_items": step_items,
        "capacity": capacity,
        "min_weight": min_weight,
        "max_weight": max_weight,
        "min_value": min_value,
        "max_value": max_value,
        "seed": seed,
        "trials": trials
    }
