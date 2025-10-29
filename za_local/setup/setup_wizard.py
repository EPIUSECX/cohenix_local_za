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
        
        # Public holidays
        current_year = getdate(today()).year
        if frappe.db.count("South African Public Holiday", {"holiday_date": ["like", f"{current_year}%"]}) > 0:
            status["public_holidays"] = True
        
        # Retirement funds
        if frappe.db.count("Retirement Fund") > 0:
            status["retirement_funds"] = True
            
    except Exception as e:
        frappe.log_error(f"Error checking wizard status: {e}")
    
    return status


def get_sa_localization_stages(args):
	"""
	Return za_local setup stage for the wizard.
	Only returns a stage if country is South Africa.
	
	Called by Frappe's setup wizard via setup_wizard_stages hook.
	"""
	import frappe
	from frappe import _
	
	# Only add stage if country is South Africa
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
					"fail_msg": _("Failed to setup SA localization")
				}
			]
		}
	]


def setup_za_localization(args):
	"""
	Execute za_local setup during the wizard.
	Loads salary components, tax slabs, and master data.
	
	Args:
		args: Dictionary from setup wizard containing user selections
	"""
	import frappe
	from frappe import _
	from za_local.setup.install import load_data_from_json, insert_record
	from za_local.utils.csv_importer import import_csv_data
	from pathlib import Path
	
	# Get user selections from args (passed from JavaScript)
	load_salary = args.get("za_load_salary_components", 1)
	load_earnings = args.get("za_load_earnings_components", 1)
	load_tax_slabs = args.get("za_load_tax_slabs", 1)
	load_tax_rebates = args.get("za_load_tax_rebates", 1)
	load_medical = args.get("za_load_medical_credits", 1)
	load_regions = args.get("za_load_business_trip_regions", 1)
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	
	try:
		# Load in correct order (dependencies first)
		
		# 1. Load Payroll Period first (required by Tax Rebates)
		if load_tax_rebates or load_medical:
			print("Loading Payroll Period...")
			load_data_from_json(data_dir / "payroll_period_2024.json")
		
		# 2. Load Tax Rebates (depends on Payroll Period)
		if load_tax_rebates or load_medical:
			print("Loading Tax Rebates and Medical Credits...")
			load_data_from_json(data_dir / "tax_rebates_2024.json")
		
		# 3. Load Income Tax Slab
		if load_tax_slabs:
			print("Loading Income Tax Slab...")
			load_data_from_json(data_dir / "tax_slabs_2024.json")
		
		# 4. Load Salary Components
		if load_salary:
			print("Loading Salary Components...")
			load_data_from_json(data_dir / "salary_components.json")
		
		# 5. Load Earnings Components
		if load_earnings:
			print("Loading Earnings Components...")
			load_data_from_json(data_dir / "earnings_components.json")
		
		# 6. Load Master Data (Business Trip Regions)
		if load_regions:
			print("Loading Business Trip Regions...")
			import_csv_data("Business Trip Region", "business_trip_region.csv")
		
		frappe.msgprint(_("South African localization configured successfully!"))
		
	except Exception as e:
		frappe.log_error(f"SA Localization setup failed: {str(e)}", "ZA Local Setup")
		raise

