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
from za_local.setup.monkey_patches import setup_all_monkey_patches
from za_local.utils.hrms_detection import is_hrms_installed


UIF_FORMULA = "(gross_pay * 0.01) if (gross_pay * 0.01) <= 177.12 else 177.12"
SDL_FORMULA = "gross_pay * 0.01"

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
	
	Sets up:
	- Custom fields for South African compliance (via fixtures, with programmatic fallback)
	- Property setters for default values
	- Default data (ETI slabs, tax rebates, etc.)
	- Master data from CSV files
	- DocType Links for bidirectional navigation
	- SA Payroll workspace
	
	Note: All setup tasks are handled here, not in patches.txt.
	Patches should only be used for one-time data migrations, not setup tasks.
	"""
	cleanup_invalid_doctype_links()
	# Custom fields are deployed via fixtures (fixtures/custom_field.json)
	# Fixtures are automatically imported by Frappe during installation
	setup_custom_fields()  # Only handles cleanup of old fields
	make_property_setters()
	setup_all_monkey_patches()
	setup_default_data()
	apply_statutory_formulas()
	import_master_data()
	insert_custom_records()
	import_workspace()
	refresh_desktop_icons()
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
	
	Ensures all setup is up to date after migrations:
	- Custom fields (via fixtures, with programmatic fallback)
	- Property setters
	- Workspace and desktop icons
	
	Note: This ensures the app remains properly configured after Frappe/ERPNext updates.
	"""
	cleanup_invalid_doctype_links()
	# Custom fields are deployed via fixtures (fixtures/custom_field.json)
	# Fixtures are automatically imported by Frappe during migration
	setup_custom_fields()  # Only handles cleanup of old fields
	make_property_setters()
	setup_all_monkey_patches()
	apply_statutory_formulas()
	import_workspace()
	refresh_desktop_icons()
	
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


