"""Fringe Benefit Utility Functions"""
import frappe
from frappe.utils import flt

def calculate_fringe_benefit_tax(benefit_type, value):
    """Calculate tax on fringe benefit"""
    return flt(value)

def get_active_benefits(employee, date):
    """Get active fringe benefits for employee"""
    return frappe.get_all("Fringe Benefit",
        filters={"employee": employee, "status": "Active"},
        fields=["name", "benefit_type", "taxable_value"])
