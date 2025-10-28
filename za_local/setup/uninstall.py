"""
Uninstallation Functions for ZA Local

Handles clean removal of South African localization customizations.
"""

import frappe


def after_uninstall():
    """
    Run after app uninstallation.
    
    Cleans up:
    - Custom fields with za_ prefix
    - Property setters
    - Custom doctypes (with confirmation)
    
    Note: This does NOT delete data, only customizations.
    """
    print("\n" + "="*80)
    print("Uninstalling South African Localization...")
    print("="*80 + "\n")
    
    # Remove custom fields
    remove_custom_fields()
    
    # Remove property setters
    remove_property_setters()
    
    # Clean up custom DocTypes (optional - with data preservation)
    cleanup_custom_doctypes()
    
    frappe.db.commit()
    
    print("\n" + "="*80)
    print("South African Localization uninstalled successfully!")
    print("="*80)
    print("\nNote: Your data has been preserved.")
    print("If you want to remove SA-specific DocTypes and data,")
    print("please do so manually through the DocType List.")
    print("="*80 + "\n")


def remove_custom_fields():
    """
    Remove all custom fields created by za_local app.
    
    Removes all fields defined in the custom_fields setup.
    """
    print("Removing custom fields...")
    
    # Import to get the field definitions
    from za_local.setup.custom_fields import setup_custom_fields
    
    # Define all custom field names we created
    custom_field_names = [
        # HR Settings
        "HR Settings-za_amount_per_kilometer",
        
        # Payroll Settings
        "Payroll Settings-za_south_african_settings_section",
        "Payroll Settings-za_calculate_annual_taxable_amount_based_on",
        "Payroll Settings-za_payroll_column_break",
        "Payroll Settings-za_disable_eti_calculation",
        "Payroll Settings-za_statutory_components_section",
        "Payroll Settings-za_paye_salary_component",
        "Payroll Settings-za_uif_employee_salary_component",
        "Payroll Settings-za_uif_employer_salary_component",
        "Payroll Settings-za_statutory_column_break",
        "Payroll Settings-za_sdl_salary_component",
        "Payroll Settings-za_coida_salary_component",
        
        # Employee
        "Employee-za_south_african_details_section",
        "Employee-za_id_number",
        "Employee-za_employee_type",
        "Employee-za_special_economic_zone",
        "Employee-za_payroll_column_break",
        "Employee-za_hours_per_month",
        "Employee-za_payroll_payable_bank_account",
        
        # Company
        "Company-za_south_african_registration_section",
        "Company-za_vat_number",
        "Company-za_coida_registration_number",
        "Company-za_registration_column_break",
        "Company-za_sdl_reference_number",
        "Company-za_uif_reference_number",
        
        # Additional Salary
        "Additional Salary-za_is_company_contribution",
        
        # Salary Structure Assignment
        "Salary Structure Assignment-za_annual_bonus",
        
        # IRP5 Certificate - No custom fields added
        
        # Payroll Employee Detail
        "Payroll Employee Detail-za_is_bank_entry_created",
        "Payroll Employee Detail-za_is_company_contribution_created",
        
        # Journal Entry Account
        "Journal Entry Account-za_is_payroll_entry",
        "Journal Entry Account-za_is_company_contribution",
    ]
    
    count = 0
    for field_name in custom_field_names:
        if frappe.db.exists("Custom Field", field_name):
            try:
                frappe.delete_doc("Custom Field", field_name, ignore_permissions=True, force=True)
                count += 1
            except Exception as e:
                print(f"  Warning: Could not delete custom field {field_name}: {e}")
    
    frappe.db.commit()
    print(f"✓ Removed {count} custom fields")


def remove_property_setters():
    """
    Remove property setters created by za_local app.
    """
    print("Removing property setters...")
    
    # Define property setters we created
    property_setters = [
        # No property setters were created
    ]
    
    count = 0
    for ps_def in property_setters:
        ps_name = frappe.db.get_value(
            "Property Setter",
            {
                "doc_type": ps_def["doc_type"],
                "field_name": ps_def["field_name"],
                "property": ps_def["property"]
            }
        )
        
        if ps_name:
            try:
                frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True, force=True)
                count += 1
            except Exception as e:
                print(f"  Warning: Could not delete property setter {ps_name}: {e}")
    
    frappe.db.commit()
    print(f"✓ Removed {count} property setters")


def cleanup_custom_doctypes():
    """
    List custom DocTypes created by za_local for optional manual cleanup.
    
    Does NOT automatically delete to preserve data.
    """
    print("\nThe following DocTypes were created by ZA Local:")
    print("(These have NOT been deleted to preserve your data)")
    print("-" * 80)
    
    modules = ["SA Payroll", "SA Tax", "SA VAT", "COIDA"]
    
    doctypes = frappe.get_all(
        "DocType",
        filters={"module": ["in", modules], "custom": 1},
        fields=["name", "module"],
        order_by="module, name"
    )
    
    if doctypes:
        current_module = None
        for dt in doctypes:
            if dt.module != current_module:
                current_module = dt.module
                print(f"\n{current_module}:")
            print(f"  - {dt.name}")
        
        print("\n" + "-" * 80)
        print("To remove these DocTypes and their data, delete them manually")
        print("from: Setup > DocType List")
    else:
        print("  No custom DocTypes found.")
    
    print("-" * 80)


def preserve_data_warning():
    """
    Display warning about data preservation.
    """
    print("\n" + "!"*80)
    print("IMPORTANT: Data Preservation")
    print("!"*80)
    print("\nThe uninstallation process preserves all your data:")
    print("- Employee records with SA ID numbers")
    print("- IRP5 Certificates")
    print("- EMP201/EMP501 submissions")
    print("- COIDA and VAT records")
    print("\nTo completely remove all SA localization data:")
    print("1. Manually delete records from each DocType")
    print("2. Then delete the DocTypes themselves")
    print("3. Run: bench clear-cache")
    print("!"*80 + "\n")