def import_workspace(enable_payroll: bool | None = None):
	"""
	Import South Africa workspaces for Tax & Compliance and Payroll Localization.
	
	- Tax & Compliance workspace is always imported (no HRMS dependency)
	- Payroll Localization workspace is imported only when HRMS is available or explicitly enabled
	"""
	import json
	from pathlib import Path
	from za_local.utils.hrms_detection import is_hrms_installed

	print("Importing South Africa workspaces...")

	hrms_installed = is_hrms_installed()
	if enable_payroll is None:
		should_include_payroll = hrms_installed
	else:
		should_include_payroll = bool(enable_payroll) and hrms_installed

	# Create or update Module Def with proper configuration for Frappe v16
	# Note: This is an app module, not a custom module, so custom = 0
	module_exists = frappe.db.exists("Module Def", "South Africa")
	try:
		if module_exists:
			module_doc = frappe.get_doc("Module Def", "South Africa")
			# Update existing module to ensure proper configuration
			module_doc.app_name = "za_local"
			module_doc.custom = 0  # App module, not custom
			module_doc.save(ignore_permissions=True)
			frappe.db.commit()
			print("  ✓ Updated Module Def 'South Africa'")
		else:
			# Create new module with proper configuration
			module_doc = frappe.get_doc({
				"doctype": "Module Def",
				"module_name": "South Africa",
				"app_name": "za_local",
				"custom": 0,  # App module, not custom
			})
			module_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			print("  ✓ Created Module Def 'South Africa'")
	except Exception as e:
		print(f"  ! Could not create/update Module Def 'South Africa': {e}")
		import traceback
		traceback.print_exc()

	workspace_definitions = [
		{
			"name": "South Africa Localization",
			"path": Path(frappe.get_app_path("za_local", "south_africa", "workspace", "south_africa_localization", "south_africa_localization.json")),
			"requires_hrms": False,
			"sequence": 0,  # Main landing workspace - appears first
		},
		{
			"name": "Tax & Compliance",
			"path": Path(frappe.get_app_path("za_local", "south_africa", "workspace", "tax_&_compliance", "tax_&_compliance.json")),
			"requires_hrms": False,
			"sequence": 1,  # Second workspace in module
		},
		{
			"name": "Payroll",
			"path": Path(frappe.get_app_path("za_local", "south_africa", "workspace", "payroll", "payroll.json")),
			"requires_hrms": True,
			"sequence": 2,  # Third workspace in module
		},
	]

	# Determine which workspaces should exist for the current environment
	desired_workspace_names = {
		wd["name"]
		for wd in workspace_definitions
		if not wd.get("requires_hrms") or should_include_payroll
	}

	# Remove any other South Africa workspaces so navigation stays clean
	existing_workspaces = frappe.get_all(
		"Workspace",
		filters={"module": "South Africa"},
		fields=["name"],
	)
	for ws in existing_workspaces:
		if ws.name not in desired_workspace_names:
			try:
				frappe.delete_doc("Workspace", ws.name, force=True, ignore_permissions=True)
				print(f"  ⊙ Removed workspace '{ws.name}' (not part of South Africa navigation)")
			except Exception as delete_error:
				print(f"  ! Could not delete workspace '{ws.name}': {delete_error}")

	for workspace_def in workspace_definitions:
		workspace_path = workspace_def["path"]
		requires_hrms = workspace_def.get("requires_hrms", False)

		if requires_hrms:
			if not hrms_installed:
				print(f"  ⊙ Skipping workspace {workspace_path.name} (HRMS not installed)")
				continue
			if not should_include_payroll:
				print(f"  ⊙ Skipping workspace {workspace_path.name} (Payroll localization disabled)")
				continue

		if not workspace_path.exists():
			print(f"  ! Workspace file not found: {workspace_path}")
			continue

		try:
			with open(workspace_path, "r") as f:
				workspace_data = json.load(f)

			workspace_name = workspace_def["name"]
			workspace_data["name"] = workspace_name
			workspace_data["label"] = workspace_name
			workspace_data["title"] = workspace_name
			workspace_data["module"] = "South Africa"
			workspace_data["app"] = "za_local"
			# Set sequence_id for proper ordering within the module
			# Always use sequence from workspace_def to ensure consistent ordering
			workspace_data["sequence_id"] = float(workspace_def.get("sequence", 1))

			workspace_exists = frappe.db.exists("Workspace", workspace_name) is not None

			# Filter links for existing DocTypes/Reports and skip entries that rely on missing doctypes
			filtered_links = []
			for link in workspace_data.get("links", []):
				if link.get("type") == "Link":
					link_to = link.get("link_to")
					link_type = link.get("link_type", "DocType")

					if link_type == "DocType":
						if frappe.db.exists("DocType", link_to):
							filtered_links.append(link)
						else:
							print(f"  ⊙ Skipping link to non-existent DocType: {link_to}")
					elif link_type == "Report":
						if frappe.db.exists("Report", link_to):
							filtered_links.append(link)
						else:
							print(f"  ⊙ Skipping link to non-existent Report: {link_to}")
					else:
						filtered_links.append(link)
				else:
					filtered_links.append(link)

			workspace_data["links"] = filtered_links

			if not workspace_exists:
				doc = frappe.get_doc(workspace_data)
				doc.flags.ignore_links = True
				doc.flags.ignore_validate = True  # Prevent validation issues during import
				doc.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"  ✓ Imported workspace: {workspace_name}")
			else:
				print(f"  ⊙ Workspace '{workspace_name}' exists, updating with latest content")
				doc = frappe.get_doc("Workspace", workspace_name)
				fields_to_update = [
					"label",
					"public",
					"is_hidden",  # Ensure workspace is visible
					"icon",
					"module",  # CRITICAL: Ensure module is set to "South Africa"
					"app",
					"title",
					"content",
					"links",
					"charts",
					"custom_blocks",
					"quick_lists",
					"shortcuts",
					"number_cards",
					"sequence_id",  # Ensure proper ordering
				]
				for field in fields_to_update:
					if field in workspace_data:
						doc.set(field, workspace_data[field])
				# Force module assignment and visibility to ensure it's under "South Africa" and visible
				doc.module = "South Africa"
				doc.app = "za_local"
				doc.public = 1  # Ensure workspace is public
				doc.is_hidden = 0  # Ensure workspace is visible
				doc.flags.ignore_links = True
				doc.flags.ignore_validate = True  # Prevent validation issues during update
				# Prevent export to files during save (workspaces are managed by app)
				doc.flags.do_not_export = True
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				print(f"  ✓ Updated workspace: {workspace_name} (module: {doc.module})")
		except Exception as e:
			print(f"  ! Error importing workspace from {workspace_path}: {e}")
			import traceback
			traceback.print_exc()
	
	# Verify all workspaces are correctly assigned to "South Africa" module
	print("\nVerifying workspace module assignments...")
	all_workspaces = frappe.get_all(
		"Workspace",
		filters={"app": "za_local"},
		fields=["name", "module", "sequence_id"]
	)
	for ws in all_workspaces:
		if ws.module != "South Africa":
			print(f"  ⚠ Warning: Workspace '{ws.name}' has module '{ws.module}' instead of 'South Africa'")
			try:
				doc = frappe.get_doc("Workspace", ws.name)
				doc.module = "South Africa"
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				print(f"  ✓ Fixed: Updated '{ws.name}' to module 'South Africa'")
			except Exception as fix_error:
				print(f"  ! Could not fix workspace '{ws.name}': {fix_error}")
		else:
			print(f"  ✓ Workspace '{ws.name}' correctly assigned to 'South Africa' module")
	
	# Create/refresh Desktop Icons so workspaces appear on Desk
	refresh_desktop_icons()


