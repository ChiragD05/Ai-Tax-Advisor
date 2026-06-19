import sys
import os

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.tax_calculator import calculate_old_regime_tax, calculate_new_regime_tax

def run_tests():
    print("--- Running Tax Calculation Tests ---")

    # Scenario 1: Old Regime <= 5,00,000 (tax should be 0 due to 87A rebate)
    old_tax_1 = calculate_old_regime_tax(500000, 0)
    print(f"Old Regime Tax (Income: 5L, Deductions: 0) -> Expected: 0.00, Got: {old_tax_1:.2f}")
    assert old_tax_1 == 0.0, "Test Failed: Old Regime <= 5L should have 0 tax"

    # Scenario 2: Old Regime > 5,00,000 (tax should be calculated with 4% cess, no rebate)
    # Income: 6,00,000. Deductions: 50,000. Taxable income: 5,50,000.
    # Base Tax: 2.5L to 5L (2.5L * 5% = 12,500) + 5L to 5.5L (50k * 20% = 10,000) = 22,500
    # With 4% cess: 22,500 * 1.04 = 23,400
    old_tax_2 = calculate_old_regime_tax(600000, 50000)
    print(f"Old Regime Tax (Income: 6L, Deductions: 50k) -> Expected: 23400.00, Got: {old_tax_2:.2f}")
    assert abs(old_tax_2 - 23400.00) < 0.01, "Test Failed: Old Regime > 5L calculation"

    # Scenario 3: New Regime <= 12,00,000 (tax should be 0 due to 87A rebate)
    new_tax_1 = calculate_new_regime_tax(1200000, 0)
    print(f"New Regime Tax (Income: 12L, Deductions: 0) -> Expected: 0.00, Got: {new_tax_1:.2f}")
    assert new_tax_1 == 0.0, "Test Failed: New Regime <= 12L should have 0 tax"

    # Scenario 4: New Regime slightly above 12,00,000 (marginal relief applies)
    # Income: 12,05,000. Deductions: 0. Taxable: 12,05,000.
    # Base Tax: 4L at 0% + 4L at 5% (20,000) + 4L at 10% (40,000) + 5,000 at 15% (750) = 60,750.
    # Excess over 12L = 5,000.
    # Base Tax after marginal relief: min(60,750, 5,000) = 5,000.
    # Tax with 4% cess: 5,000 * 1.04 = 5,200.
    new_tax_2 = calculate_new_regime_tax(1205000, 0)
    print(f"New Regime Tax (Income: 12.05L, Deductions: 0) -> Expected: 5200.00, Got: {new_tax_2:.2f}")
    assert abs(new_tax_2 - 5200.00) < 0.01, "Test Failed: New Regime marginal relief calculation"

    # Scenario 5: New Regime high income (no marginal relief)
    # Income: 15,00,000. Deductions: 75,000 (standard deduction). Taxable: 14,25,000.
    # Base Tax: 4L at 5% (20,000) + 4L at 10% (40,000) + 2.25L at 15% (33,750) = 93,750.
    # Excess over 12L = 2,25,000.
    # Base Tax after relief: min(93,750, 2,25,000) = 93,750.
    # Tax with 4% cess: 93,750 * 1.04 = 97,500.
    new_tax_3 = calculate_new_regime_tax(1500000, 75000)
    print(f"New Regime Tax (Income: 15L, Deductions: 75k) -> Expected: 97500.00, Got: {new_tax_3:.2f}")
    assert abs(new_tax_3 - 97500.00) < 0.01, "Test Failed: New Regime high income calculation"

    print("✅ All Tax Calculation Tests Passed!")

if __name__ == "__main__":
    run_tests()
