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
from frappe.utils.fixtures import import_fixtures
from za_local.setup.custom_fields import setup_custom_fields
from za_local.setup.property_setters import get_property_setters
from za_local.setup.monkey_patches import setup_all_monkey_patches
from za_local.utils.hrms_detection import is_hrms_installed


UIF_FORMULA = "(gross_pay * 0.01) if (gross_pay * 0.01) <= 177.12 else 177.12"
SDL_FORMULA = "gross_pay * 0.01"


def sync_za_local():
	"""
	Unified sync: other fixtures (property setter, print format, app) then setup/custom_fields.
	Custom fields, cleanup, property setters, and DocType Links all live in custom_fields.py
	and run in one order via setup_custom_fields().
	"""
	import_fixtures("za_local")
	setup_custom_fields()


def before_install():
	"""
	Run before app installation.
	
	Creates essential DocTypes that are required before the app is fully installed:
	- Company Contribution (child table for Salary Structure) - only if HRMS is installed
	"""
	# Only create Company Contribution if HRMS is available
	# This is called during install, so we check if HRMS will be available
	try:
		create_company_contribution_doctype()
	except Exception as e:
		# Don't fail installation if this can't be created
		print(f"  ! Could not create Company Contribution DocType: {e}")
		print("  Note: This is only needed when HRMS is installed")


