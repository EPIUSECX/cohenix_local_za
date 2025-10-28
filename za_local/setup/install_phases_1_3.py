"""
Phase 1-3 Installation Functions

Additional setup functions for Phases 1-3 features.
"""

import frappe
from frappe import _


def setup_phases_1_3():
	"""
	Main setup function for Phases 1-3.
	Call this from after_install or after_migrate.
	"""
	print("\n" + "="*80)
	print("Setting up Phases 1-3 Features...")
	print("="*80 + "\n")
	
	# Phase 1: Tax & Payroll Compliance
	setup_default_travel_rates()
	
	# Phase 2: Leave Management
	setup_sa_leave_types()
	setup_public_holidays_for_current_year()
	
	# Phase 3: Employment Equity
	add_phase_1_3_custom_fields()
	
	print("\n" + "="*80)
	print("✅ Phases 1-3 Setup Complete!")
	print("="*80 + "\n")


def setup_default_travel_rates():
	"""Create default travel allowance rates"""
	from frappe.utils import today
	
	if not frappe.db.exists("Travel Allowance Rate", {"company": frappe.defaults.get_defaults().get("company")}):
		try:
			doc = frappe.get_doc({
				"doctype": "Travel Allowance Rate",
				"effective_from": today(),
				"reimbursive_rate_per_km": 4.25,  # 2024 SARS rate
				"fixed_allowance_rate": 0.80,  # 80% taxable
				"company": frappe.defaults.get_defaults().get("company")
			})
			doc.insert(ignore_permissions=True)
			print("✓ Default travel allowance rates created")
		except Exception as e:
			print(f"! Could not create travel allowance rates: {e}")


def setup_sa_leave_types():
	"""Create South African BCEA-compliant leave types"""
	from za_local.setup.leave_types import setup_sa_leave_types as create_leave_types
	
	try:
		create_leave_types()
		print("✓ SA leave types created")
	except Exception as e:
		print(f"! Could not create leave types: {e}")


def setup_public_holidays_for_current_year():
	"""Generate public holidays for current year"""
	from frappe.utils import today, getdate
	import calendar
	from datetime import datetime
	
	current_year = getdate(today()).year
	
	# Fixed public holidays
	fixed_holidays = [
		("01-01", "New Year's Day"),
		("03-21", "Human Rights Day"),
		("04-27", "Freedom Day"),
		("05-01", "Workers' Day"),
		("06-16", "Youth Day"),
		("08-09", "National Women's Day"),
		("09-24", "Heritage Day"),
		("12-16", "Day of Reconciliation"),
		("12-25", "Christmas Day"),
		("12-26", "Day of Goodwill"),
	]
	
	for date_str, name in fixed_holidays:
		month, day = map(int, date_str.split("-"))
		holiday_date = datetime(current_year, month, day).date()
		
		# Check if holiday falls on Sunday - move to Monday
		if holiday_date.weekday() == 6:  # Sunday
			holiday_date = datetime(current_year, month, day + 1).date()
			name = f"{name} (Observed)"
		
		if not frappe.db.exists("South African Public Holiday", {"holiday_date": holiday_date}):
			try:
				doc = frappe.get_doc({
					"doctype": "South African Public Holiday",
					"holiday_date": holiday_date,
					"holiday_name": name,
					"is_fixed": 1,
					"fiscal_year": f"{current_year}-{current_year+1}"
				})
				doc.insert(ignore_permissions=True)
			except Exception as e:
				print(f"! Could not create holiday {name}: {e}")
	
	# Easter-based holidays (Good Friday, Family Day)
	# TODO: Calculate Easter for current year
	
	print(f"✓ Public holidays for {current_year} created")


def add_phase_1_3_custom_fields():
	"""Add Phase 1-3 custom fields"""
	from za_local.setup.custom_fields_phases_1_3 import add_phase_1_3_fields
	
	try:
		add_phase_1_3_fields()
		print("✓ Phase 1-3 custom fields added")
	except Exception as e:
		print(f"! Could not add custom fields: {e}")


def setup_default_retirement_funds():
	"""Create default retirement fund types"""
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

