"""Lump Sum Tax Calculation Utilities"""
import frappe
from frappe.utils import flt

def calculate_lump_sum_tax(amount, reason="termination"):
    """
    Calculate tax on lump sum payments (severance, leave payout)
    Uses special lump sum tax rates
    """
    # TODO: Implement SARS lump sum tax tables
    return flt(amount) * 0.18  # Placeholder

def calculate_severance_tax(severance_amount):
    """Calculate tax on severance pay"""
    # First R500,000 tax-free, then taxed
    tax_free_portion = 500000
    if severance_amount <= tax_free_portion:
        return 0
    taxable = severance_amount - tax_free_portion
    return calculate_lump_sum_tax(taxable)
