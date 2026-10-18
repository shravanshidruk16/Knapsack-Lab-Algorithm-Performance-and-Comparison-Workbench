"""
Independent correctness and feasibility validation for algorithm results.
Validates knapsack constraints, index bounds, objective values, and algorithm agreement.
"""

from typing import Dict, Any, List, Tuple

def validate_algorithm_result(
    result: Dict[str, Any],
    original_items: List[Dict[str, Any]],
    capacity: int,
    algorithm_label: str
) -> Tuple[bool, List[str], int, int]:
    """
    Validates a single algorithm result for feasibility and internal consistency.
    Returns (is_valid, error_list, calculated_weight, calculated_value).
    """
    errors: List[str] = []

    if not result.get("success", False):
        err_msg = result.get("error_message", "Unknown algorithm failure.")
        return False, [f"{algorithm_label} reported execution error: {err_msg}"], 0, 0

    optimal_value = result.get("optimal_value", 0)
    reported_weight = result.get("total_weight", 0)
    selected_indices = result.get("selected_indices", [])

    # Handle empty selection
    if not selected_indices:
        if optimal_value != 0:
            errors.append(f"{algorithm_label} selected 0 items but reported optimal value {optimal_value} != 0.")
        if reported_weight != 0:
            errors.append(f"{algorithm_label} selected 0 items but reported total weight {reported_weight} != 0.")
        return len(errors) == 0, errors, 0, 0

    # Index bounds and uniqueness check
    seen_indices = set()
    num_items = len(original_items)
    calc_weight = 0
    calc_value = 0

    for idx in selected_indices:
        if not isinstance(idx, int):
            errors.append(f"{algorithm_label} returned non-integer item index: {idx}")
            continue

        if idx < 0 or idx >= num_items:
            errors.append(f"{algorithm_label} selected index {idx} out of range [0, {num_items - 1}].")
            continue

        if idx in seen_indices:
            errors.append(f"{algorithm_label} selected item index {idx} multiple times (0/1 constraint violated).")
        seen_indices.add(idx)

        calc_weight += original_items[idx]["weight"]
        calc_value += original_items[idx]["value"]

    # Capacity constraint verification
    if calc_weight > capacity:
        errors.append(
            f"{algorithm_label} exceeded knapsack capacity: total weight {calc_weight:,} > capacity {capacity:,}."
        )

    # Weight consistency verification
    if calc_weight != reported_weight:
        errors.append(
            f"{algorithm_label} reported weight ({reported_weight:,}) differs from calculated item weight sum ({calc_weight:,})."
        )

    # Value consistency verification
    if calc_value != optimal_value:
        errors.append(
            f"{algorithm_label} reported optimal value ({optimal_value:,}) differs from calculated item value sum ({calc_value:,})."
        )

    return len(errors) == 0, errors, calc_weight, calc_value


def verify_dual_results(
    dp_res: Dict[str, Any],
    bb_res: Dict[str, Any],
    original_items: List[Dict[str, Any]],
    capacity: int
) -> Dict[str, Any]:
    """
    Performs comprehensive verification of both DP and B&B results and their agreement.
    """
    dp_valid, dp_errors, dp_w, dp_v = validate_algorithm_result(dp_res, original_items, capacity, "Dynamic Programming")
    bb_valid, bb_errors, bb_w, bb_v = validate_algorithm_result(bb_res, original_items, capacity, "Branch and Bound")

    all_errors = dp_errors + bb_errors
    agreement = False
    agreement_message = ""

    dp_opt = dp_res.get("optimal_value") if dp_res.get("success") else None
    bb_opt = bb_res.get("optimal_value") if bb_res.get("success") else None

    if dp_valid and bb_valid:
        if dp_opt == bb_opt:
            agreement = True
            agreement_message = f"Optimal values match exactly (V* = {dp_opt:,}). Both algorithms verified feasible."
        else:
            agreement = False
            agreement_message = f"CRITICAL: Objective value mismatch! DP={dp_opt:,} vs B&B={bb_opt:,}."
            all_errors.append(agreement_message)
    elif not dp_valid and not bb_valid:
        agreement_message = "Both algorithms failed validation."
    elif not dp_valid:
        agreement_message = "Dynamic Programming failed validation."
    else:
        agreement_message = "Branch and Bound failed validation."

    return {
        "verified": len(all_errors) == 0 and agreement,
        "agreement": agreement,
        "agreement_message": agreement_message,
        "dp_valid": dp_valid,
        "bb_valid": bb_valid,
        "validation_errors": all_errors,
        "dp_calculated_weight": dp_w,
        "dp_calculated_value": dp_v,
        "bb_calculated_weight": bb_w,
        "bb_calculated_value": bb_v
    }
