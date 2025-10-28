"""
Employment Tax Incentive (ETI) Utility Functions

The Employment Tax Incentive is a South African tax incentive aimed at encouraging
employers to hire young, less experienced job seekers.

ETI Eligibility Criteria:
- Age: 18-29 years on the last day of the month
- Monthly remuneration within qualifying thresholds
- Employment period: First 24 months only
- Hired on or after October 1, 2013
- Valid SA ID or Asylum Seeker permit
"""

import frappe
from frappe.utils import flt, getdate, date_diff
from datetime import date, timedelta


def check_eti_eligibility(employee, salary_slip):
    """
    Check if an employee qualifies for ETI.
    
    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document
        
    Returns:
        dict: {eligible: bool, reason: str, months_employed: int}
    """
    # Get employee details
    emp_doc = frappe.get_doc("Employee", employee)
    
    # Check if ETI is disabled globally
    payroll_settings = frappe.get_single("Payroll Settings")
    if payroll_settings.get("za_disable_eti_calculation"):
        return {
            "eligible": False,
            "reason": "ETI calculation is disabled in Payroll Settings",
            "months_employed": 0
        }
    
    # Check date of birth
    if not emp_doc.date_of_birth:
        return {
            "eligible": False,
            "reason": "Employee date of birth not set",
            "months_employed": 0
        }
    
    # Check age (18-29 years on last day of month)
    last_day_of_month = getdate(salary_slip.end_date)
    dob = getdate(emp_doc.date_of_birth)
    
    age = last_day_of_month.year - dob.year
    if (last_day_of_month.month, last_day_of_month.day) < (dob.month, dob.day):
        age -= 1
    
    if age < 18 or age > 29:
        return {
            "eligible": False,
            "reason": f"Employee age ({age}) not within 18-29 range",
            "months_employed": 0
        }
    
    # Check employment start date
    if not emp_doc.date_of_joining:
        return {
            "eligible": False,
            "reason": "Employee joining date not set",
            "months_employed": 0
        }
    
    joining_date = getdate(emp_doc.date_of_joining)
    
    # Must be employed on or after October 1, 2013
    eti_start_date = date(2013, 10, 1)
    if joining_date < eti_start_date:
        return {
            "eligible": False,
            "reason": "Employee joined before ETI program start (Oct 1, 2013)",
            "months_employed": 0
        }
    
    # Calculate months employed
    months_employed = calculate_months_employed(joining_date, last_day_of_month)
    
    # ETI only applies for first 24 months
    if months_employed > 24:
        return {
            "eligible": False,
            "reason": "Employee has exceeded 24-month ETI period",
            "months_employed": months_employed
        }
    
    # Check if employee has valid SA ID or permit
    if not emp_doc.get("za_id_number"):
        # Could also check for asylum seeker permit field if implemented
        return {
            "eligible": False,
            "reason": "Employee SA ID number not set",
            "months_employed": months_employed
        }
    
    return {
        "eligible": True,
        "reason": "Employee qualifies for ETI",
        "months_employed": months_employed
    }


def calculate_eti_amount(employee, salary_slip, monthly_remuneration):
    """
    Calculate the ETI amount for an employee.
    
    ETI Calculation Brackets (2024/2025):
    
    First 12 months:
    - R0 - R2,000: 50% of remuneration
    - R2,001 - R4,500: R1,000
    - R4,501 - R6,500: R1,000 - (0.5 × (Remuneration - R4,500))
    - Above R6,500: R0
    
    Second 12 months:
    - R0 - R2,000: 25% of remuneration
    - R2,001 - R4,500: R500
    - R4,501 - R6,500: R500 - (0.25 × (Remuneration - R4,500))
    - Above R6,500: R0
    
    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document
        monthly_remuneration (float): Monthly remuneration amount
        
    Returns:
        float: ETI amount for the month
    """
    # Check eligibility first
    eligibility = check_eti_eligibility(employee, salary_slip)
    
    if not eligibility["eligible"]:
        return 0
    
    months_employed = eligibility["months_employed"]
    remuneration = flt(monthly_remuneration)
    
    # Get ETI slab for calculation
    eti_slab = get_eti_slab()
    
    if not eti_slab:
        frappe.log_error("ETI Slab not configured", "ETI Calculation")
        return 0
    
    # Determine which period (first 12 or second 12 months)
    is_first_period = months_employed <= 12
    
    eti_amount = 0
    
    # Apply ETI formulas based on remuneration brackets
    for detail in eti_slab.details:
        if is_first_period and detail.period != "First 12 Months":
            continue
        if not is_first_period and detail.period != "Second 12 Months":
            continue
        
        min_rem = flt(detail.min_remuneration)
        max_rem = flt(detail.max_remuneration)
        
        if min_rem <= remuneration <= max_rem:
            # Evaluate the formula
            if detail.formula:
                try:
                    # Make remuneration available in formula
                    eti_amount = eval(detail.formula, {"__builtins__": None}, {
                        "remuneration": remuneration,
                        "R": remuneration  # Alias for formulas
                    })
                except Exception as e:
                    frappe.log_error(f"ETI formula error: {e}", "ETI Calculation")
                    eti_amount = 0
            else:
                eti_amount = flt(detail.amount)
            
            break
    
    # Pro-rate based on hours if applicable
    hours_per_month = frappe.db.get_value("Employee", employee, "za_hours_per_month")
    if hours_per_month and hours_per_month > 0:
        # Standard month is typically 160-173 hours
        standard_hours = 160
        if hours_per_month < standard_hours:
            eti_amount = eti_amount * (hours_per_month / standard_hours)
    
    return flt(eti_amount, 2)


