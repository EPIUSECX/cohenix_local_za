"""
COIDA Utility Functions

Utilities for Compensation for Occupational Injuries and Diseases Act (COIDA) compliance.
"""

import frappe
from frappe.utils import flt


def calculate_coida_contribution(gross_remuneration, industry_rate):
    """
    Calculate COIDA contribution.
    
    COIDA is calculated as a percentage of gross remuneration based on industry risk class.
    
    Args:
        gross_remuneration (float): Total gross remuneration
        industry_rate (float): Industry rate percentage
        
    Returns:
        float: COIDA contribution amount
    """
    if not gross_remuneration or not industry_rate:
        return 0
    
    coida_amount = flt(gross_remuneration) * (flt(industry_rate) / 100)
    
    return flt(coida_amount, 2)


def get_company_industry_rate(company):
    """
    Get the COIDA industry rate for a company.
    
    Args:
        company (str): Company name
        
    Returns:
        float: Industry rate percentage
    """
    # Get COIDA settings
    coida_settings = frappe.get_all(
        "COIDA Settings",
        filters={"company": company},
        fields=["name"],
        limit=1
    )
    
    if not coida_settings:
        frappe.log_error(f"COIDA Settings not configured for {company}", "COIDA Calculation")
        return 0
    
    settings_doc = frappe.get_doc("COIDA Settings", coida_settings[0].name)
    
    # Get the primary industry rate (typically first one)
    if settings_doc.industry_rates:
        return flt(settings_doc.industry_rates[0].rate)
    
    return 0


def validate_industry_rates(industry_rates):
    """
    Validate COIDA industry rates configuration.
    
    Args:
        industry_rates (list): List of industry rate entries
        
    Returns:
        dict: {valid: bool, errors: list}
    """
    errors = []
    
    if not industry_rates:
        errors.append("At least one industry rate must be configured")
        return {"valid": False, "errors": errors}
    
    for rate in industry_rates:
        if not rate.industry_class:
            errors.append("Industry class is required")
        
        if flt(rate.rate) <= 0:
            errors.append(f"Industry rate for {rate.industry_class} must be greater than 0")
        
        if flt(rate.rate) > 10:
            errors.append(f"Industry rate for {rate.industry_class} seems unusually high (>{10}%)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def calculate_annual_coida(company, from_date, to_date):
    """
    Calculate total COIDA for annual return.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        
    Returns:
        dict: {total_remuneration: float, total_coida: float, employee_count: int}
    """
    # Get all salary slips in the period
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "company": company,
            "start_date": [">=", from_date],
            "end_date": ["<=", to_date],
            "docstatus": 1
        },
        fields=["gross_pay", "employee"]
    )
    
    total_remuneration = sum(flt(slip.gross_pay) for slip in salary_slips)
    
    # Get company industry rate
    industry_rate = get_company_industry_rate(company)
    
    total_coida = calculate_coida_contribution(total_remuneration, industry_rate)
    
    # Count unique employees
    unique_employees = set(slip.employee for slip in salary_slips)
    
    return {
        "total_remuneration": flt(total_remuneration, 2),
        "total_coida": flt(total_coida, 2),
        "employee_count": len(unique_employees),
        "industry_rate": industry_rate
    }


def get_workplace_injuries_for_period(company, from_date, to_date):
    """
    Get workplace injuries for a company within a period.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        
    Returns:
        list: List of Workplace Injury documents
    """
    injuries = frappe.get_all(
        "Workplace Injury",
        filters={
            "company": company,
            "incident_date": ["between", [from_date, to_date]]
        },
        fields=["*"],
        order_by="incident_date desc"
    )
    
    return injuries


def get_oid_claims_for_period(company, from_date, to_date, status=None):
    """
    Get OID claims for a company within a period.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        status (str): Optional status filter
        
    Returns:
        list: List of OID Claim documents
    """
    filters = {
        "company": company,
        "claim_date": ["between", [from_date, to_date]]
    }
    
    if status:
        filters["status"] = status
    
    claims = frappe.get_all(
        "OID Claim",
        filters=filters,
        fields=["*"],
        order_by="claim_date desc"
    )
    
    return claims

