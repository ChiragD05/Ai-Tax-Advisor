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

    return round(tax, 2)

def calculate_new_regime_tax(salary):

    # Zero tax benefit up to 12 lakh
    if salary <= 1200000:
        return 0

    tax = 0

    if salary <= 300000:
        tax = 0

    elif salary <= 600000:

        tax = (
            (salary - 300000) * 0.05
        )

    elif salary <= 900000:

        tax = (
            300000 * 0.05
            + (salary - 600000) * 0.10
        )

    elif salary <= 1200000:

        tax = (
            300000 * 0.05
            + 300000 * 0.10
            + (salary - 900000) * 0.15
        )

    elif salary <= 1500000:

        tax = (
            300000 * 0.05
            + 300000 * 0.10
            + 300000 * 0.15
            + (salary - 1200000) * 0.20
        )

    else:

        tax = (
            300000 * 0.05
            + 300000 * 0.10
            + 300000 * 0.15
            + 300000 * 0.20
            + (salary - 1500000) * 0.30
        )

    return round(tax, 2)