def refresh_desktop_icons():
	"""
	Create/refresh Desktop Icons for South Africa workspaces so they appear on Desk.
	
	In Frappe v16, Desktop Icons require Workspace Sidebars to be created first.
	We ensure both are created immediately after workspace import.
	"""
	try:
		from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import (
			create_workspace_sidebar_for_workspaces
		)
		from frappe.desk.doctype.desktop_icon.desktop_icon import (
			create_desktop_icons_from_workspace,
			clear_desktop_icons_cache
		)
		print("\nCreating Workspace Sidebars and Desktop Icons...")
		# First create Workspace Sidebars (required for Desktop Icons)
		create_workspace_sidebar_for_workspaces()
		frappe.db.commit()
		
		# Ensure all za_local Workspace Sidebars have correct module assignment
		# This ensures the sidebar shows "South Africa" instead of "Frappe HR" or other modules
		workspaces = frappe.get_all(
			"Workspace",
			filters={"app": "za_local", "public": 1},
			fields=["name", "module"]
		)
		
		# Special handling for "South Africa Localization" workspace sidebar
		# Add links to child workspaces (Payroll and Tax & Compliance) so they appear in the sidebar
		sa_localization_sidebar_name = frappe.db.exists("Workspace Sidebar", "South Africa Localization")
		if sa_localization_sidebar_name:
			try:
				sa_sidebar = frappe.get_doc("Workspace Sidebar", sa_localization_sidebar_name)
				# Get all za_local workspaces except the main one
				child_workspaces = [w for w in workspaces if w.name != "South Africa Localization"]
				
				# Check if workspace links already exist
				existing_workspace_links = [item.link_to for item in (sa_sidebar.items or []) if item.link_type == "Workspace"]
				
				# Add workspace links for Payroll and Tax & Compliance if they don't exist
				for child_ws in child_workspaces:
					if child_ws.name not in existing_workspace_links:
						# Get the workspace icon for the sidebar item
						child_ws_doc = frappe.get_doc("Workspace", child_ws.name)
						sa_sidebar.append("items", {
							"label": child_ws.name,
							"link_to": child_ws.name,
							"link_type": "Workspace",
							"type": "Link",
							"icon": child_ws_doc.icon or "file-text",
							"indent": 0,
							"child": 0,
							"collapsible": 1,
							"keep_closed": 0,
							"show_arrow": 0,
						})
						print(f"  ✓ Added workspace link '{child_ws.name}' to South Africa Localization sidebar")
				
				if sa_sidebar.has_value_changed("items"):
					sa_sidebar.save(ignore_permissions=True)
					frappe.db.commit()
			except Exception as e:
				print(f"  ⊙ Could not update South Africa Localization sidebar with workspace links: {e}")
		for w in workspaces:
			sidebar_name = frappe.db.exists("Workspace Sidebar", w.name)
			if sidebar_name:
				try:
					sidebar_doc = frappe.get_doc("Workspace Sidebar", sidebar_name)
					workspace_doc = frappe.get_doc("Workspace", w.name)
					# Ensure the sidebar uses the workspace's module
					if sidebar_doc.module != w.module:
						sidebar_doc.module = w.module
						sidebar_doc.app = "za_local"
					# Update header icon to match workspace icon (for sidebar display)
					if sidebar_doc.header_icon != workspace_doc.icon:
						sidebar_doc.header_icon = workspace_doc.icon
					
					# Note: Payroll workspace sidebar structure is now managed via fixtures
					# (fixtures/workspace_sidebar.json) following Frappe best practices.
					# Only ensure basic configuration (module, app, icon) is correct.
					# Sidebar items are imported from fixtures during installation/migration.
					if w.name == "Payroll":
						# Ensure Payroll sidebar exists and has correct configuration
						# Items are managed via fixtures, so we don't rebuild them here
						print(f"  ✓ Payroll Workspace Sidebar configured (items managed via fixtures)")
					else:
						# For other workspaces, use default behavior - populate if empty
						if not sidebar_doc.items or len(sidebar_doc.items) == 0:
							workspace_links = workspace_doc.get("links", [])
							if workspace_links:
								# First, add a "Home" link pointing to the workspace itself
								sidebar_doc.append("items", {
									"label": "Home",
									"link_to": w.name,
									"link_type": "Workspace",
									"type": "Link",
									"icon": "home",
									"indent": 0,
									"child": 0,
									"collapsible": 1,
									"keep_closed": 0,
									"show_arrow": 0,
								})
								
								# Convert workspace links to sidebar items, preserving Card Break structure
								for link in workspace_links:
									if link.get("type") == "Link" and link.get("link_to"):
										# Map icon based on link type or use default
										icon = link.get("icon", "")
										if not icon:
											if link.get("link_type") == "DocType":
												icon = "file-text"
											elif link.get("link_type") == "Report":
												icon = "report"
										
										sidebar_doc.append("items", {
											"label": link.get("label", link.get("link_to")),
											"link_to": link.get("link_to"),
											"link_type": link.get("link_type", "DocType"),
											"type": "Link",
											"icon": icon,
											"indent": 0,
											"child": 0,
											"collapsible": 1,
											"keep_closed": 0,
											"show_arrow": 0,
										})
									elif link.get("type") == "Card Break":
										# Card breaks become section breaks in sidebar for grouping
										sidebar_doc.append("items", {
											"label": link.get("label", ""),
											"link_type": "DocType",
											"type": "Section Break",
											"icon": link.get("icon", ""),
											"indent": 0,
											"child": 0,
											"collapsible": 1,
											"keep_closed": 0,
											"show_arrow": 0,
										})
								print(f"  ✓ Populated Workspace Sidebar '{w.name}' with {len(sidebar_doc.items)} items from workspace links")
					
					# Ensure sidebar is saved and will be used for navigation
					sidebar_doc.save(ignore_permissions=True)
					frappe.db.commit()
					print(f"  ✓ Updated Workspace Sidebar '{w.name}' (module: {w.module}, icon: {workspace_doc.icon})")
				except Exception as e:
					print(f"  ⊙ Could not update Workspace Sidebar '{w.name}': {e}")
		frappe.db.commit()
		# Then create Desktop Icons from all public workspaces
		create_desktop_icons_from_workspace()
		frappe.db.commit()
		
		# Configure Desktop Icons correctly:
		# 1. Hide "South Africa Localization" workspace icon (it's the main landing page, not a nested item)
		# 2. Ensure only "Payroll" and "Tax & Compliance" appear as nested items
		# 3. Link the "South Africa" app icon to the "South Africa Localization" workspace
		workspaces = frappe.get_all(
			"Workspace",
			filters={"app": "za_local", "public": 1},
			fields=["name"]
		)
		
		# Ensure the main "South Africa" app icon always points to this app
		# and uses the SA map image, even on existing sites with older data.
		app_title = frappe.get_hooks("app_title", app_name="za_local")[0]
		app_logo = frappe.get_hooks("app_logo_url", app_name="za_local")[0]
		app_icon_name = frappe.db.exists("Desktop Icon", {"label": app_title, "icon_type": "App"})
		if app_icon_name:
			app_icon_doc = frappe.get_doc("Desktop Icon", app_icon_name)
		else:
			# Create the app icon if it does not exist (defensive for older sites)
			app_icon_doc = frappe.get_doc({
				"doctype": "Desktop Icon",
				"label": app_title,
				"icon_type": "App",
				"link": "/app",
				"link_type": "External",
				"standard": 1,
			})
		
		# Always keep the app icon wired to za_local and the SA map image
		app_icon_doc.app = "za_local"
		if app_logo and app_icon_doc.logo_url != app_logo:
			app_icon_doc.logo_url = app_logo
		app_icon_doc.save(ignore_permissions=True)
		frappe.db.commit()
		app_icon_name = app_icon_doc.name
		
		for w in workspaces:
			di = frappe.db.exists("Desktop Icon", {"label": w.name, "icon_type": "Link"})
			try:
				if di:
					icon_doc = frappe.get_doc("Desktop Icon", di)
				else:
					# Explicitly create missing Desktop Icons for known ZA workspaces (defensive for v16 behaviour)
					icon_doc = frappe.get_doc({
						"doctype": "Desktop Icon",
						"label": w.name,
						"icon_type": "Link",
						"link_to": w.name,
						"link_type": "Workspace Sidebar",
						"standard": 1,
					})
				workspace_doc = frappe.get_doc("Workspace", w.name)
				icon_doc.app = "za_local"

				# Ensure ZA workspaces always open their Workspace Sidebar (not legacy SA VAT module etc.)
				# This is idempotent and will fix any existing Desktop Icons with wrong link_type/link_to.
				if w.name in ("Payroll", "Tax & Compliance", "South Africa Localization"):
					icon_doc.icon_type = "Link"
					icon_doc.link_type = "Workspace Sidebar"
					icon_doc.link_to = w.name

				# Update icon to match workspace icon (for desktop display)
				if workspace_doc.icon and icon_doc.icon != workspace_doc.icon:
					icon_doc.icon = workspace_doc.icon

				# Set logo_url for desktop icons to display images instead of letters
				# Payroll uses salary_payout.svg, Tax & Compliance uses tax-benefits.svg
				if w.name == "Payroll" and not icon_doc.logo_url:
					icon_doc.logo_url = "/assets/hrms/icons/desktop_icons/salary_payout.svg"
				elif w.name == "Tax & Compliance" and not icon_doc.logo_url:
					icon_doc.logo_url = "/assets/hrms/icons/desktop_icons/tax-benefits.svg"

				# Hide "South Africa Localization" - it's the main workspace, not a nested item
				if w.name == "South Africa Localization":
					icon_doc.hidden = 1
					icon_doc.parent_icon = None
				else:
					# Ensure Payroll and Tax & Compliance are visible and nested under app icon
					icon_doc.hidden = 0
					if app_icon_name:
						icon_doc.parent_icon = app_icon_name

				icon_doc.save(ignore_permissions=True)
				print(f"  ✓ Updated Desktop Icon '{w.name}' (icon: {workspace_doc.icon})")
			except Exception as e:
				print(f"  ⊙ Could not update Desktop Icon for '{w.name}': {e}")
		
		
		# Clear cache so icons appear immediately
		clear_desktop_icons_cache()
		frappe.db.commit()
		print("  ✓ Workspace Sidebars and Desktop Icons created/updated")
	except Exception as e:
		print(f"  ⊙ Could not create Desktop Icons: {e}")
		import traceback
		traceback.print_exc()
		# Don't fail installation - try to clear cache anyway
		try:
			from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache
			clear_desktop_icons_cache()
		except:
			pass


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