def calculate_months_employed(joining_date, current_date):
    """
    Calculate number of complete months employed.
    
    Args:
        joining_date (date): Date of joining
        current_date (date): Current date
        
    Returns:
        int: Number of complete months employed
    """
    joining_date = getdate(joining_date)
    current_date = getdate(current_date)
    
    months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month)
    
    # Add 1 if we've passed the joining day in the current month
    if current_date.day >= joining_date.day:
        months += 1
    
    return max(0, months)


def get_eti_slab():
    """
    Get the current ETI Slab configuration.
    
    Returns:
        Document: ETI Slab document
    """
    slabs = frappe.get_all(
        "ETI Slab",
        fields=["name"],
        limit=1
    )
    
    if slabs:
        return frappe.get_doc("ETI Slab", slabs[0].name)
    
    return None


def log_eti_calculation(employee, salary_slip, eti_amount, eligibility_details):
    """
    Log ETI calculation details for audit trail.
    
    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document
        eti_amount (float): Calculated ETI amount
        eligibility_details (dict): Eligibility check results
    """
    try:
        # Check if log already exists for this salary slip
        existing_log = frappe.db.exists(
            "Employee ETI Log",
            {
                "employee": employee,
                "salary_slip": salary_slip.name
            }
        )
        
        if existing_log:
            # Update existing log
            log_doc = frappe.get_doc("Employee ETI Log", existing_log)
        else:
            # Create new log
            log_doc = frappe.new_doc("Employee ETI Log")
            log_doc.employee = employee
            log_doc.salary_slip = salary_slip.name
        
        log_doc.posting_date = salary_slip.end_date
        log_doc.payroll_period = salary_slip.payroll_period
        log_doc.is_eligible = eligibility_details["eligible"]
        log_doc.eligibility_reason = eligibility_details["reason"]
        log_doc.months_employed = eligibility_details["months_employed"]
        log_doc.eti_amount = eti_amount
        log_doc.monthly_remuneration = salary_slip.gross_pay
        
        log_doc.save(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error logging ETI calculation: {str(e)}", "ETI Log")


def get_employee_eti_history(employee, from_date=None, to_date=None):
    """
    Get ETI history for an employee.
    
    Args:
        employee (str): Employee ID
        from_date (date): Optional start date filter
        to_date (date): Optional end date filter
        
    Returns:
        list: List of ETI Log documents
    """
    filters = {"employee": employee}
    
    if from_date:
        filters["posting_date"] = [">=", from_date]
    if to_date:
        if "posting_date" in filters:
            filters["posting_date"] = ["between", [from_date, to_date]]
        else:
            filters["posting_date"] = ["<=", to_date]
    
    return frappe.get_all(
        "Employee ETI Log",
        filters=filters,
        fields=["*"],
        order_by="posting_date desc"
    )


def calculate_total_eti_for_period(company, from_date, to_date):
    """
    Calculate total ETI for a company in a period (for EMP201/EMP501).
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        
    Returns:
        float: Total ETI amount
    """
    # Get all eligible salary slips in the period
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "company": company,
            "start_date": [">=", from_date],
            "end_date": ["<=", to_date],
            "docstatus": 1
        },
        fields=["name", "za_monthly_eti"]
    )
    
    total_eti = sum(flt(slip.get("za_monthly_eti", 0)) for slip in salary_slips)
    
    return flt(total_eti, 2)

