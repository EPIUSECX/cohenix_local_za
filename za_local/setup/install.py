"""
Installation and Setup Functions for ZA Local

This module handles installation, uninstallation, and migration setup
for the South African localization app.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.customize_form.customize_form import (
	docfield_properties,
	doctype_properties,
)
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from za_local.setup.custom_fields import setup_custom_fields
from za_local.setup.property_setters import get_property_setters


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
    - Property setters for default values
    - Default data (ETI slabs, tax rebates, etc.)
    - Master data from CSV files
    """
    cleanup_invalid_doctype_links()
    setup_custom_fields()
    make_property_setters()
    setup_default_data()
    apply_statutory_formulas()
    import_master_data()
    insert_custom_records()
    frappe.db.commit()
    print("\n" + "="*80)
    print("South African Localization installed successfully!")
    print("="*80)
    print("\nNext steps:")
    print("1. Configure Company SA registration numbers")
    print("2. Set up Payroll Settings with SA statutory components")
    print("3. Configure ETI Slabs and Tax Rebates")
    print("4. Set up COIDA and VAT settings if applicable")
    print("5. Configure Business Trip Settings for travel allowances")
    print("="*80 + "\n")


def after_migrate():
    """
    Run after migrations.
    
    Ensures custom fields are always up to date after migrations.
    """
    cleanup_invalid_doctype_links()
    setup_custom_fields()
    apply_statutory_formulas()
    frappe.db.commit()


def cleanup_invalid_doctype_links():
    """
    Remove invalid DocType Links from the database.
    
    These links may exist from previous installations and cause
    validation errors when creating property setters.
    """
    print("\nCleaning up invalid DocType Links...")
    
    # List of invalid links to remove: (parent_doctype, link_doctype, link_fieldname)
    invalid_links = [
        ("Payroll Entry", "EMP201 Submission", "payroll_entry"),
    ]
    
    for parent_dt, link_dt, link_field in invalid_links:
        # Find and delete invalid links
        links_to_delete = frappe.db.sql("""
            SELECT name 
            FROM `tabDocType Link` 
            WHERE parent = %s 
                AND link_doctype = %s 
                AND link_fieldname = %s
        """, (parent_dt, link_dt, link_field), as_dict=1)
        
        for link in links_to_delete:
            try:
                frappe.delete_doc("DocType Link", link.name, force=True, ignore_permissions=True)
                print(f"  ✓ Removed invalid link: {parent_dt} → {link_dt}.{link_field}")
            except Exception as e:
                print(f"  ! Error removing link {link.name}: {e}")
    
    frappe.db.commit()
    print("  ✓ Invalid DocType Links cleaned up\n")


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
        "module": "Payroll",  # Use existing Payroll module from HRMS
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


def make_property_setters():
	"""
	Create property setters for South African localization.
	
	Sets default values and customizations for standard DocTypes:
	- Default currency to ZAR
	- Hide irrelevant fields
	- Protect attachments on compliance documents
	"""
	print("Creating property setters...")
	
	for doctypes, property_setters in get_property_setters().items():
		if isinstance(doctypes, str):
			doctypes = (doctypes,)

		for doctype in doctypes:
			for property_setter in property_setters:
				if property_setter[0]:
					for_doctype = False
					property_type = docfield_properties[property_setter[1]]
				else:
					for_doctype = True
					property_type = doctype_properties[property_setter[1]]

				make_property_setter(
					doctype=doctype,
					fieldname=property_setter[0],
					property=property_setter[1],
					value=property_setter[2],
					property_type=property_type,
					for_doctype=for_doctype,
				)
	
	print("✓ Property setters created successfully")


