"""Travel Allowance Utility Functions"""
import frappe
from frappe.utils import flt

def calculate_reimbursive_allowance(km_traveled, rate):
    """Calculate reimbursive allowance - fully taxable"""
    return flt(km_traveled) * flt(rate)

def calculate_fixed_allowance(monthly_amount):
    """Calculate fixed allowance - 80% taxable, 20% non-taxable"""
    taxable = flt(monthly_amount) * 0.80
    non_taxable = flt(monthly_amount) * 0.20
    return {"taxable": taxable, "non_taxable": non_taxable}
