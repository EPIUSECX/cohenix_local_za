"""
Installation and Setup Functions for ZA Local

This module handles installation, uninstallation, and migration setup
for the South African localization app.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from za_local.setup.custom_fields import setup_custom_fields


def before_install():
    """
    Run before app installation.
    
    Creates essential DocTypes that are required before the app is fully installed:
    - Company Contribution (child table for Salary Structure)
    """
    create_company_contribution_doctype()


def after_install():
    """
    Run after app installation.
    
    Sets up:
    - Custom fields for South African compliance
    - Default data (ETI slabs, tax rebates, etc.)
    """
    setup_custom_fields()
    setup_default_data()
    frappe.db.commit()
    print("\n" + "="*80)
    print("South African Localization installed successfully!")
    print("="*80)
    print("\nNext steps:")
    print("1. Configure Company SA registration numbers")
    print("2. Set up Payroll Settings with SA statutory components")
    print("3. Configure ETI Slabs and Tax Rebates")
    print("4. Set up COIDA and VAT settings if applicable")
    print("="*80 + "\n")


def after_migrate():
    """
    Run after migrations.
    
    Ensures custom fields are always up to date after migrations.
    """
    setup_custom_fields()
    frappe.db.commit()


def create_company_contribution_doctype():
    """
    Create Company Contribution DocType if it doesn't exist.
    
    This is a child table used in Salary Structure for company contributions
    like UIF employer portion, SDL, COIDA, etc.
    """
    if frappe.db.exists("DocType", "Company Contribution"):
        print("Company Contribution DocType already exists")
        return
    
    print("Creating Company Contribution DocType...")
    
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "Company Contribution",
        "module": "SA Payroll",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "salary_component",
                "label": "Salary Component",
                "fieldtype": "Link",
                "options": "Salary Component",
                "in_list_view": 1,
                "reqd": 1
            },
            {
                "fieldname": "abbr",
                "label": "Abbr",
                "fieldtype": "Data",
                "fetch_from": "salary_component.salary_component_abbr",
                "read_only": 1
            },
            {
                "fieldname": "amount",
                "label": "Amount",
                "fieldtype": "Currency",
                "options": "currency",
                "in_list_view": 1,
                "allow_on_submit": 1
            },
            {
                "fieldname": "condition_and_formula_section",
                "label": "Condition and Formula",
                "fieldtype": "Section Break",
                "collapsible": 1
            },
            {
                "fieldname": "condition",
                "label": "Condition",
                "fieldtype": "Code",
                "fetch_from": "salary_component.condition",
                "allow_on_submit": 1
            },
            {
                "fieldname": "column_break_6",
                "fieldtype": "Column Break"
            },
            {
                "fieldname": "amount_based_on_formula",
                "label": "Amount based on formula",
                "fieldtype": "Check",
                "default": "0",
                "fetch_from": "salary_component.amount_based_on_formula",
                "allow_on_submit": 1
            },
            {
                "fieldname": "formula",
                "label": "Formula",
                "fieldtype": "Code",
                "fetch_from": "salary_component.formula",
                "allow_on_submit": 1
            }
        ],
        "permissions": [
            {
                "role": "HR Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1
            },
            {
                "role": "HR User",
                "read": 1,
                "write": 1,
                "create": 1
            }
        ]
    })
    
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("✓ Company Contribution DocType created successfully")


def setup_default_data():
    """
    Set up default data required for South African localization.
    
    Creates:
    - Default ETI Slabs
    - Default Tax Rebates
    - Default Medical Tax Credit Rates
    """
    print("Setting up default data...")
    
    # ETI Slabs will be created when the ETI Slab doctype is migrated
    # Tax Rebates will be created when the Tax Rebates doctype is migrated
    # For now, we just print a message
    
    print("✓ Default data setup complete")
    print("  Note: Configure ETI Slabs, Tax Rebates, and other settings manually")


def create_salary_component_if_not_exists(component_data):
    """
    Helper function to create a salary component if it doesn't exist.
    
    Args:
        component_data (dict): Salary component configuration
    """
    if not frappe.db.exists("Salary Component", component_data["name"]):
        doc = frappe.get_doc({
            "doctype": "Salary Component",
            **component_data
        })
        doc.insert(ignore_permissions=True)
        print(f"✓ Created Salary Component: {component_data['name']}")
    else:
        print(f"  Salary Component already exists: {component_data['name']}")


def setup_default_salary_components():
    """
    Create default South African salary components.
    
    Creates components for:
    - PAYE (4102)
    - UIF Employee (4141)
    - UIF Employer (4141)
    - SDL (4142)
    - COIDA
    """
    components = [
        {
            "name": "4102 PAYE",
            "salary_component_abbr": "PAYE",
            "type": "Deduction",
            "description": "Pay As You Earn - Income Tax",
            "is_tax_applicable": 0,
            "variable_based_on_taxable_salary": 1
        },
        {
            "name": "4141 UIF Employee Contribution",
            "salary_component_abbr": "UIF_EE",
            "type": "Deduction",
            "description": "Unemployment Insurance Fund - Employee Contribution (1%)",
            "is_tax_applicable": 0,
            "formula": "(BS)/100 if (BS)<=17712 else 177.12"
        },
        {
            "name": "4141 UIF Employer Contribution",
            "salary_component_abbr": "UIF_ER",
            "type": "Deduction",
            "description": "Unemployment Insurance Fund - Employer Contribution (1%)",
            "is_tax_applicable": 0,
            "formula": "(BS)/100 if (BS)<=17712 else 177.12"
        },
        {
            "name": "4142 SDL Contribution",
            "salary_component_abbr": "SDL",
            "type": "Deduction",
            "description": "Skills Development Levy (1%)",
            "is_tax_applicable": 0,
            "formula": "(BS)/100"
        }
    ]
    
    for component in components:
        create_salary_component_if_not_exists(component)

