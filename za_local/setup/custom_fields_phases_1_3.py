"""
Phase 1-3 Custom Fields Addition
Add these fields to custom_fields.py
"""

PHASE_1_3_CUSTOM_FIELDS = {
    # Phase 1.3: Travel Allowance - Add to Employee
    "za_travel_allowance_section": {
        "fieldname": "za_travel_allowance_section",
        "label": "Travel Allowance",
        "fieldtype": "Section Break",
        "insert_after": "za_payroll_payable_bank_account",
        "collapsible": 1
    },
    "za_travel_allowance_type": {
        "fieldname": "za_travel_allowance_type",
        "label": "Travel Allowance Type",
        "fieldtype": "Select",
        "options": "\nReimbursive (Actual km)\nFixed Allowance (80/20 split)\nNone",
        "insert_after": "za_travel_allowance_section"
    },
    
    # Phase 1.4: Retirement Fund - Add to Employee
    "za_retirement_fund": {
        "fieldname": "za_retirement_fund",
        "label": "Retirement Fund",
        "fieldtype": "Link",
        "options": "Retirement Fund",
        "insert_after": "za_travel_allowance_type"
    },
    "za_retirement_contribution_percentage": {
        "fieldname": "za_retirement_contribution_percentage",
        "label": "Retirement Contribution %",
        "fieldtype": "Percent",
        "insert_after": "za_retirement_fund"
    },
    
    # Phase 3.1: Employment Equity - Add new Tab to Employee
    "za_employment_equity_tab": {
        "fieldname": "za_employment_equity_tab",
        "label": "Employment Equity",
        "fieldtype": "Tab Break",
        "insert_after": "internal_work_history"
    },
    "za_race": {
        "fieldname": "za_race",
        "label": "Race",
        "fieldtype": "Select",
        "options": "\nAfrican\nColoured\nIndian\nWhite\nOther",
        "insert_after": "za_employment_equity_tab"
    },
    "za_is_disabled": {
        "fieldname": "za_is_disabled",
        "label": "Is Disabled",
        "fieldtype": "Check",
        "insert_after": "za_race"
    },
    "za_disability_type": {
        "fieldname": "za_disability_type",
        "label": "Disability Type",
        "fieldtype": "Data",
        "insert_after": "za_is_disabled",
        "depends_on": "eval:doc.za_is_disabled==1"
    },
    "za_ee_column_break": {
        "fieldname": "za_ee_column_break",
        "fieldtype": "Column Break",
        "insert_after": "za_disability_type"
    },
    "za_is_foreign_national": {
        "fieldname": "za_is_foreign_national",
        "label": "Foreign National",
        "fieldtype": "Check",
        "insert_after": "za_ee_column_break"
    },
    "za_occupational_level": {
        "fieldname": "za_occupational_level",
        "label": "Occupational Level (EE)",
        "fieldtype": "Select",
        "options": "\nTop Management\nSenior Management\nProfessionally Qualified\nSkilled Technical\nSemi-Skilled\nUnskilled\nTemporary\nNon-Permanent",
        "insert_after": "za_is_foreign_national",
        "description": "EEA occupational categories for Employment Equity reporting"
    },
    
    # Phase 2.1: Leave Type custom fields
    "Leave Type": {
        "za_medical_certificate_required_after": {
            "fieldname": "za_medical_certificate_required_after",
            "label": "Medical Certificate Required After (Days)",
            "fieldtype": "Int",
            "default": 2,
            "insert_after": "is_lwp",
            "description": "Number of consecutive days after which medical certificate is mandatory"
        },
        "za_applicable_gender": {
            "fieldname": "za_applicable_gender",
            "label": "Applicable Gender",
            "fieldtype": "Select",
            "options": "\nMale\nFemale\nOther",
            "insert_after": "za_medical_certificate_required_after"
        },
        "za_bcea_compliant": {
            "fieldname": "za_bcea_compliant",
            "label": "BCEA Compliant",
            "fieldtype": "Check",
            "default": 1,
            "insert_after": "za_applicable_gender"
        }
    },
    
    # Company SETA field
    "Company": {
        "za_seta": {
            "fieldname": "za_seta",
            "label": "SETA",
            "fieldtype": "Select",
            "options": "\nBanking SETA\nConstruction SETA\nEducation Training SETA\nHealth & Welfare SETA\nManufacturing SETA\nServices SETA\nTransport SETA\nOther",
            "insert_after": "za_uif_reference_number",
            "description": "Sector Education and Training Authority"
        }
    }
}

def add_phase_1_3_fields():
    """
    Add Phase 1-3 custom fields to existing setup
    
    Usage in custom_fields.py:
    - Add travel allowance fields to Employee section
    - Add retirement fund fields to Employee section  
    - Add Employment Equity tab and fields to Employee
    - Add Leave Type custom fields
    - Add Company SETA field
    """
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    # Employee fields
    employee_additions = [
        PHASE_1_3_CUSTOM_FIELDS["za_travel_allowance_section"],
        PHASE_1_3_CUSTOM_FIELDS["za_travel_allowance_type"],
        PHASE_1_3_CUSTOM_FIELDS["za_retirement_fund"],
        PHASE_1_3_CUSTOM_FIELDS["za_retirement_contribution_percentage"],
        PHASE_1_3_CUSTOM_FIELDS["za_employment_equity_tab"],
        PHASE_1_3_CUSTOM_FIELDS["za_race"],
        PHASE_1_3_CUSTOM_FIELDS["za_is_disabled"],
        PHASE_1_3_CUSTOM_FIELDS["za_disability_type"],
        PHASE_1_3_CUSTOM_FIELDS["za_ee_column_break"],
        PHASE_1_3_CUSTOM_FIELDS["za_is_foreign_national"],
        PHASE_1_3_CUSTOM_FIELDS["za_occupational_level"],
    ]
    
    custom_fields_to_add = {
        "Employee": employee_additions,
        "Leave Type": list(PHASE_1_3_CUSTOM_FIELDS["Leave Type"].values()),
        "Company": [PHASE_1_3_CUSTOM_FIELDS["Company"]["za_seta"]]
    }
    
    create_custom_fields(custom_fields_to_add)
    print("✓ Phase 1-3 custom fields added successfully")

if __name__ == "__main__":
    add_phase_1_3_fields()