def apply_statutory_formulas():
    """Ensure statutory Salary Components and Company Contribution rows carry correct formulas.
    - UIF Employer: (BS)/100 capped at 177.12
    - SDL: (BS)/100
    Also enable Amount based on Formula on these components and child rows.
    """
    print("Applying statutory formulas to salary components and company contribution rows...")
    components_to_update = [
        {
            "name": "4141 UIF Employer Contribution",
            "formula": "(BS)/100 if (BS)<=17712 else 177.12",
        },
        {
            "name": "4142 SDL Contribution",
            "formula": "(BS)/100",
        },
    ]
    for comp in components_to_update:
        if frappe.db.exists("Salary Component", comp["name"]):
            try:
                frappe.db.set_value(
                    "Salary Component", comp["name"], {
                        "amount_based_on_formula": 1,
                        "formula": comp["formula"],
                    }
                )
            except Exception as e:
                print(f"  ! Could not update Salary Component {comp['name']}: {e}")
    # Update existing Salary Structure child rows
    try:
        for comp in components_to_update:
            frappe.db.sql(
                """
                UPDATE `tabCompany Contribution`
                SET amount_based_on_formula = 1, formula = %(formula)s
                WHERE salary_component = %(name)s
                """,
                comp,
            )
        frappe.db.commit()
    except Exception as e:
        print(f"  ! Could not update Company Contribution child rows: {e}")
    print("✓ Statutory formulas applied")

def import_master_data():
	"""
	Import master data from CSV files.
	
	Loads predefined data for:
	- Business Trip Regions (SA cities and international rates)
	- SETA list
	- Bargaining Councils
	"""
	print("Importing master data...")
	
	try:
		from za_local.utils.csv_importer import import_all_master_data
		import_all_master_data()
	except Exception as e:
		print(f"  Warning: Could not import master data: {e}")
		print("  Master data can be imported manually later.")


def insert_custom_records():
	"""
	Insert custom records like DocType Links for bidirectional connections.
	
	Creates links between za_local DocTypes and standard ERPNext DocTypes
	so that related records show in the Connections tab.
	"""
	print("Inserting custom records...")
	
	for custom_record in frappe.get_hooks("za_local_custom_records"):
		filters = custom_record.copy()
		# Clean up filters. They need to be a plain dict without nested dicts or lists.
		for key, value in custom_record.items():
			if isinstance(value, (list, dict)):
				del filters[key]

		if not frappe.db.exists(filters):
			frappe.get_doc(custom_record).insert(ignore_if_duplicate=True)
	
	print("✓ Custom records inserted successfully")


def setup_default_retirement_funds():
	"""Create default retirement fund types for South African retirement planning"""
	retirement_funds = [
		{"fund_name": "Company Pension Fund", "fund_type": "Pension"},
		{"fund_name": "Company Provident Fund", "fund_type": "Provident"},
		{"fund_name": "Retirement Annuity", "fund_type": "Retirement Annuity"},
	]
	
	for fund in retirement_funds:
		if not frappe.db.exists("Retirement Fund", {"fund_name": fund["fund_name"]}):
			try:
				doc = frappe.get_doc({
					"doctype": "Retirement Fund",
					**fund,
					"employee_contribution_percentage": 7.5,
					"employer_contribution_percentage": 10.0,
					"tax_deductible_limit": 27.5,  # 27.5% of taxable income
					"company": frappe.defaults.get_defaults().get("company")
				})
				doc.insert(ignore_permissions=True)
			except Exception as e:
				print(f"! Could not create retirement fund {fund['fund_name']}: {e}")
	
	print("✓ Default retirement funds created")


