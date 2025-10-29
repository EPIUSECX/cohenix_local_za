# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Test Data Generator for za_local

Creates sample data for testing and demonstration:
- Test employees with SA compliance data
- Sample payroll data
- Business trips
- Tax directives
- Skills development records

Usage:
    bench execute za_local.utils.create_test_data.create_all_test_data
"""

import frappe
from frappe.utils import today, add_days, add_months, getdate
from datetime import date


def create_all_test_data():
	"""Create all test data"""
	print("\n" + "="*80)
	print("Creating Test Data for za_local")
	print("="*80 + "\n")
	
	company = get_or_create_test_company()
	employees = create_test_employees(company)
	create_test_business_trips(employees)
	create_test_tax_directives(employees)
	create_test_skills_development(employees)
	
	print("\n" + "="*80)
	print("✅ Test Data Created Successfully!")
	print("="*80)
	print(f"\nCompany: {company}")
	print(f"Employees: {len(employees)}")
	print("\nYou can now:")
	print("1. Process test payroll")
	print("2. Generate EMP201 submissions")
	print("3. Create business trips")
	print("4. Run compliance reports")
	print("="*80 + "\n")


def get_or_create_test_company():
	"""Get or create test company with SA details"""
	company_name = "Test Company (Pty) Ltd"
	
	if frappe.db.exists("Company", company_name):
		print(f"✓ Test company already exists: {company_name}")
		return company_name
	
	company = frappe.get_doc({
		"doctype": "Company",
		"company_name": company_name,
		"abbr": "TEST",
		"country": "South Africa",
		"default_currency": "ZAR",
		"za_paye_registration_number": "7001234567",
		"za_uif_reference_number": "U12345678",
		"za_sdl_reference_number": "L12345678",
		"za_seta": "Services SETA"
	})
	company.insert(ignore_permissions=True)
	
	print(f"✓ Created test company: {company_name}")
	return company_name


def create_test_employees(company):
	"""Create test employees with SA compliance data"""
	print("\nCreating test employees...")
	
	employees_data = [
		{
			"first_name": "Thabo",
			"last_name": "Mokwena",
			"gender": "Male",
			"date_of_birth": "1990-03-15",
			"date_of_joining": add_months(today(), -36),  # 3 years ago
			"za_id_number": "9003155009087",
			"za_employee_type": "Full-Time Permanent",
			"za_race": "African",
			"za_occupational_level": "Professionally Qualified",
			"za_nationality": "South Africa",
			"za_working_hours_per_week": 40,
			"za_has_children": 1,
			"za_number_of_dependants": 2,
			"za_highest_qualification": "Bachelor's Degree",
			"department": "Engineering",
			"designation": "Senior Developer"
		},
		{
			"first_name": "Sarah",
			"last_name": "Van Der Merwe",
			"gender": "Female",
			"date_of_birth": "1985-08-22",
			"date_of_joining": add_months(today(), -60),  # 5 years ago
			"za_id_number": "8508225009081",
			"za_employee_type": "Full-Time Permanent",
			"za_race": "White",
			"za_occupational_level": "Senior Management",
			"za_nationality": "South Africa",
			"za_working_hours_per_week": 45,
			"za_has_children": 0,
			"za_number_of_dependants": 1,
			"za_highest_qualification": "Master's Degree",
			"department": "Operations",
			"designation": "Operations Manager"
		},
		{
			"first_name": "Naledi",
			"last_name": "Naidoo",
			"gender": "Female",
			"date_of_birth": "1995-11-10",
			"date_of_joining": add_months(today(), -8),  # 8 months ago (ETI eligible)
			"za_id_number": "9511105009082",
			"za_employee_type": "Full-Time Permanent",
			"za_race": "Indian",
			"za_occupational_level": "Skilled Technical",
			"za_nationality": "South Africa",
			"za_working_hours_per_week": 40,
			"za_has_children": 0,
			"za_number_of_dependants": 0,
			"za_highest_qualification": "National Diploma",
			"department": "Finance",
			"designation": "Junior Accountant"
		},
		{
			"first_name": "Marcus",
			"last_name": "Adams",
			"gender": "Male",
			"date_of_birth": "1992-05-18",
			"date_of_joining": add_months(today(), -24),  # 2 years ago
			"za_id_number": "9205185009083",
			"za_employee_type": "Full-Time Permanent",
			"za_race": "Coloured",
			"za_occupational_level": "Professionally Qualified",
			"za_is_disabled": 1,
			"za_disability_type": "Mobility",
			"za_nationality": "South Africa",
			"za_working_hours_per_week": 40,
			"za_has_children": 1,
			"za_number_of_dependants": 3,
			"za_highest_qualification": "Honoursdegree",
			"department": "HR",
			"designation": "HR Officer"
		}
	]
	
	created_employees = []
	for emp_data in employees_data:
		employee_id = f"{emp_data['first_name'][:2].upper()}{emp_data['last_name'][:3].upper()}"
		
		if frappe.db.exists("Employee", {"employee_name": f"{emp_data['first_name']} {emp_data['last_name']}"}):
			print(f"  ✓ Employee already exists: {emp_data['first_name']} {emp_data['last_name']}")
			created_employees.append(employee_id)
			continue
		
		employee = frappe.get_doc({
			"doctype": "Employee",
			**emp_data,
			"company": company,
			"status": "Active"
		})
		employee.insert(ignore_permissions=True)
		created_employees.append(employee.name)
		
		print(f"  ✓ Created employee: {emp_data['first_name']} {emp_data['last_name']} ({employee.name})")
	
	return created_employees


def create_test_business_trips(employees):
	"""Create sample business trips"""
	if not employees:
		return
	
	print("\nCreating test business trips...")
	
	# Only create if Business Trip Settings exists
	if not frappe.db.exists("DocType", "Business Trip"):
		print("  ! Business Trip DocType not found, skipping")
		return
	
	# Create Business Trip Settings if not exists
	if not frappe.db.exists("Business Trip Settings"):
		settings = frappe.get_doc({
			"doctype": "Business Trip Settings",
			"mileage_allowance_rate": 4.25,
			"require_manager_approval": 1,
			"auto_create_expense_claim_on_submit": 1
		})
		settings.insert(ignore_permissions=True)
		print("  ✓ Created Business Trip Settings")
	
	# Create sample trip for first employee
	trip = frappe.get_doc({
		"doctype": "Business Trip",
		"employee": employees[0],
		"company": frappe.defaults.get_defaults().get("company"),
		"trip_purpose": "Client Meeting in Cape Town",
		"from_date": add_days(today(), -7),
		"to_date": add_days(today(), -5),
		"status": "Draft"
	})
	
	# Add allowances
	trip.append("allowances", {
		"date": add_days(today(), -7),
		"region": "CPT" if frappe.db.exists("Business Trip Region", "CPT") else None,
		"daily_rate": 1400,
		"incidental_rate": 100,
		"total": 1500
	})
	
	# Add journey
	trip.append("journeys", {
		"date": add_days(today(), -7),
		"from_location": "Johannesburg",
		"to_location": "Cape Town",
		"transport_mode": "Flight",
		"receipt_amount": 2500,
		"receipt_attached": 1
	})
	
	trip.insert(ignore_permissions=True)
	print(f"  ✓ Created business trip: {trip.name}")


def create_test_tax_directives(employees):
	"""Create sample tax directives"""
	if not employees or len(employees) < 2:
		return
	
	print("\nCreating test tax directives...")
	
	# Only create if Tax Directive DocType exists
	if not frappe.db.exists("DocType", "Tax Directive"):
		print("  ! Tax Directive DocType not found, skipping")
		return
	
	# Create tax directive for second employee (low PAYE rate)
	directive = frappe.get_doc({
		"doctype": "Tax Directive",
		"employee": employees[1],
		"directive_number": "TD001/2024",
		"effective_from": add_months(today(), -3),
		"effective_to": add_months(today(), 9),
		"paye_rate": 15.0,  # Lower than standard
		"reason": "Multiple Employers",
		"status": "Active"
	})
	directive.insert(ignore_permissions=True)
	print(f"  ✓ Created tax directive: {directive.name}")


def create_test_skills_development(employees):
	"""Create sample skills development records"""
	if not employees:
		return
	
	print("\nCreating test skills development records...")
	
	# Only create if Skills Development Record DocType exists
	if not frappe.db.exists("DocType", "Skills Development Record"):
		print("  ! Skills Development Record DocType not found, skipping")
		return
	
	for employee in employees[:2]:  # First 2 employees
		record = frappe.get_doc({
			"doctype": "Skills Development Record",
			"employee": employee,
			"training_date": add_months(today(), -6),
			"training_title": "Advanced Excel Training",
			"training_provider": "Skills Academy",
			"training_cost": 5000,
			"duration_hours": 40,
			"training_type": "Internal",
			"completion_status": "Completed"
		})
		record.insert(ignore_permissions=True)
	
	print(f"  ✓ Created {2} skills development records")


# Utility function to clear test data
def clear_test_data():
	"""Clear all test data (use with caution!)"""
	print("\n" + "="*80)
	print("Clearing Test Data")
	print("="*80 + "\n")
	
	company_name = "Test Company (Pty) Ltd"
	
	if frappe.db.exists("Company", company_name):
		# Delete employees
		employees = frappe.get_all("Employee", filters={"company": company_name}, pluck="name")
		for emp in employees:
			frappe.delete_doc("Employee", emp, force=1)
		print(f"✓ Deleted {len(employees)} test employees")
		
		# Delete company
		frappe.delete_doc("Company", company_name, force=1)
		print(f"✓ Deleted test company")
	
	print("\n" + "="*80)
	print("✅ Test Data Cleared")
	print("="*80 + "\n")


if __name__ == "__main__":
	create_all_test_data()

