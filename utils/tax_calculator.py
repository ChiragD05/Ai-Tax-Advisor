def calculate_old_regime_tax(
    salary,
    deductions
):
    taxable_income = max(0, salary - deductions)

    tax = 0

    if taxable_income <= 250000:
        tax = 0

    elif taxable_income <= 500000:
        tax = (taxable_income - 250000) * 0.05

    elif taxable_income <= 1000000:
        tax = (
            250000 * 0.05
            + (taxable_income - 500000) * 0.20
        )

    else:
        tax = (
            250000 * 0.05
            + 500000 * 0.20
            + (taxable_income - 1000000) * 0.30
        )

    # Section 87A Rebate for Old Regime (taxable income <= 5L gets 100% rebate up to ₹12,500)
    if taxable_income <= 500000:
        tax = 0

    # Add 4% Health and Education Cess
    tax_with_cess = tax * 1.04

    return round(tax_with_cess, 2)


def calculate_new_regime_tax(salary, deductions=0):
    taxable_income = max(0, salary - deductions)

    # Slabs for New Tax Regime (FY 2025-26 / AY 2026-27):
    # Up to ₹4,00,000: Nil
    # ₹4,00,001 – ₹8,00,000: 5%
    # ₹8,00,001 – ₹12,00,000: 10%
    # ₹12,00,001 – ₹16,00,000: 15%
    # ₹16,00,001 – ₹20,00,000: 20%
    # ₹20,00,001 – ₹24,00,000: 25%
    # Above ₹24,00,000: 30%
    base_tax = 0

    if taxable_income <= 400000:
        base_tax = 0
    elif taxable_income <= 800000:
        base_tax = (taxable_income - 400000) * 0.05
    elif taxable_income <= 1200000:
        base_tax = (
            400000 * 0.05
            + (taxable_income - 800000) * 0.10
        )
    elif taxable_income <= 1600000:
        base_tax = (
            400000 * 0.05
            + 400000 * 0.10
            + (taxable_income - 1200000) * 0.15
        )
    elif taxable_income <= 2000000:
        base_tax = (
            400000 * 0.05
            + 400000 * 0.10
            + 400000 * 0.15
            + (taxable_income - 1600000) * 0.20
        )
    elif taxable_income <= 2400000:
        base_tax = (
            400000 * 0.05
            + 400000 * 0.10
            + 400000 * 0.15
            + 400000 * 0.20
            + (taxable_income - 2000000) * 0.25
        )
    else:
        base_tax = (
            400000 * 0.05
            + 400000 * 0.10
            + 400000 * 0.15
            + 400000 * 0.20
            + 400000 * 0.25
            + (taxable_income - 2400000) * 0.30
        )

    # Section 87A Rebate for New Regime:
    # Taxable income up to ₹12 Lakh gets 100% rebate (base tax = 0)
    if taxable_income <= 1200000:
        base_tax = 0
    else:
        # Section 87A Marginal Relief for New Regime:
        # Capping the base tax liability to the excess income over ₹12 Lakhs
        excess_income = taxable_income - 1200000
        if base_tax > excess_income:
            base_tax = excess_income

    # Add 4% Health and Education Cess
    tax_with_cess = base_tax * 1.04

    return round(tax_with_cess, 2)