def after_install():
	"""
	Run after app installation.

	Unified setup order (sync_za_local): fixtures → custom fields + property setters → custom records.
	Then: make_property_setters, monkey patches, default data, master data, workspace/module visibility.

	Note: All setup tasks are handled here, not in patches.txt.
	Patches should only be used for one-time data migrations, not setup tasks.
	"""
	cleanup_invalid_doctype_links()
	sync_za_local()  # fixtures → custom fields (cleanup + property setters) → custom records
	make_property_setters()
	setup_all_monkey_patches()
	setup_default_data()
	apply_statutory_formulas()
	import_master_data()
	cleanup_orphaned_workspace_records()
	ensure_modules_visible()
	set_accounts_settings_for_za_vat()
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

	Same sync order as install (sync_za_local): fixtures → custom fields + property setters → custom records.
	Then: make_property_setters, monkey patches, statutory formulas, workspace/module visibility.
	"""
	cleanup_invalid_doctype_links()
	sync_za_local()  # fixtures → custom fields (cleanup + property setters) → custom records
	make_property_setters()
	setup_all_monkey_patches()
	apply_statutory_formulas()
	cleanup_orphaned_workspace_records()
	ensure_modules_visible()
	set_accounts_settings_for_za_vat()
	frappe.db.commit()


def set_accounts_settings_for_za_vat():
	"""
	Set Accounts Settings for ZA VAT so tax rows come from document templates only.
	- add_taxes_from_taxes_and_charges_template = 1: Sales/Purchase Templates define tax rows (VAT Collected / VAT Paid).
	- add_taxes_from_item_tax_template = 0: Item templates only affect rate per item, not which accounts appear.
	This prevents VAT Collected (sales) from appearing on Purchase Invoices when items have a Sales-oriented template.
	"""
	try:
		if not frappe.db.table_exists("Accounts Settings"):
			return
		settings = frappe.get_single("Accounts Settings")
		settings.add_taxes_from_taxes_and_charges_template = 1
		settings.add_taxes_from_item_tax_template = 0
		settings.flags.ignore_permissions = True
		settings.save()
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="ZA Local: Set Accounts Settings for VAT",
		)


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


def cleanup_orphaned_workspace_records():
	"""
	Remove orphaned workspace and desktop icon records from za_local.
	
	Since we removed workspace management, we need to clean up any
	existing workspace and desktop icon records that were created by
	the old workspace management code.
	"""
	print("\nCleaning up orphaned workspace records...")
	
	# Remove all za_local workspaces (we no longer use custom workspaces)
	workspaces = frappe.get_all(
		"Workspace",
		filters={"app": "za_local"},
		fields=["name"]
	)
	for ws in workspaces:
		try:
			frappe.delete_doc("Workspace", ws.name, force=True, ignore_permissions=True)
			print(f"  ✓ Removed workspace: {ws.name}")
		except Exception as e:
			print(f"  ! Could not remove workspace '{ws.name}': {e}")
	
	# Remove all za_local desktop icons (we no longer use custom desktop icons)
	desktop_icons = frappe.get_all(
		"Desktop Icon",
		filters={"app": "za_local"},
		fields=["name", "label"]
	)
	for icon in desktop_icons:
		try:
			frappe.delete_doc("Desktop Icon", icon.name, force=True, ignore_permissions=True)
			print(f"  ✓ Removed desktop icon: {icon.label}")
		except Exception as e:
			print(f"  ! Could not remove desktop icon '{icon.label}': {e}")
	
	# Remove all za_local workspace sidebars
	sidebars = frappe.get_all(
		"Workspace Sidebar",
		filters={"app": "za_local"},
		fields=["name"]
	)
	for sidebar in sidebars:
		try:
			frappe.delete_doc("Workspace Sidebar", sidebar.name, force=True, ignore_permissions=True)
			print(f"  ✓ Removed workspace sidebar: {sidebar.name}")
		except Exception as e:
			print(f"  ! Could not remove workspace sidebar '{sidebar.name}': {e}")
	
	frappe.db.commit()
	print("  ✓ Orphaned workspace records cleaned up\n")


def ensure_modules_visible():
	"""
	Ensure all za_local modules are visible in the sidebar navigation.
	
	In Frappe, modules appear in the sidebar if they have DocTypes assigned
	and the modules are properly configured. This function ensures all
	za_local modules are set up correctly.
	"""
	print("\nEnsuring za_local modules are visible...")
	
	# List of za_local modules from modules.txt
	za_local_modules = [
		"South Africa",
		"SA Payroll",
		"SA Tax",
		"SA VAT",
		"COIDA",
		"SA EE"
	]
	
	for module_name in za_local_modules:
		# Check if module exists
		if not frappe.db.exists("Module Def", module_name):
			print(f"  ⊙ Module '{module_name}' does not exist (will be created by Frappe)")
			continue
		
		try:
			module_doc = frappe.get_doc("Module Def", module_name)
			
			# Ensure module is properly configured
			if module_doc.app_name != "za_local":
				module_doc.app_name = "za_local"
				module_doc.save(ignore_permissions=True)
				print(f"  ✓ Updated module '{module_name}' app_name to 'za_local'")
			
			# Ensure module is not custom (app modules should have custom=0)
			if module_doc.custom != 0:
				module_doc.custom = 0
				module_doc.save(ignore_permissions=True)
				print(f"  ✓ Updated module '{module_name}' to non-custom")
			
			# Check if module has DocTypes
			doctype_count = frappe.db.count("DocType", {"module": module_name})
			if doctype_count > 0:
				print(f"  ✓ Module '{module_name}' has {doctype_count} DocType(s)")
			else:
				print(f"  ⚠ Module '{module_name}' has no DocTypes (may not appear in sidebar)")
		
		except Exception as e:
			print(f"  ! Could not check/update module '{module_name}': {e}")
	
	frappe.db.commit()
	print("  ✓ Module visibility check complete\n")


def create_company_contribution_doctype():
	"""
	Create Company Contribution DocType if it doesn't exist.
	
	This is a child table used in Salary Structure for company contributions
	like UIF employer portion, SDL, COIDA, etc.
	
	Note: Only creates if HRMS is installed, as it's used by Salary Structure.
	"""
	if not is_hrms_installed():
		print("  ⊙ Skipping Company Contribution DocType (HRMS not installed)")
		return
	
	if frappe.db.exists("DocType", "Company Contribution"):
		print("Company Contribution DocType already exists")
		return
	
	print("Creating Company Contribution DocType...")
	
	# Determine module - use Payroll if available, otherwise SA Payroll
	module_name = "Payroll"  # HRMS module
	if not frappe.db.exists("Module Def", "Payroll"):
		module_name = "SA Payroll"  # Fallback to our module
	
	doc = frappe.get_doc({
		"doctype": "DocType",
		"name": "Company Contribution",
		"module": module_name,
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
	- PAYE
	- UIF Employee Contribution
	- UIF Employer Contribution
	- SDL Contribution
	- COIDA
	"""
	components = [
		{
			"name": "PAYE",
			"salary_component_abbr": "PAYE",
			"type": "Deduction",
			"description": "Pay As You Earn - Income Tax",
			"is_tax_applicable": 0,
			"variable_based_on_taxable_salary": 1
		},
		{
			"name": "UIF Employee Contribution",
			"salary_component_abbr": "UIF_EE",
			"type": "Deduction",
			"description": "Unemployment Insurance Fund - Employee Contribution (1%)",
			"is_tax_applicable": 0,
			"formula": UIF_FORMULA,
			"amount_based_on_formula": 1
		},
		{
			"name": "UIF Employer Contribution",
			"salary_component_abbr": "UIF_ER",
			"type": "Company Contribution",
			"description": "Unemployment Insurance Fund - Employer Contribution (1%)",
			"is_tax_applicable": 0,
			"formula": UIF_FORMULA,
			"amount_based_on_formula": 1
		},
		{
			"name": "SDL Contribution",
			"salary_component_abbr": "SDL",
			"type": "Company Contribution",
			"description": "Skills Development Levy (1%)",
			"is_tax_applicable": 0,
			"formula": SDL_FORMULA,
			"amount_based_on_formula": 1
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
	
	hrms_installed = is_hrms_installed()
	hrms_only_doctypes = {
		"Salary Component",
		"Salary Slip",
		"Salary Structure",
		"Salary Structure Assignment",
		"Payroll Entry",
		"Additional Salary",
	}
	
	for doctypes, property_setters in get_property_setters().items():
		if isinstance(doctypes, str):
			doctypes = (doctypes,)

		for doctype in doctypes:
			if doctype in hrms_only_doctypes and not hrms_installed:
				print(f"  ⊙ Skipping property setters for {doctype} (HRMS not installed)")
				continue

			if not frappe.db.exists("DocType", doctype):
				print(f"  ⊙ Skipping property setters for {doctype} (DocType not found)")
				continue

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
					validate_fields_for_doctype=False,
				)
	
	print("✓ Property setters created successfully")


def apply_statutory_formulas():
	"""Ensure statutory Salary Components and Company Contribution rows carry correct formulas.
	- UIF Employee & Employer: 1% of gross pay capped at 177.12
	- SDL: 1% of gross pay
	Also enable Amount based on Formula on these components and child rows.
	"""
	print("Applying statutory formulas to salary components and company contribution rows...")

	if not frappe.db.table_exists("tabSalary Component"):
		print("  ⊙ Skipping statutory formula updates (Salary Component DocType not available)")
		return

	component_updates = {
		"UIF Employee Contribution": {
			"amount_based_on_formula": 1,
			"formula": UIF_FORMULA,
		},
		"UIF Employer Contribution": {
			"amount_based_on_formula": 1,
			"formula": UIF_FORMULA,
			"type": "Company Contribution",
		},
		"SDL Contribution": {
			"amount_based_on_formula": 1,
			"formula": SDL_FORMULA,
			"type": "Company Contribution",
		},
	}

	for canonical_name, fields in component_updates.items():
		if frappe.db.exists("Salary Component", canonical_name):
			try:
				frappe.db.set_value("Salary Component", canonical_name, fields)
			except Exception as e:
				print(f"  ! Could not update Salary Component {canonical_name}: {e}")

	# Update existing Salary Structure child rows and Salary Detail records
	_update_statutory_formulas_in_child_tables(component_updates)

	print("✓ Statutory formulas applied")


def _update_statutory_formulas_in_child_tables(component_updates: dict[str, dict]):
	if not frappe.db.table_exists("tabCompany Contribution"):
		print("  ⊙ Skipping Company Contribution child row updates (DocType not available)")
	else:
		for name, fields in component_updates.items():
			if name not in ("UIF Employer Contribution", "SDL Contribution"):
				continue
			frappe.db.sql(
				"""
				UPDATE `tabCompany Contribution`
				SET amount_based_on_formula = 1, formula = %(formula)s
				WHERE salary_component = %(name)s
				""",
				{"name": name, "formula": fields["formula"]},
			)

	if frappe.db.table_exists("tabSalary Detail"):
		for name, fields in component_updates.items():
			frappe.db.sql(
				"""
				UPDATE `tabSalary Detail`
				SET amount_based_on_formula = 1, formula = %(formula)s
				WHERE salary_component = %(name)s
				""",
				{"name": name, "formula": fields["formula"]},
			)

	frappe.db.commit()

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
		
		# Load Chart of Accounts
		if setup_doc.load_chart_of_accounts and setup_doc.company:
			print("Loading South African Chart of Accounts...")
			try:
				from za_local.accounts.setup_chart import load_sa_chart_of_accounts
				load_sa_chart_of_accounts(setup_doc.company)
				print("✓ Loaded Chart of Accounts")
			except Exception as e:
				print(f"  ! Warning: Could not load Chart of Accounts: {e}")
				print("  Note: Chart of Accounts can be loaded manually later")
				frappe.log_error(f"Chart of Accounts loading failed: {str(e)}", "ZA Local Setup")

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
	
	# Commit after loading all records from this file
	frappe.db.commit()


def insert_record(record):
	"""
	Insert a single record, skip if exists.
	Handles both regular DocTypes and Single DocTypes.
	Also handles child tables (like Holiday List with holidays).
	
	Args:
		record: Dict with doctype and field values
	"""
	doctype = record.get("doctype")
	
	# Determine the name field - different DocTypes use different name fields
	# Standard: "name"
	# Salary Component: "salary_component" 
	# Holiday List: "holiday_list_name"
	name = (record.get("name") or 
	        record.get("salary_component") or 
	        record.get("holiday_list_name"))
	
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
			# Special handling for Holiday List - check by holiday_list_name
			if doctype == "Holiday List" and name:
				exists = frappe.db.exists("Holiday List", name)
			elif name:
				exists = frappe.db.exists(doctype, name)
			else:
				# If no name field, check if we should create anyway
				exists = False
			
			if not exists:
				# Create the document
				# frappe.get_doc() automatically handles child tables when you pass them in the record dict
				# For Holiday List, the "holidays" array will be automatically converted to child table rows
				# Each item in the "holidays" array becomes a row in the Holiday child table
				doc = frappe.get_doc(record)
				doc.insert(ignore_permissions=True, ignore_mandatory=True)
				
				created_name = name or doc.name
				print(f"  ✓ Created {doctype}: {created_name}")
				
				# For Holiday List, verify holidays were saved
				if doctype == "Holiday List":
					# Reload document to get latest state from database
					doc.reload()
					holiday_count = len(doc.get("holidays", [])) if hasattr(doc, 'get') else 0
					if holiday_count > 0:
						print(f"    → Added {holiday_count} holidays to '{created_name}'")
					else:
						# If no holidays in doc, check the original record
						holiday_count_from_record = len(record.get("holidays", []))
						if holiday_count_from_record > 0:
							print(f"    ! Warning: {holiday_count_from_record} holidays in record but not saved.")
							print(f"    ! This may indicate a child table field name mismatch or HRMS not fully installed.")
						else:
							print(f"    ! Warning: No holidays found in record")
			else:
				print(f"  ⊙ Skipped {doctype}: {name} (already exists)")
		
		# Restore message log
		frappe.local.message_log = _message_log
	except Exception as e:
		# Restore message log even on error
		frappe.local.message_log = _message_log
		print(f"  ✗ Error with {doctype} {name or 'unknown'}: {e}")
		
		# For Holiday List, provide more specific error information
		if doctype == "Holiday List":
			print(f"    ! Holiday List creation failed. Check:")
			print(f"      - Is HRMS installed? (Holiday List is an HRMS DocType)")
			print(f"      - Does the record have 'holidays' child table array?")
			print(f"      - Are holiday items properly formatted with 'holiday_date' and 'description'?")
		
		import traceback
		traceback.print_exc()
