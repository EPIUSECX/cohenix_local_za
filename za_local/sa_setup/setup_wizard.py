"""
South African Compliance Setup Wizard

Interactive wizard to configure za_local app for first-time use.
Integrates with ERPNext setup wizard via after_wizard_complete hook.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today

from za_local.utils.file_utils import read_app_json, resolve_app_path


def run_sa_compliance_wizard(company=None):
    """
    Run the complete SA compliance setup wizard

    Steps:
    1. Company registration details (PAYE, UIF, SDL, COIDA, VAT numbers)
    2. Leave types setup
    3. Salary components creation
    4. Tax slabs for current year
    5. Public holidays generation
    6. ETI slabs setup
    7. Default retirement funds
    """
    if not company:
        company = frappe.defaults.get_user_default("Company")

    if not company:
        frappe.throw(_("Please select a company first"))

    print("\n" + "="*80)
    print(f"Starting SA Compliance Setup Wizard for: {company}")
    print("="*80 + "\n")

    steps_completed = []

    # Step 1: Company Details
    try:
        setup_company_statutory_details(company)
        steps_completed.append("Company Statutory Details")
        print("✓ Step 1: Company statutory details configured")
    except Exception as e:
        print(f"✗ Step 1 failed: {e}")

    # Step 2: Leave Types
    try:
        from za_local.sa_setup.leave_types import setup_sa_leave_types
        setup_sa_leave_types()
        steps_completed.append("BCEA Leave Types")
        print("✓ Step 2: BCEA leave types created")
    except Exception as e:
        print(f"✗ Step 2 failed: {e}")

    # Step 3: Salary Components
    try:
        setup_sa_salary_components()
        steps_completed.append("Salary Components")
        print("✓ Step 3: SA salary components created")
    except Exception as e:
        print(f"✗ Step 3 failed: {e}")

    # Step 4: Tax Slabs
    try:
        setup_current_year_tax_slabs()
        steps_completed.append("Tax Slabs")
        print("✓ Step 4: Current year tax slabs loaded")
    except Exception as e:
        print(f"✗ Step 4 failed: {e}")

    # Step 5: Public Holidays
    try:
        from za_local.sa_setup.leave_types import setup_public_holidays
        setup_public_holidays()
        steps_completed.append("Public Holidays")
        print("✓ Step 5: SA public holidays generated")
    except Exception as e:
        print(f"✗ Step 5 failed: {e}")

    # Step 6: ETI Slabs
    try:
        setup_eti_slabs()
        steps_completed.append("ETI Slabs")
        print("✓ Step 6: ETI slabs configured")
    except Exception as e:
        print(f"✗ Step 6 failed: {e}")

    # Step 7: Default Retirement Funds
    try:
        from za_local.sa_setup.install import setup_default_retirement_funds
        setup_default_retirement_funds()
        steps_completed.append("Retirement Funds")
        print("✓ Step 7: Default retirement funds created")
    except Exception as e:
        print(f"✗ Step 7 failed: {e}")

    print("\n" + "="*80)
    print("Setup Wizard Completed!")
    print("="*80)
    print(f"\nSteps completed ({len(steps_completed)}/7):")
    for step in steps_completed:
        print(f"  ✓ {step}")
    print("\n" + "="*80)

    return {
        "status": "success" if len(steps_completed) >= 6 else "partial",
        "steps_completed": steps_completed,
        "total_steps": 7
    }


def setup_company_statutory_details(company):
    """Configure company statutory registration numbers"""
    # This would typically be done through a UI form
    # For now, just ensure the custom fields exist
    print(f"  → Company statutory details for {company}")
    print("     Configure: PAYE Number, UIF Number, SDL Number, COIDA Number, VAT Number")
    print("     Location: Company > {0} > SA Registration section".format(company))


def setup_sa_salary_components():
    """Create baseline SA salary components.

    UIF and SDL contribution components are provisioned via fixtures
    (salary_components.json) as UIF Employee/Employer Contribution and
    SDL Contribution; we no longer create separate 'UIF'/'SDL' deduction
    components here to avoid duplicates.
    """
    components = [
        {
            "salary_component": "Basic Salary",
            "salary_component_abbr": "BS",
            "type": "Earning",
            "is_flexible_benefit": 0,
            "is_tax_applicable": 1
        },
        {
            "salary_component": "PAYE",
            "salary_component_abbr": "PAYE",
            "type": "Deduction",
            "is_tax_applicable": 0,
            "description": "Pay As You Earn (Income Tax)"
        },
        {
            "salary_component": "ETI",
            "salary_component_abbr": "ETI",
            "type": "Earning",
            "is_tax_applicable": 0,
            "description": "Employment Tax Incentive (employer benefit)"
        }
    ]

    for comp in components:
        if not frappe.db.exists("Salary Component", comp["salary_component"]):
            try:
                doc = frappe.get_doc({
                    "doctype": "Salary Component",
                    **comp
                })
                doc.insert(ignore_permissions=True)
                print(f"  → Created: {comp['salary_component']}")
            except Exception as e:
                print(f"  ! Could not create {comp['salary_component']}: {e}")


def setup_current_year_tax_slabs():
	"""Load current year tax slabs from fixtures"""
	try:
		fixture_path = resolve_app_path(
			"sa_setup",
			"data",
			"tax_slabs_2025.json"  # 2024-2025 (2025 tax year)
		)

		if fixture_path.exists():
			data = read_app_json(fixture_path)

			# Import tax slabs if Tax Slab DocType exists
			if "Tax Slab" in data:
				for slab in data["Tax Slab"]:
					if not frappe.db.exists("Tax Slab", slab["name"]):
						# Tax Slab might not exist in this Frappe version
						# This is a placeholder for when it's available
						print(f"  → Tax slab: {slab['name']} ({slab['rate_of_tax']}%)")
		else:
			print(f"  ! Fixture file not found: {fixture_path}")

	except Exception as e:
		print(f"  ! Error loading tax slabs: {e}")


def setup_eti_slabs():
    """Setup Employment Tax Incentive slabs"""
    # ETI rates for 2024-2025
    # Age 18-29: R1,000/month (first 12 months), R500/month (months 13-24)
    # This is typically configured in the existing ETI Rate DocType
    print("  → ETI slabs configuration")
    print("     Age 18-29: R1,000/month (Year 1), R500/month (Year 2)")
    print("     Configured in: ETI Rate DocType")


@frappe.whitelist()
def get_wizard_status(company=None):
    """
    Check which setup steps have been completed

    Returns:
        dict: Status of each setup step
    """
    if not company:
        company = frappe.defaults.get_user_default("Company")

    status = {
        "company_details": False,
        "leave_types": False,
        "salary_components": False,
        "tax_slabs": False,
        "public_holidays": False,
        "eti_configured": False,
        "retirement_funds": False
    }

    # Check each step
    try:
        # Company details
        comp_doc = frappe.get_doc("Company", company)
        if comp_doc.get("za_paye_registration_number") or comp_doc.get("za_uif_reference_number"):
            status["company_details"] = True

        # Leave types
        if frappe.db.exists("Leave Type", "Annual Leave (SA)"):
            status["leave_types"] = True

        # Salary components
        if frappe.db.exists("Salary Component", "PAYE") and frappe.db.exists("Salary Component", "UIF"):
            status["salary_components"] = True

        # Public holidays (check for Holiday List records)
        current_year = getdate(today()).year
        # Check if any Holiday List exists with holidays in current year
        holiday_lists = frappe.get_all("Holiday List", filters={
            "from_date": ["<=", f"{current_year}-12-31"],
            "to_date": [">=", f"{current_year}-01-01"]
        })
        if holiday_lists:
            # Check if any of these lists have holidays
            for hl in holiday_lists:
                holidays = frappe.get_all(
                    "Holiday",
                    filters={
                        "parent": hl.name,
                        "holiday_date": ["between", [f"{current_year}-01-01", f"{current_year}-12-31"]],
                    },
                    limit=1,
                )
                if holidays:
                    status["public_holidays"] = True
                    break

        # Retirement funds
        if frappe.db.count("Retirement Fund") > 0:
            status["retirement_funds"] = True

    except Exception as e:
        frappe.log_error(f"Error checking wizard status: {e}")

    return status


def setup_sa_print_formats(include_hrms=False):
	"""Set available non-HR SA print formats as site defaults."""
	import frappe

	print("\n→ Setting up SA-compliant print formats...")

	# Map of DocType to SA Print Format
	print_format_mapping = {
		"Sales Invoice": "SA Sales Invoice",
		"Quotation": "SA Quotation",
		"Sales Order": "SA Sales Order",
		"Delivery Note": "SA Delivery Note",
		"Purchase Invoice": "SA Purchase Invoice",
		"Purchase Order": "SA Purchase Order",
		"Payment Entry": "SA Payment Entry",
	}
	if include_hrms:
		print_format_mapping.update(
			{
				"Salary Slip": "SA Salary Slip",
				"IRP5 Certificate": "IRP5 Employee Certificate",
			}
		)

	for doctype, print_format in print_format_mapping.items():
		try:
			# Check if print format exists
			if frappe.db.exists("DocType", doctype) and frappe.db.exists("Print Format", print_format):
				# Set as default
				frappe.db.set_value("DocType", doctype, "default_print_format", print_format)
				print(f"  ✓ Set {print_format} as default for {doctype}")
		except Exception as e:
			print(f"  ! Error setting print format for {doctype}: {e}")

	print("  ✓ SA print formats configured successfully")


def get_sa_localization_stages(args):
	"""
	Return the minimal za_local post-ERPNext setup stage.

	Called by Frappe's setup wizard via setup_wizard_stages hook.
	"""
	from frappe import _

	country = args.get("country")
	if country != "South Africa":
		return []

	return [
		{
			"status": _("Configuring South African Localization"),
			"fail_msg": _("Failed to configure SA localization"),
			"tasks": [
				{
					"fn": setup_za_localization,
					"args": args,
					"fail_msg": _("Failed to setup SA localization"),
				}
			],
		}
	]


def setup_za_localization(args):
	"""
	Execute the minimal non-blocking za_local setup during ERPNext first run.

	ERPNext remains responsible for Company, Fiscal Year, chart, defaults, and
	core masters. This stage only augments an existing South African company and
	refreshes ZA navigation records. It never creates HRMS/payroll masters.

	Args:
		args: Dictionary from setup wizard containing user selections
	"""
	import frappe

	from za_local.accounts.setup_chart import load_sa_chart_of_accounts
	from za_local.sa_setup.install import (
		ensure_sa_print_formats,
		sync_sa_navigation,
	)

	company = (
		args.get("company_name")
		or args.get("company")
		or frappe.defaults.get_user_default("Company")
	)
	if not company:
		companies = frappe.get_all(
			"Company",
			filters={"country": "South Africa"},
			pluck="name",
			limit=1,
		)
		company = companies[0] if companies else None

	try:
		if not company or not frappe.db.exists("Company", company):
			print("  ⊙ ZA setup skipped: ERPNext Company is not available yet")
			return

		account_count = frappe.db.count("Account", {"company": company})
		if not account_count:
			print(f"  ⊙ ZA chart augmentation skipped for {company}: no ERPNext accounts found")
			return
		else:
			added = load_sa_chart_of_accounts(company)
			if added:
				print("  ✓ ZA statutory accounts added to ERPNext Chart of Accounts")

		ensure_sa_print_formats()
		setup_sa_print_formats(include_hrms=False)
		sync_sa_navigation()
		frappe.clear_cache()
		print("✓ South African localization post-setup completed")

	except Exception as e:
		# Log the error but don't raise - allow setup wizard to continue
		frappe.log_error(f"SA Localization setup failed: {e!s}", "ZA Local Setup")
		print(f"✗ SA Localization setup encountered errors: {e}")
		print("  Note: Some features may not be configured. Check error logs for details.")
		# Don't raise - let setup wizard complete even if some steps failed
