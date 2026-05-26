"""Travel Allowance Utility Functions"""
from frappe.utils import flt

from za_local.utils.statutory_rates import (
    get_default_travel_paye_inclusion_percentage,
    get_reimbursive_travel_rate,
)


def calculate_reimbursive_allowance(km_traveled, rate=None, date_value=None):
    """Calculate reimbursive allowance and taxable excess over the prescribed rate."""
    prescribed_rate = get_reimbursive_travel_rate(date_value)
    actual_rate = flt(rate) if rate is not None else prescribed_rate
    total = flt(km_traveled) * actual_rate
    taxable_excess = max(0, actual_rate - prescribed_rate) * flt(km_traveled)
    return {
        "total": flt(total, 2),
        "taxable": flt(taxable_excess, 2),
        "non_taxable": flt(total - taxable_excess, 2),
        "prescribed_rate": prescribed_rate,
    }


def calculate_fixed_allowance(monthly_amount, inclusion_percentage=None, date_value=None):
    """Calculate PAYE taxable/non-taxable portions of a fixed travel allowance."""
    if inclusion_percentage is None:
        inclusion_percentage = get_default_travel_paye_inclusion_percentage(date_value)
    taxable = flt(monthly_amount) * flt(inclusion_percentage) / 100
    non_taxable = flt(monthly_amount) - taxable
    return {"taxable": taxable, "non_taxable": non_taxable}
