"""
South African Tax Utility Functions

This module provides utility functions for South African tax calculations including:
- PAYE (Pay As You Earn) calculations
- Tax rebates (primary, secondary, tertiary)
- Medical aid tax credits
- Retirement annuity deductions
"""

import frappe
from frappe.utils import flt, getdate, date_diff
from datetime import date


def calculate_south_african_tax(annual_taxable_income, tax_slab=None):
    """
    Calculate South African PAYE tax based on annual taxable income.
    
    Args:
        annual_taxable_income (float): Total annual taxable income
        tax_slab (str): Optional tax slab name (defaults to current year)
        
    Returns:
        float: Annual tax amount
    """
    if not annual_taxable_income or annual_taxable_income <= 0:
        return 0
    
    # Get tax slab if not provided
    if not tax_slab:
        tax_slab = get_current_tax_slab()
    
    if not tax_slab:
        frappe.throw("No tax slab found for the current period")
    
    # Calculate tax using tax slab
    from hrms.payroll.doctype.salary_slip.salary_slip import calculate_tax_by_tax_slab
    
    tax_amount = calculate_tax_by_tax_slab(
        annual_taxable_income,
        tax_slab
    )
    
    return flt(tax_amount)


def get_current_tax_slab():
    """
    Get the current applicable tax slab.
    
    Returns:
        str: Tax slab name
    """
    # Get active tax slabs
    tax_slabs = frappe.get_all(
        "Income Tax Slab",
        filters={"disabled": 0},
        fields=["name", "effective_from"],
        order_by="effective_from desc",
        limit=1
    )
    
    if tax_slabs:
        return tax_slabs[0].name
    
    return None


def get_tax_rebate(salary_slip, date_of_birth):
    """
    Calculate tax rebates based on employee age.
    
    South African tax rebates (2024/2025):
    - Primary rebate: R17,235 (all taxpayers)
    - Secondary rebate: R9,444 (age 65+)
    - Tertiary rebate: R3,145 (age 75+)
    
    Args:
        salary_slip: Salary Slip document
        date_of_birth (date): Employee date of birth
        
    Returns:
        float: Total annual tax rebate
    """
    if not date_of_birth:
        return 0
    
    # Get tax rebate settings
    rebate_settings = frappe.get_doc("Tax Rebates and Medical Tax Credit")
    
    if not rebate_settings or not rebate_settings.rebate_rates:
        frappe.log_error("Tax rebate settings not configured", "Tax Calculation")
        return 0
    
    # Calculate age as of the end of the tax year
    dob = getdate(date_of_birth)
    year_end = getdate(salary_slip.end_date)
    
    # Calculate age at end of tax year (Feb 28/29)
    age = year_end.year - dob.year
    if (year_end.month, year_end.day) < (dob.month, dob.day):
        age -= 1
    
    total_rebate = 0
    
    # Get rebates based on age
    for rebate in rebate_settings.rebate_rates:
        if rebate.rebate_type == "Primary":
            total_rebate += flt(rebate.amount)
        elif rebate.rebate_type == "Secondary" and age >= 65:
            total_rebate += flt(rebate.amount)
        elif rebate.rebate_type == "Tertiary" and age >= 75:
            total_rebate += flt(rebate.amount)
    
    return total_rebate


def get_medical_aid_credit(salary_slip, number_of_dependants):
    """
    Calculate medical aid tax credits.
    
    South African medical aid tax credits (2024/2025):
    - Main member: R364 per month
    - First dependant: R364 per month
    - Additional dependants: R246 per month each
    
    Args:
        salary_slip: Salary Slip document
        number_of_dependants (int): Number of dependants on medical aid
        
    Returns:
        float: Annual medical aid tax credit
    """
    if number_of_dependants < 0:
        return 0
    
    # Get medical aid credit settings
    credit_settings = frappe.get_doc("Tax Rebates and Medical Tax Credit")
    
    if not credit_settings or not credit_settings.medical_tax_credit_rates:
        frappe.log_error("Medical tax credit settings not configured", "Tax Calculation")
        return 0
    
    total_credit = 0
    
    for credit in credit_settings.medical_tax_credit_rates:
        if credit.beneficiary == "Main Member":
            # Main member credit
            total_credit += flt(credit.amount) * 12  # Annual amount
        elif credit.beneficiary == "First Dependant" and number_of_dependants >= 1:
            # First dependant credit
            total_credit += flt(credit.amount) * 12
        elif credit.beneficiary == "Additional Dependants" and number_of_dependants > 1:
            # Additional dependants
            additional_deps = number_of_dependants - 1
            total_credit += flt(credit.amount) * 12 * additional_deps
    
    return total_credit


