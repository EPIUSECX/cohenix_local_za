"""
South African Payroll Utility Functions

This module provides utility functions for South African payroll processing,
including frequency calculations, payroll period handling, and employee mapping.
"""

import frappe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period


# Frequency mapping for payroll calculations
FREQUENCY_MONTHS = {
    "Quarterly": 3,
    "Half-Yearly": 6,
    "Yearly": 12
}


def get_current_block(frequency, date, payroll_period):
    """
    Get the current payroll block for a given frequency and date.
    
    Args:
        frequency (str): Payroll frequency (Quarterly, Half-Yearly, Yearly)
        date (date): Date to check
        payroll_period (Document): Payroll Period document
        
    Returns:
        frappe._dict: Dict with start_date and end_date of the block
    """
    if frequency not in FREQUENCY_MONTHS:
        frappe.throw(f"Invalid frequency: {frequency}")
    
    start_date = payroll_period.start_date
    end_date = payroll_period.end_date
    months = FREQUENCY_MONTHS[frequency]
    
    while True:
        start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        block_end_date = (start_date + relativedelta(months=months) - timedelta(days=1))
        
        date = datetime.strptime(str(date), "%Y-%m-%d").date()
        if start_date <= date <= block_end_date:
            return frappe._dict({
                "start_date": start_date,
                "end_date": block_end_date
            })
        else:
            start_date = block_end_date + timedelta(days=1)


def get_current_block_period(salary_slip):
    """
    Get current block period for all configured frequencies.
    
    Args:
        salary_slip: Salary Slip document
        
    Returns:
        dict: Map of frequency to block period
    """
    payroll_period = get_payroll_period(
        salary_slip.start_date, 
        salary_slip.end_date, 
        salary_slip.company
    )
    
    if not payroll_period:
        return {}
    
    payroll_period_doc = frappe.get_doc("Payroll Period", payroll_period)
    frequency_map = {}
    
    for freq in FREQUENCY_MONTHS:
        frequency_map[freq] = get_current_block(
            freq, 
            salary_slip.start_date, 
            payroll_period_doc
        )
    
    return frequency_map


def get_employee_frequency_map():
    """
    Get mapping of employees to their payroll frequencies.
    
    Returns:
        dict: Employee ID to frequency mapping
    """
    emp_map = {}
    
    frequency_details = frappe.get_all(
        "Employee Frequency Detail",
        fields=["employee", "frequency"]
    )
    
    for detail in frequency_details:
        emp_map[detail.employee] = detail.frequency
    
    return emp_map


def is_payroll_processed(employee, frequency_period):
    """
    Check if payroll has already been processed for an employee in a period.
    
    Args:
        employee (str): Employee ID
        frequency_period (frappe._dict): Period with start_date and end_date
        
    Returns:
        bool: True if already processed
    """
    if not frequency_period:
        return False
        
    return frappe.db.exists(
        "Salary Slip",
        {
            "employee": employee,
            "start_date": [">=", frequency_period.start_date],
            "end_date": ["<=", frequency_period.end_date],
            "docstatus": 1
        }
    )


def get_additional_salaries(employee, from_date, to_date, component_type="earnings"):
    """
    Get additional salaries for an employee within a date range.
    
    Args:
        employee (str): Employee ID
        from_date (date): Start date
        to_date (date): End date
        component_type (str): Type of component (earnings/deductions/company_contributions)
        
    Returns:
        list: List of Additional Salary documents
    """
    filters = {
        "employee": employee,
        "docstatus": 1,
        "payroll_date": ["between", [from_date, to_date]]
    }
    
    if component_type == "company_contributions":
        filters["za_is_company_contribution"] = 1
    else:
        filters["za_is_company_contribution"] = 0
    
    return frappe.get_all(
        "Additional Salary",
        filters=filters,
        fields=["*"]
    )


def validate_payroll_frequency(employee, start_date, end_date, frequency):
    """
    Validate that payroll frequency is correctly configured for employee.
    
    Args:
        employee (str): Employee ID
        start_date (date): Payroll start date
        end_date (date): Payroll end date
        frequency (str): Expected frequency
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If frequency is invalid
    """
    employee_frequency = frappe.db.get_value(
        "Employee Frequency Detail",
        {"employee": employee},
        "frequency"
    )
    
    if employee_frequency and employee_frequency != frequency:
        frappe.throw(
            f"Employee {employee} is configured for {employee_frequency} payroll, "
            f"but {frequency} is being processed"
        )
    
    return True


def get_payroll_period_dates(payroll_period_name):
    """
    Get start and end dates for a payroll period.
    
    Args:
        payroll_period_name (str): Payroll Period name
        
    Returns:
        tuple: (start_date, end_date)
    """
    period = frappe.get_doc("Payroll Period", payroll_period_name)
    return period.start_date, period.end_date

