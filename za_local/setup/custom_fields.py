"""
South African Localization Custom Fields

This module creates custom fields for South African payroll, tax, VAT, and COIDA compliance.
All fields use the 'za_' prefix for consistency and clarity.

Based on modern Frappe best practices.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_custom_fields():
    """
    Setup all custom fields for South African localization.
    
    This function creates custom fields across multiple doctypes:
    - Employee: SA ID, employee type, hours per month, payroll account
    - Company: VAT number, COIDA registration, SDL/UIF reference numbers
    - Payroll Settings: SA tax calculation options, statutory components
    - Salary Structure Assignment: Annual bonus
    - Additional Salary: Company contribution flag
    - IRP5 Certificate: Bulk generation fields
    - Payroll Employee Detail: Journal entry tracking
    - Journal Entry Account: Payroll entry references
    - Salary Component: Additional calculation fields
    - Salary Structure: Company contributions
    - Employee Benefit Claim: SA-specific fields
    """
    
    # Fields to delete if they exist (old custom_ prefix versions)
    fields_to_delete_if_exist = {
        "Employee": [
            "custom_id_number", "custom_employee_type", "custom_special_economic_zone",
            "custom_hours_per_month", "payroll_payable_bank_account"
        ],
        "Company": [
            "custom_coida_registration_number", "custom_vat_number",
            "custom_sdl_reference_number", "custom_uif_reference_number"
        ],
        "Payroll Settings": [
            "custom_coida_salary_component", "custom_disable_eti_calculation"
        ],
        "Salary Structure Assignment": ["custom_annual_bonus"],
        "Additional Salary": ["is_company_contribution"],
    }
    
    # Delete old fields
    for doctype, fieldnames in fields_to_delete_if_exist.items():
        for fieldname in fieldnames:
            custom_field_name = f"{doctype}-{fieldname}"
            if frappe.db.exists("Custom Field", custom_field_name):
                try:
                    frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
                    frappe.db.commit()
                    print(f"Deleted existing custom field: {custom_field_name}")
                except Exception as e:
                    print(f"Error deleting custom field {custom_field_name}: {e}")

    # Define all custom fields
    custom_fields = {
        "HR Settings": [
            {
                "fieldname": "za_amount_per_kilometer",
                "label": "Amount Per Kilometer",
                "fieldtype": "Currency",
                "insert_after": "emp_created_by",
                "description": "Reimbursement rate per kilometer for mileage claims"
            }
        ],
        
        "Payroll Settings": [
            {
                "fieldname": "za_south_african_settings_section",
                "label": "South African Settings",
                "fieldtype": "Section Break",
                "insert_after": "daily_wages_fraction_for_half_day",
                "collapsible": 1
            },
            {
                "fieldname": "za_calculate_annual_taxable_amount_based_on",
                "label": "Calculate Annual Taxable Amount Based On",
                "fieldtype": "Select",
                "options": "\nJoining and Relieving Date\nPayroll Period",
                "default": "Payroll Period",
                "insert_after": "za_south_african_settings_section",
                "description": "Method for calculating annual taxable income"
            },
            {
                "fieldname": "za_payroll_column_break",
                "fieldtype": "Column Break",
                "insert_after": "za_calculate_annual_taxable_amount_based_on"
            },
            {
                "fieldname": "za_disable_eti_calculation",
                "label": "Disable ETI Calculation",
                "fieldtype": "Check",
                "insert_after": "za_payroll_column_break",
                "description": "Disable automatic Employment Tax Incentive calculations"
            },
            {
                "fieldname": "za_statutory_components_section",
                "label": "South African Statutory Components",
                "fieldtype": "Section Break",
                "insert_after": "za_disable_eti_calculation",
                "collapsible": 1
            },
            {
                "fieldname": "za_paye_salary_component",
                "label": "PAYE Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "insert_after": "za_statutory_components_section",
                "description": "Salary Component used for Pay As You Earn (PAYE) tax"
            },
            {
                "fieldname": "za_uif_employee_salary_component",
                "label": "UIF Employee Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "insert_after": "za_paye_salary_component",
                "description": "Salary Component for UIF employee contribution"
            },
            {
                "fieldname": "za_uif_employer_salary_component",
                "label": "UIF Employer Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "insert_after": "za_uif_employee_salary_component",
                "description": "Salary Component for UIF employer contribution"
            },
            {
                "fieldname": "za_statutory_column_break",
                "fieldtype": "Column Break",
                "insert_after": "za_uif_employer_salary_component"
            },
            {
                "fieldname": "za_sdl_salary_component",
                "label": "SDL Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "insert_after": "za_statutory_column_break",
                "description": "Salary Component for Skills Development Levy (SDL)"
            },
            {
                "fieldname": "za_coida_salary_component",
                "label": "COIDA Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "insert_after": "za_sdl_salary_component",
                "description": "Salary Component for Compensation for Occupational Injuries and Diseases Act (COIDA)"
            }
        ],
        
        "Employee": [
            {
                "fieldname": "za_south_african_details_section",
                "label": "South African Details",
                "fieldtype": "Section Break",
                "insert_after": "passport_number",
                "collapsible": 1
            },
            {
                "fieldname": "za_id_number",
                "label": "SA ID Number",
                "fieldtype": "Data",
                "insert_after": "za_south_african_details_section",
                "description": "South African ID Number (13 digits)",
                "length": 13
            },
            {
                "fieldname": "za_employee_type",
                "label": "Employee Type",
                "fieldtype": "Link",
                "options": "Employee Type",
                "insert_after": "za_id_number",
                "description": "South African employee classification",
                "reqd": 1
            },
            {
                "fieldname": "za_special_economic_zone",
                "label": "Special Economic Zone",
                "fieldtype": "Check",
                "insert_after": "za_employee_type",
                "description": "Employee works in a Special Economic Zone (SEZ)"
            },
            {
                "fieldname": "za_payroll_column_break",
                "fieldtype": "Column Break",
                "insert_after": "za_special_economic_zone"
            },
            {
                "fieldname": "za_hours_per_month",
                "label": "Hours Per Month",
                "fieldtype": "Float",
                "insert_after": "za_payroll_column_break",
                "description": "Standard working hours per month for ETI calculations"
            },
            {
                "fieldname": "za_payroll_payable_bank_account",
                "label": "Payroll Payable Bank Account",
                "fieldtype": "Link",
                "options": "Bank Account",
                "insert_after": "za_hours_per_month",
                "description": "Bank account for payroll disbursement"
            }
        ],
        
        "Company": [
            {
                "fieldname": "za_south_african_registration_section",
                "label": "South African Registration Details",
                "fieldtype": "Section Break",
                "insert_after": "tax_id",
                "collapsible": 1
            },
            {
                "fieldname": "za_vat_number",
                "label": "VAT Number",
                "fieldtype": "Data",
                "insert_after": "za_south_african_registration_section",
                "description": "South African VAT Registration Number",
                "length": 10
            },
            {
                "fieldname": "za_coida_registration_number",
                "label": "COIDA Registration Number",
                "fieldtype": "Data",
                "insert_after": "za_vat_number",
                "description": "Compensation for Occupational Injuries and Diseases Act Registration Number"
            },
            {
                "fieldname": "za_registration_column_break",
                "fieldtype": "Column Break",
                "insert_after": "za_coida_registration_number"
            },
            {
                "fieldname": "za_sdl_reference_number",
                "label": "SDL Reference Number",
                "fieldtype": "Data",
                "insert_after": "za_registration_column_break",
                "description": "Skills Development Levy Reference Number"
            },
            {
                "fieldname": "za_uif_reference_number",
                "label": "UIF Reference Number",
                "fieldtype": "Data",
                "insert_after": "za_sdl_reference_number",
                "description": "Unemployment Insurance Fund Reference Number"
            }
        ],
        
        "Additional Salary": [
            {
                "fieldname": "za_is_company_contribution",
                "label": "Is Company Contribution",
                "fieldtype": "Check",
                "insert_after": "column_break_8",
                "description": "Mark as company contribution for payroll processing"
            }
        ],
        
        "Salary Structure Assignment": [
            {
                "fieldname": "za_annual_bonus",
                "label": "Annual Bonus",
                "fieldtype": "Currency",
                "insert_after": "base",
                "allow_on_submit": 1,
                "description": "Annual bonus amount for tax calculations"
            }
        ],
        
        "IRP5 Certificate": [
            {
                "fieldname": "za_generation_mode",
                "label": "Generation Mode",
                "fieldtype": "Select",
                "options": "Individual\nBulk",
                "default": "Individual",
                "insert_after": "certificate_type",
                "description": "Certificate generation mode"
            },
            {
                "fieldname": "za_bulk_generation_section",
                "label": "Bulk Generation",
                "fieldtype": "Section Break",
                "insert_after": "za_generation_mode",
                "depends_on": "eval:doc.za_generation_mode=='Bulk'",
                "collapsible": 1
            },
            {
                "fieldname": "za_bulk_department",
                "label": "Department Filter",
                "fieldtype": "Link",
                "options": "Department",
                "insert_after": "za_bulk_generation_section",
                "description": "Generate certificates for specific department"
            },
            {
                "fieldname": "za_bulk_employee_list",
                "label": "Employee List",
                "fieldtype": "Table",
                "options": "IRP5 Bulk Employee",
                "insert_after": "za_bulk_department",
                "description": "List of employees for bulk generation"
            }
        ],
        
        "Payroll Employee Detail": [
            {
                "fieldname": "za_is_bank_entry_created",
                "label": "Is Bank Entry Created",
                "fieldtype": "Check",
                "insert_after": "custom_employee_type",
                "read_only": 1,
                "description": "Indicates if bank entry has been created"
            },
            {
                "fieldname": "za_is_company_contribution_created",
                "label": "Is Company Contribution Created",
                "fieldtype": "Check",
                "insert_after": "za_is_bank_entry_created",
                "read_only": 1,
                "description": "Indicates if company contribution entry has been created"
            }
        ],
        
        "Journal Entry Account": [
            {
                "fieldname": "za_is_payroll_entry",
                "label": "Is Payroll Entry",
                "fieldtype": "Check",
                "insert_after": "reference_name",
                "description": "Mark as payroll-related journal entry"
            },
            {
                "fieldname": "za_is_company_contribution",
                "label": "Is Company Contribution",
                "fieldtype": "Check",
                "insert_after": "za_is_payroll_entry",
                "description": "Mark as company contribution entry"
            }
        ]
    }
    
    # Create custom fields
    create_custom_fields(custom_fields)
    
    # Setup property setters
    setup_property_setters()
    
    print("✓ South African custom fields created successfully")


def setup_property_setters():
    """
    Setup property setters to modify standard field behaviors for South African requirements.
    """
    
    properties = {
        "Salary Structure Assignment": {
            "variable": {"hidden": 0, "read_only": 0},
            "base": {"hidden": 0, "read_only": 0}
        },
        "Salary Slip": {
            "payroll_entry": {"hidden": 0}
        },
        "IRP5 Certificate": {
            "employee": {
                "reqd": 0,
                "mandatory_depends_on": "eval:doc.za_generation_mode!='Bulk'",
                "depends_on": "eval:doc.za_generation_mode!='Bulk'"
            },
            "certificate_number": {
                "reqd": 0,
                "mandatory_depends_on": "eval:doc.za_generation_mode!='Bulk'"
            }
        }
    }
    
    for doctype, field_properties in properties.items():
        for fieldname, props in field_properties.items():
            for prop, value in props.items():
                try:
                    frappe.make_property_setter({
                        "doctype": doctype,
                        "fieldname": fieldname,
                        "property": prop,
                        "value": value,
                        "property_type": get_property_type(value)
                    })
                except Exception as e:
                    print(f"Error setting property {prop} for {doctype}.{fieldname}: {e}")
    
    print("✓ Property setters configured successfully")


def get_property_type(value):
    """Get the property type based on value type."""
    if isinstance(value, bool) or isinstance(value, int):
        return "Check"
    elif isinstance(value, str):
        if value.startswith("eval:"):
            return "Code"
        return "Data"
    else:
        return "Data"


def validate_south_african_id(id_number):
    """
    Validate South African ID number format and checksum.
    
    Format: YYMMDD SSSS CAZ
    - YYMMDD: Date of birth
    - SSSS: Gender (Females: 0000-4999, Males: 5000-9999)
    - C: Citizenship (0: SA, 1: Permanent resident)
    - A: Usually 8 or 9 (historical)
    - Z: Checksum digit (Luhn algorithm)
    
    Args:
        id_number (str): South African ID number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not id_number or not id_number.isdigit() or len(id_number) != 13:
        return False
        
    # Birth date validation
    year = int(id_number[:2])
    month = int(id_number[2:4])
    day = int(id_number[4:6])
    
    if month < 1 or month > 12 or day < 1 or day > 31:
        return False
        
    # Calculate checksum using Luhn algorithm
    checksum = 0
    for i, digit in enumerate(id_number[:-1]):
        num = int(digit)
        if i % 2 == 0:
            checksum += num
        else:
            checksum += (num * 2 if num * 2 <= 9 else num * 2 - 9)
            
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit == int(id_number[-1])

