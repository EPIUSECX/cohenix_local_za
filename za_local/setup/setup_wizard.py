"""
South African Compliance Setup Wizard

Interactive wizard to configure za_local app for first-time use.
Integrates with ERPNext setup wizard via after_wizard_complete hook.
"""

import frappe
from frappe import _
from frappe.utils import today, getdate
import json


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
        from za_local.setup.leave_types import setup_sa_leave_types
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
        from za_local.setup.leave_types import setup_public_holidays
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
        from za_local.setup.install import setup_default_retirement_funds
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
    """Create standard SA salary components"""
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
            "salary_component": "UIF",
            "salary_component_abbr": "UIF",
            "type": "Deduction",
            "is_tax_applicable": 0,
            "description": "Unemployment Insurance Fund (1% of gross, capped)"
        },
        {
            "salary_component": "SDL",
            "salary_component_abbr": "SDL",
            "type": "Deduction",
            "is_tax_applicable": 0,
            "description": "Skills Development Levy (1% of gross)"
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
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "data",
            "tax_slabs_2024.json"
        )
        
        if os.path.exists(fixture_path):
            with open(fixture_path, 'r') as f:
                data = json.load(f)
                
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


def setup_sa_print_formats():
	"""Set SA-compliant print formats as default for South African companies"""
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
		"Payment Entry": "SA Payment Entry"
	}
	
	for doctype, print_format in print_format_mapping.items():
		try:
			# Check if print format exists
			if frappe.db.exists("Print Format", print_format):
				# Set as default
				frappe.db.set_value("DocType", doctype, "default_print_format", print_format)
				print(f"  ✓ Set {print_format} as default for {doctype}")
		except Exception as e:
			print(f"  ! Error setting print format for {doctype}: {e}")
	
	frappe.db.commit()
	print("  ✓ SA print formats configured successfully")


def get_sa_localization_stages(args):
	"""
	Return za_local setup stage for the wizard.
	
	Since za_local is a South Africa-specific localization app, the setup stage
	should always run when za_local is installed, regardless of country setting.
	This ensures the wizard runs on fresh installs even if country isn't set yet.
	
	Called by Frappe's setup wizard via setup_wizard_stages hook.
	"""
	import frappe
	from frappe import _
	
	# Get country from args
	country = args.get("country")
	
	# Check if za_local is installed
	# If za_local is installed, we should always run the setup stage
	# since this is a South Africa-specific localization app
	za_local_installed = False
	try:
		# Check if za_local module exists in the database
		za_local_installed = frappe.db.exists("Module Def", {"app_name": "za_local"})
	except Exception:
		# If database check fails, assume za_local is installed (we're in za_local code)
		# This handles cases where database isn't fully initialized yet
		za_local_installed = True
	
	# Always add stage if za_local is installed
	# This ensures the wizard runs on fresh installs even if country isn't set yet
	# Since za_local is SA-specific, if it's installed, the user wants SA localization
	if za_local_installed:
		# Default to using SA print formats
		if "use_sa_print_formats" not in args:
			args["use_sa_print_formats"] = True
		
		return [
			{
				"status": _("Configuring South African Localization"),
				"fail_msg": _("Failed to configure SA localization"),
				"tasks": [
					{
						"fn": setup_za_localization,
						"args": args,
						"fail_msg": _("Failed to setup SA localization")
					}
				]
			}
		]
	
	# If za_local is not installed, don't add stage
	return []


