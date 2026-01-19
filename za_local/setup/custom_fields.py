"""
South African Localization Custom Fields

This module handles cleanup of old custom fields.

Note: All custom fields are now deployed via fixtures (fixtures/custom_field.json),
which is Frappe's best practice. Fixtures are automatically imported during
app installation and migration.

Based on modern Frappe best practices.
"""

import frappe
from za_local.utils.hrms_detection import is_hrms_installed
from za_local.utils.setup_utils import get_property_type


def setup_custom_fields():
    """
    Cleanup function for custom fields.
    
    Note: Custom fields are now deployed via fixtures (fixtures/custom_field.json),
    which is Frappe's best practice. Fixtures are automatically imported during
    app installation and migration.
    
    This function only handles cleanup of old/incorrect fields that may exist
    from previous installations. All field creation is handled by fixtures.
    
    Frappe automatically handles:
    - Conditional logic (HRMS-only doctypes) - fields for missing doctypes are skipped
    - Field updates - fixtures update existing fields if they change
    - Field creation - all fields are created from fixtures
    """
    
    # Fields to delete if they exist (old custom_ prefix versions from previous installations)
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
        "Additional Salary": ["is_company_contribution"],  # Note: This is different - it's on Additional Salary, not Salary Component
        "Salary Component": ["is_company_contribution"],  # Remove old flag field - now using Type = "Company Contribution"
    }
    
    # Delete old fields
    deleted_count = 0
    for doctype, fieldnames in fields_to_delete_if_exist.items():
        for fieldname in fieldnames:
            custom_field_name = f"{doctype}-{fieldname}"
            if frappe.db.exists("Custom Field", custom_field_name):
                try:
                    frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
                    frappe.db.commit()
                    deleted_count += 1
                    print(f"  ✓ Deleted old custom field: {custom_field_name}")
                except Exception as e:
                    print(f"  ! Error deleting custom field {custom_field_name}: {e}")
    
    if deleted_count > 0:
        print(f"  ✓ Cleaned up {deleted_count} old custom field(s)")
    
    # All custom fields are now deployed via fixtures/custom_field.json
    # Fixtures are automatically imported during app installation/migration
    # Frappe handles conditional logic (missing doctypes) automatically
    print("  ✓ Custom fields are deployed via fixtures (fixtures/custom_field.json)")
    
    # Setup property setters
    setup_property_setters()


def setup_property_setters():
    """
    Setup property setters to modify standard field behaviors for South African requirements.
    """
    
    hrms_installed = is_hrms_installed()
    hrms_only_doctypes = {
        "Salary Structure Assignment",
        "Salary Slip",
    }

    properties = {
        "Salary Structure Assignment": {
            "variable": {"hidden": 0, "read_only": 0},
            "base": {"hidden": 0, "read_only": 0}
        },
        "Salary Slip": {
            "payroll_entry": {"hidden": 0}
        },
        "Customer": {
            "tax_id": {
                "label": "VAT Registration Number",
                "description": "South African VAT registration number (format: 4XXXXXXXXXX)"
            }
        }
        # IRP5 Certificate - No property setters needed (bulk generation handled programmatically)
    }
    
    for doctype, field_properties in properties.items():
        if doctype in hrms_only_doctypes and not hrms_installed:
            print(f"  ⊙ Skipping property setters for {doctype} (HRMS not installed)")
            continue

        if not frappe.db.exists("DocType", doctype):
            print(f"  ⊙ Skipping property setters for {doctype} (DocType not found)")
            continue

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