def calculate_retirement_annuity_deduction(salary_slip, retirement_contribution):
    """
    Calculate allowable retirement annuity deduction for tax purposes.
    
    South African rules:
    - Maximum deduction: 27.5% of taxable income
    - Subject to annual limit (currently R350,000)
    
    Args:
        salary_slip: Salary Slip document
        retirement_contribution (float): Annual retirement contribution
        
    Returns:
        float: Allowable deduction amount
    """
    if not retirement_contribution or retirement_contribution <= 0:
        return 0
    
    # Get retirement annuity settings
    ra_slabs = frappe.get_all(
        "Retirement Annuity Slab",
        fields=["*"],
        order_by="name desc",
        limit=1
    )
    
    if not ra_slabs:
        frappe.log_error("Retirement annuity slabs not configured", "Tax Calculation")
        # Use default limits
        max_percentage = 0.275  # 27.5%
        max_annual_limit = 350000
    else:
        slab = ra_slabs[0]
        max_percentage = flt(slab.maximum_percentage) / 100
        max_annual_limit = flt(slab.annual_limit)
    
    # Calculate maximum allowable deduction
    taxable_income = flt(salary_slip.total_taxable_earnings)
    max_by_percentage = taxable_income * max_percentage
    
    # Take the minimum of:
    # 1. Actual contribution
    # 2. 27.5% of taxable income
    # 3. Annual limit
    allowable_deduction = min(
        retirement_contribution,
        max_by_percentage,
        max_annual_limit
    )
    
    return allowable_deduction


def calculate_uif_contribution(gross_pay):
    """
    Calculate UIF (Unemployment Insurance Fund) contribution.
    
    UIF rates:
    - Employee: 1% of remuneration
    - Employer: 1% of remuneration
    - Maximum monthly remuneration: R17,712 (2024/2025)
    
    Args:
        gross_pay (float): Monthly gross pay
        
    Returns:
        tuple: (employee_uif, employer_uif)
    """
    UIF_RATE = 0.01  # 1%
    UIF_MAX_MONTHLY = 17712.00  # Maximum monthly remuneration
    
    # Cap gross pay at maximum
    capped_gross = min(flt(gross_pay), UIF_MAX_MONTHLY)
    
    # Calculate contributions
    uif_amount = capped_gross * UIF_RATE
    
    return (uif_amount, uif_amount)


def calculate_sdl_contribution(gross_pay):
    """
    Calculate SDL (Skills Development Levy) contribution.
    
    SDL rate: 1% of total payroll (employer pays)
    
    Args:
        gross_pay (float): Monthly gross pay
        
    Returns:
        float: SDL amount
    """
    SDL_RATE = 0.01  # 1%
    
    sdl_amount = flt(gross_pay) * SDL_RATE
    
    return sdl_amount


def validate_south_african_id_number(id_number):
    """
    Validate South African ID number using Luhn algorithm.
    
    Format: YYMMDD SSSS CAZ
    - YYMMDD: Date of birth
    - SSSS: Gender (0000-4999 Female, 5000-9999 Male)
    - C: Citizenship (0 SA citizen, 1 Permanent resident)
    - A: Usually 8 or 9
    - Z: Checksum digit
    
    Args:
        id_number (str): 13-digit ID number
        
    Returns:
        dict: {valid: bool, gender: str, dob: date, citizenship: str} or None
    """
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        return None
    
    # Extract components
    yy = int(id_number[0:2])
    mm = int(id_number[2:4])
    dd = int(id_number[4:6])
    gender_code = int(id_number[6:10])
    citizenship_code = int(id_number[10])
    checksum = int(id_number[12])
    
    # Validate date
    if mm < 1 or mm > 12 or dd < 1 or dd > 31:
        return None
    
    # Determine century
    current_year = date.today().year % 100
    century = 1900 if yy > current_year else 2000
    year = century + yy
    
    try:
        dob = date(year, mm, dd)
    except ValueError:
        return None
    
    # Validate checksum using Luhn algorithm
    total = 0
    for i, digit in enumerate(id_number[:-1]):
        num = int(digit)
        if i % 2 == 0:
            total += num
        else:
            doubled = num * 2
            total += doubled if doubled <= 9 else doubled - 9
    
    calculated_checksum = (10 - (total % 10)) % 10
    
    if calculated_checksum != checksum:
        return None
    
    # Determine gender and citizenship
    gender = "Female" if gender_code < 5000 else "Male"
    citizenship = "SA Citizen" if citizenship_code == 0 else "Permanent Resident"
    
    return {
        "valid": True,
        "gender": gender,
        "date_of_birth": dob,
        "citizenship": citizenship
    }


def get_tax_year_dates(date_in_year=None):
    """
    Get the South African tax year dates (March 1 to Feb 28/29).
    
    Args:
        date_in_year (date): Date within the tax year
        
    Returns:
        tuple: (start_date, end_date) of tax year
    """
    if not date_in_year:
        date_in_year = date.today()
    
    year = date_in_year.year
    
    # Tax year runs from March 1 to Feb 28/29
    if date_in_year.month < 3:
        # Before March, so previous tax year
        start_date = date(year - 1, 3, 1)
        end_date = date(year, 2, 29 if year % 4 == 0 else 28)
    else:
        # March or later, current tax year
        start_date = date(year, 3, 1)
        next_year = year + 1
        end_date = date(next_year, 2, 29 if next_year % 4 == 0 else 28)
    
    return (start_date, end_date)