def run_za_local_setup(setup_doc):
	"""
	Execute za_local setup based on user selections.
	Called from ZA Local Setup DocType when user completes the setup wizard.
	
	Args:
		setup_doc: ZA Local Setup document instance
	"""
	import json
	from pathlib import Path
	
	setup_doc.setup_status = "In Progress"
	setup_doc.save()
	frappe.db.commit()
	
	try:
		data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
		
		# Load salary components
		if setup_doc.load_salary_components:
			load_data_from_json(data_dir / "salary_components.json")
			print("✓ Loaded statutory salary components")
		
		if setup_doc.load_earnings_components:
			load_data_from_json(data_dir / "earnings_components.json")
			print("✓ Loaded earnings components")
		
		# Load tax configuration
		if setup_doc.load_tax_slabs:
			load_data_from_json(data_dir / "tax_slabs_2024.json")
			print("✓ Loaded 2024-2025 tax slabs")
		
        if setup_doc.load_tax_rebates or setup_doc.load_medical_credits:
			load_data_from_json(data_dir / "tax_rebates_2024.json")
			print("✓ Loaded tax rebates and medical tax credits")
		
		# Load master data
		if setup_doc.load_business_trip_regions:
			from za_local.utils.csv_importer import import_csv_data
			import_csv_data("Business Trip Region", "business_trip_region.csv")
			print("✓ Loaded business trip regions")
		
		# Mark as completed
		setup_doc.setup_status = "Completed"
		setup_doc.setup_completed_on = frappe.utils.now()
		setup_doc.save()
		frappe.db.commit()
		
		frappe.msgprint("✅ South African localization setup completed successfully!")
		
	except Exception as e:
		setup_doc.setup_status = "Pending"
		setup_doc.save()
		frappe.db.commit()
		frappe.log_error(f"Setup failed: {str(e)}", "ZA Local Setup")
		frappe.throw(f"Setup failed: {str(e)}")


def load_data_from_json(file_path):
	"""
	Load data from JSON file and insert into database.
	
	Args:
		file_path: Path to JSON file
	"""
	import json
	
	with open(file_path, "r") as f:
		data = json.load(f)
	
	# Handle different JSON formats
	if isinstance(data, dict):
		# Check if it's a single record (has "doctype" key)
		if "doctype" in data:
			# Single record
			insert_record(data)
		else:
			# Dict with DocType as key
			for doctype, records in data.items():
				for record in records:
					# Add doctype to record if not present
					if "doctype" not in record:
						record["doctype"] = doctype
					insert_record(record)
	elif isinstance(data, list):
		# List of records
		for record in data:
			insert_record(record)


def insert_record(record):
	"""
	Insert a single record, skip if exists.
	Handles both regular DocTypes and Single DocTypes.
	
	Args:
		record: Dict with doctype and field values
	"""
	doctype = record.get("doctype")
	name = record.get("name") or record.get("salary_component")
	
	# Check if it's a Single DocType
	meta = frappe.get_meta(doctype)
	is_single = meta.issingle
	
	# Handle company field - set to first company if empty
	if "company" in record and not record.get("company"):
		companies = frappe.get_all("Company", limit=1)
		if companies:
			record["company"] = companies[0].name
	
	try:
		# Suppress validation warnings during setup (e.g., "Accounts not set")
		# These are expected and users will configure accounts later
		_message_log = frappe.local.message_log
		frappe.local.message_log = []
		
		if is_single:
			# For Single DocTypes, always update (don't check exists)
			doc = frappe.get_single(doctype)
			# Update fields from record
			for key, value in record.items():
				if key != "doctype":
					doc.set(key, value)
			doc.save(ignore_permissions=True)
			print(f"  ✓ Updated Single DocType: {doctype}")
		else:
			# For regular DocTypes, check if exists
			if not frappe.db.exists(doctype, name):
				doc = frappe.get_doc(record)
				doc.insert(ignore_permissions=True, ignore_mandatory=True)
				print(f"  ✓ Created {doctype}: {name}")
			else:
				print(f"  ⊙ Skipped {doctype}: {name} (already exists)")
		
		# Restore message log
		frappe.local.message_log = _message_log
	except Exception as e:
		# Restore message log even on error
		frappe.local.message_log = _message_log
		print(f"  ✗ Error with {doctype} {name}: {e}")
		import traceback
		traceback.print_exc()