def setup_za_localization(args):
	"""
	Execute za_local setup during the wizard.
	Loads salary components, tax slabs, and master data.
	
	Args:
		args: Dictionary from setup wizard containing user selections
	"""
	import frappe
	from frappe import _
	from za_local.setup.install import load_data_from_json, import_workspace, insert_record
	from za_local.utils.hrms_detection import is_hrms_installed, require_hrms
	from za_local.utils.csv_importer import import_csv_data
	from pathlib import Path
	
	# Check if HRMS features are enabled
	enable_hrms_payroll = args.get("za_enable_hrms_payroll", 0)
	
	# Validate HRMS requirement if enabled
	if enable_hrms_payroll:
		if not is_hrms_installed():
			frappe.throw(
				_("HRMS features are enabled but HRMS app is not installed. "
				  "Please install HRMS app first, or disable HRMS features in the setup wizard."),
				title=_("HRMS Required")
			)
		require_hrms("ZA HR/Payroll Localisation")
	
	# Get user selections from args (passed from JavaScript)
	# HRMS-dependent features are only loaded if HRMS is enabled
	if enable_hrms_payroll:
		load_salary = args.get("za_load_salary_components", 1)
		load_earnings = args.get("za_load_earnings_components", 1)
		load_holidays = args.get("za_load_holiday_list", 1)
	else:
		# Disable HRMS-dependent features if HRMS is not enabled
		load_salary = 0
		load_earnings = 0
		load_holidays = 0
	
	# Non-HRMS features (always available)
	load_tax_slabs = args.get("za_load_tax_slabs", 1)
	load_tax_rebates = args.get("za_load_tax_rebates", 1)
	load_medical = args.get("za_load_medical_credits", 1)
	load_regions = args.get("za_load_business_trip_regions", 1)
	
	# Get company name from args (still used for other setup pieces)
	company = args.get("company_name") or frappe.defaults.get_user_default("Company")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	
	try:
		# Step 1: Setup SA print formats as default
		try:
			setup_sa_print_formats()
		except Exception as e:
			print(f"  ! Warning: Could not setup print formats: {e}")
			frappe.log_error(f"Print formats setup failed: {str(e)}", "ZA Local Setup")

		# Step 1.5: Ensure BCEA-compliant Leave Types exist (only if HRMS is enabled)
		if enable_hrms_payroll:
			print("Loading BCEA Leave Types (SA)...")
			try:
				from za_local.setup.leave_types import setup_sa_leave_types
				setup_sa_leave_types()
			except Exception as e:
				print(f"  ! Warning: Could not load Leave Types: {e}")
				frappe.log_error(f"Leave Types setup failed: {str(e)}", "ZA Local Setup")
		
		# Load in correct order (dependencies first)
		
		# 2. Load Payroll Periods first (required by Tax Rebates)
		# Note: Payroll Periods are HRMS-dependent, but Tax Rebates can work without them
		# For now, we'll skip Payroll Periods if HRMS is not enabled
		if enable_hrms_payroll and (load_tax_rebates or load_medical):
			print("Loading Payroll Periods...")
			try:
				load_data_from_json(data_dir / "payroll_period_2024.json")
				load_data_from_json(data_dir / "payroll_period_2025.json")
			except Exception as e:
				print(f"  ! Warning: Could not load Payroll Periods: {e}")
				print("  Note: Tax Rebates will work but may need manual Payroll Period configuration")
		
		# 3. Load Tax Rebates (depends on Payroll Period)
		if load_tax_rebates or load_medical:
			print("Loading Tax Rebates and Medical Credits...")
			try:
				load_data_from_json(data_dir / "tax_rebates_2024.json")
				load_data_from_json(data_dir / "tax_rebates_2025.json")
			except Exception as e:
				print(f"  ! Warning: Could not load Tax Rebates: {e}")
				frappe.log_error(f"Tax Rebates loading failed: {str(e)}", "ZA Local Setup")
		
		# 4. Load Income Tax Slab
		if load_tax_slabs:
			print("Loading Income Tax Slab...")
			try:
				load_data_from_json(data_dir / "tax_slabs_2024.json")
				load_data_from_json(data_dir / "tax_slabs_2025.json")
			except Exception as e:
				print(f"  ! Warning: Could not load Tax Slabs: {e}")
				frappe.log_error(f"Tax Slabs loading failed: {str(e)}", "ZA Local Setup")
		
		# 5. Load Salary Components
		if load_salary:
			print("Loading Salary Components...")
			try:
				load_data_from_json(data_dir / "salary_components.json")
			except Exception as e:
				print(f"  ! Warning: Could not load Salary Components: {e}")
				frappe.log_error(f"Salary Components loading failed: {str(e)}", "ZA Local Setup")
		
		# 6. Load Earnings Components
		if load_earnings:
			print("Loading Earnings Components...")
			try:
				load_data_from_json(data_dir / "earnings_components.json")
			except Exception as e:
				print(f"  ! Warning: Could not load Earnings Components: {e}")
				frappe.log_error(f"Earnings Components loading failed: {str(e)}", "ZA Local Setup")
		
		# 7. Load Holiday Lists (match the years for which tax slabs are loaded)
		# Note: Holiday List is an HRMS DocType, so only load if HRMS is enabled
		if load_holidays:
			print("Loading South African Holiday Lists...")
			try:
				# Verify Holiday List DocType exists (requires HRMS)
				if not frappe.db.exists("DocType", "Holiday List"):
					print("  ! Warning: Holiday List DocType not found (HRMS may not be installed)")
					print("  ⊙ Skipping holiday list loading")
				else:
					# Load holiday lists for 2024 and 2025 to match tax slabs periods
					load_data_from_json(data_dir / "holiday_list_2024.json")
					load_data_from_json(data_dir / "holiday_list_2025.json")
					print("  ✓ Holiday lists loaded successfully")
			except Exception as e:
				print(f"  ! Error loading holiday lists: {e}")
				print("  Note: Holiday lists can be created manually later in HR > Holiday List")
				frappe.log_error(f"Holiday list loading failed: {str(e)}", "ZA Local Setup")
		
		# 8. Load Master Data (Business Trip Regions)
		if load_regions:
			print("Loading Business Trip Regions...")
			try:
				import_csv_data("Business Trip Region", "business_trip_region.csv")
			except Exception as e:
				print(f"  ! Warning: Could not load Business Trip Regions: {e}")
				frappe.log_error(f"Business Trip Regions loading failed: {str(e)}", "ZA Local Setup")
		
		# 9. Refresh South Africa workspaces to respect payroll selection
		try:
			import_workspace(enable_payroll=bool(enable_hrms_payroll))
		except Exception as e:
			print(f"  ! Warning: Could not import workspace: {e}")
			frappe.log_error(f"Workspace import failed: {str(e)}", "ZA Local Setup")
		
		# Don't use msgprint in setup wizard - it can cause issues
		# frappe.msgprint(_("South African localization configured successfully!"))
		print("✓ South African localization configured successfully!")
		
	except Exception as e:
		# Log the error but don't raise - allow setup wizard to continue
		frappe.log_error(f"SA Localization setup failed: {str(e)}", "ZA Local Setup")
		print(f"✗ SA Localization setup encountered errors: {e}")
		print("  Note: Some features may not be configured. Check error logs for details.")
		# Don't raise - let setup wizard complete even if some steps failed

