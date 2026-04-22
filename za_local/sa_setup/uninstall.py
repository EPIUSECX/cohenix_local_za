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
    Names are taken from setup/custom_fields.py (CUSTOM_FIELD_FIXTURES_JSON) so they stay in sync.
    """
    import json
    print("Removing custom fields...")
    from za_local.sa_setup.custom_fields import CUSTOM_FIELD_FIXTURES_JSON
    data = json.loads(CUSTOM_FIELD_FIXTURES_JSON)
    custom_field_names = [d["name"] for d in data]
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
    
    from za_local.sa_setup.property_setters import get_property_setters
    
    count = 0
    for doctypes, property_setters in get_property_setters().items():
        if isinstance(doctypes, str):
            doctypes = (doctypes,)

        for doctype in doctypes:
            for property_setter in property_setters:
                try:
                    frappe.db.delete(
                        "Property Setter",
                        {
                            "doc_type": doctype,
                            "field_name": property_setter[0],
                            "property": property_setter[1],
                            "value": property_setter[2],
                        },
                    )
                    count += 1
                except Exception as e:
                    print(f"  Warning: Could not delete property setter for {doctype}.{property_setter[0]}: {e}")
    
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

