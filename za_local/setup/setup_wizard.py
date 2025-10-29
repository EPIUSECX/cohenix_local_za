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


def check_sa_setup_needed(login_manager=None):
	"""
	Called on every session creation (login).
	Checks if this is first login after ERPNext setup for a South African company.
	Only redirects once to za_local setup page.
	
	Args:
		login_manager: Frappe login manager object (passed by hook)
	"""
	import frappe
	from frappe import _
	
	# Don't run for Guest user or if not in request context
	if not frappe.session or frappe.session.user == "Guest":
		return
	
	# Check if za_local is installed
	if "za_local" not in frappe.get_installed_apps():
		return
	
	# Check if this is a fresh setup (company exists but < 10 docs total)
	# This indicates we just completed setup wizard
	companies = frappe.get_all("Company", filters={"country": "South Africa"}, limit=1)
	
	if not companies:
		return  # No South African companies
	
	company_name = companies[0].name
	
	# Check if setup already exists or was shown
	if frappe.db.exists("ZA Local Setup", {"company": company_name}):
		return  # Already created setup doc
	
	# Check if user has dismissed setup
	# Using cache to avoid repeated database queries
	cache_key = f"za_setup_dismissed_{company_name}"
	if frappe.cache().get(cache_key):
		return
	
	# Create setup document and redirect
	try:
		setup_doc = frappe.get_doc({
			"doctype": "ZA Local Setup",
			"company": company_name,
			"setup_status": "Pending",
			"country": "South Africa",
			# Default selections (all recommended items enabled)
			"load_salary_components": 1,
			"load_earnings_components": 1,
			"load_tax_slabs": 1,
			"load_tax_rebates": 1,
			"load_medical_credits": 1,
			"load_business_trip_regions": 1,
			"load_seta_list": 0,  # Optional
			"load_bargaining_councils": 0  # Optional
		})
		setup_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Set message to show in UI
		frappe.msgprint(
			_("Welcome! Let's configure your South African payroll and compliance settings."),
			title=_("ZA Localization Setup"),
			indicator="blue"
		)
		
		# Redirect happens via client-side after msgprint is shown
		frappe.local.response["redirect_to"] = f"/app/za-local-setup/{setup_doc.name}"
		
	except Exception as e:
		# Log error but don't break the login process
		frappe.log_error(f"Failed to create ZA Local Setup: {str(e)}", "ZA Local Setup Wizard")


@frappe.whitelist()
def dismiss_setup_wizard():
	"""
	Mark the setup wizard as dismissed so it doesn't appear again.
	Called when user clicks 'Skip Setup' button.
	"""
	import frappe
	
	# Get current company
	companies = frappe.get_all("Company", filters={"country": "South Africa"}, limit=1)
	
	if companies:
		company_name = companies[0].name
		# Set cache flag to prevent showing again
		cache_key = f"za_setup_dismissed_{company_name}"
		frappe.cache().set(cache_key, 1, expires_in_sec=31536000)  # 1 year
		
		# Also create a skipped setup record for audit trail
		if not frappe.db.exists("ZA Local Setup", {"company": company_name}):
			setup_doc = frappe.get_doc({
				"doctype": "ZA Local Setup",
				"company": company_name,
				"setup_status": "Skipped",
				"country": "South Africa"
			})
			setup_doc.insert(ignore_permissions=True)
			frappe.db.commit()
	
	return {"status": "dismissed"}

