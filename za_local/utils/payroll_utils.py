"""
South African Payroll Utility Functions

This module provides utility functions for South African payroll processing,
including frequency calculations, payroll period handling, and employee mapping.
"""

import frappe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from za_local.utils.hrms_detection import safe_import_hrms, require_hrms

# Conditionally import HRMS functions
get_payroll_period, = safe_import_hrms(
    "hrms.payroll.doctype.payroll_period.payroll_period",
    "get_payroll_period"
)

if get_payroll_period is None:
    def get_payroll_period(*args, **kwargs):
        require_hrms("Payroll Period")
        return None


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
        frappe._dict: Dict with start_date and end_date of the block, or None if invalid
    """
    if frequency not in FREQUENCY_MONTHS:
        return None
    
    if not payroll_period or not hasattr(payroll_period, 'start_date'):
        return None
    
    try:
        start_date = payroll_period.start_date
        end_date = payroll_period.end_date
        months = FREQUENCY_MONTHS[frequency]
        
        # Convert to date objects if strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        if isinstance(date, str):
            date = datetime.strptime(str(date), "%Y-%m-%d").date()
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(date, datetime):
            date = date.date()
        
        current_start = start_date
        
        # Limit iterations to prevent infinite loop
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            block_end_date = (current_start + relativedelta(months=months) - timedelta(days=1))
            
            if current_start <= date <= block_end_date:
                return frappe._dict({
                    "start_date": current_start,
                    "end_date": block_end_date
                })
            else:
                current_start = block_end_date + timedelta(days=1)
                # Check if we've gone past the payroll period end
                if current_start > end_date:
                    break
        
        return None
    except Exception as e:
        frappe.log_error(f"Error calculating block period for {frequency}: {str(e)}", "Payroll Block Calculation")
        return None


def get_current_block_period(doc):
    """
    Get current block period for all configured frequencies.
    
    Args:
        doc: Document with start_date, end_date, and company (Salary Slip or Payroll Entry)
        
    Returns:
        dict: Map of frequency to block period
    """
    # Handle both Salary Slip and Payroll Entry
    start_date = getattr(doc, 'start_date', None)
    end_date = getattr(doc, 'end_date', None)
    company = getattr(doc, 'company', None)
    
    if not all([start_date, end_date, company]):
        return {}
    
    payroll_period = get_payroll_period(
        start_date, 
        end_date, 
        company
    )
    
    if not payroll_period:
        return {}
    
    try:
        payroll_period_doc = frappe.get_doc("Payroll Period", payroll_period)
        frequency_map = {}
        
        for freq in FREQUENCY_MONTHS:
            block = get_current_block(freq, start_date, payroll_period_doc)
            if block:  # Only include if valid block was calculated
                frequency_map[freq] = block
        
        return frequency_map
    except Exception as e:
        frappe.log_error(f"Error getting block period: {str(e)}", "Payroll Block Period")
        return {}


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
    Filters by Additional Salary type (Earning vs Deduction) so each record
    appears only in the correct section on the Salary Slip (earnings or deductions).
    
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
        # Filter by type so the same Additional Salary does not appear in both earnings and deductions
        if component_type == "earnings":
            filters["type"] = "Earning"
        elif component_type == "deductions":
            filters["type"] = "Deduction"
    
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

