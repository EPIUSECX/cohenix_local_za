"""Lump Sum Tax Calculation Utilities"""
from frappe.utils import flt

from za_local.utils.statutory_rates import calculate_lump_sum_benefit_tax


def calculate_lump_sum_tax(amount, reason="termination", date_value=None, previous_lump_sums=0):
    """
    Calculate tax on lump sum payments (severance, leave payout)
    Uses the date-effective retirement/severance benefit tax table.
    """
    return calculate_lump_sum_benefit_tax(amount, date_value=date_value, previous_lump_sums=previous_lump_sums)


def calculate_severance_tax(severance_amount, date_value=None, previous_lump_sums=0):
    """Calculate tax on severance pay"""
    return flt(
        calculate_lump_sum_tax(
            severance_amount,
            "severance",
            date_value=date_value,
            previous_lump_sums=previous_lump_sums,
        ),
        2,
    )
