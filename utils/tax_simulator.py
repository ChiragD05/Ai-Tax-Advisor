from typing import Dict, List, Any

from utils.tax_calculator import (
    calculate_old_regime_tax,
    calculate_new_regime_tax,
)


def simulate_tax_scenarios(
    salary: float,
    deduction_breakdown: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Build a few what-if tax scenarios from the user's current inputs.
    """

    scenarios = []

    # Scenario 1: Current plan
    current_total = sum(deduction_breakdown.values())
    current_old_tax = calculate_old_regime_tax(salary, current_total)
    current_new_tax = calculate_new_regime_tax(salary)

    scenarios.append({
        "scenario": "Current plan",
        "salary": salary,
        "deductions": current_total,
        "old_tax": current_old_tax,
        "new_tax": current_new_tax,
        "best_regime": "Old tax regime" if current_old_tax < current_new_tax else "New tax regime",
        "savings": abs(current_old_tax - current_new_tax),
    })

    # Scenario 2: New regime compliant plan
    # Only keep deductions allowed in new regime
    new_regime_allowed_keys = {"80ccd2", "standard"}
    new_regime_total = sum(
        amount for key, amount in deduction_breakdown.items()
        if key in new_regime_allowed_keys
    )
    new_regime_old_tax = calculate_old_regime_tax(salary, new_regime_total)
    new_regime_new_tax = calculate_new_regime_tax(salary)

    scenarios.append({
        "scenario": "New regime compliant plan",
        "salary": salary,
        "deductions": new_regime_total,
        "old_tax": new_regime_old_tax,
        "new_tax": new_regime_new_tax,
        "best_regime": "Old tax regime" if new_regime_old_tax < new_regime_new_tax else "New tax regime",
        "savings": abs(new_regime_old_tax - new_regime_new_tax),
    })

    # Scenario 3: Maximize old regime deductions
    # Keep only old-regime-friendly deductions and keep the amounts as selected
    old_regime_total = sum(
        amount for key, amount in deduction_breakdown.items()
        if key != "80ccd2"
    )
    old_regime_old_tax = calculate_old_regime_tax(salary, old_regime_total)
    old_regime_new_tax = calculate_new_regime_tax(salary)

    scenarios.append({
        "scenario": "Old regime optimized plan",
        "salary": salary,
        "deductions": old_regime_total,
        "old_tax": old_regime_old_tax,
        "new_tax": old_regime_new_tax,
        "best_regime": "Old tax regime" if old_regime_old_tax < old_regime_new_tax else "New tax regime",
        "savings": abs(old_regime_old_tax - old_regime_new_tax),
    })

    return scenarios