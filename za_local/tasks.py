# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Scheduled Compliance Tasks

Background jobs for monitoring SA compliance requirements:
- Tax directive expiry
- ETI eligibility changes
- Employee ID validation
- SARS rate updates
- EEA reporting reminders
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, get_datetime, getdate, add_months
from datetime import date


def all():
	"""Run on every scheduler tick (hourly)"""
	# Add any tasks that need to run hourly
	pass


def daily():
	"""Run daily compliance checks"""
	check_tax_directive_expiry()
	check_eti_eligibility_changes()


def weekly():
	"""Run weekly compliance checks"""
	validate_employee_id_numbers()


def monthly():
	"""Run monthly compliance checks"""
	check_coida_rate_updates()
	check_sars_rate_updates()


def quarterly():
	"""Run quarterly compliance reminders"""
	reminder_for_eea_reporting()


# ==================== Tax Directive Monitoring ====================

def check_tax_directive_expiry():
	"""
	Check for tax directives expiring within 30 days.
	
	Creates notifications for HR Admin to renew directives before expiry.
	"""
	# Get directives expiring in next 30 days
	thirty_days_from_now = add_days(today(), 30)
	
	expiring_directives = frappe.get_all(
		"Tax Directive",
		filters={
			"status": "Active",
			"effective_to": ["<=", thirty_days_from_now],
			"effective_to": [">=", today()]
		},
		fields=["name", "employee", "employee_name", "effective_to"]
	)
	
	if not expiring_directives:
		return
	
	# Create notification for HR Admin
	for directive in expiring_directives:
		days_until_expiry = (getdate(directive.effective_to) - getdate(today())).days
		
		# Create notification
		notification = frappe.new_doc("Notification Log")
		notification.subject = _("Tax Directive Expiring Soon: {0}").format(directive.employee_name)
		notification.email_content = _(
			"Tax Directive {0} for employee {1} ({2}) will expire in {3} days on {4}. "
			"Please renew the directive before expiry."
		).format(
			directive.name,
			directive.employee_name,
			directive.employee,
			days_until_expiry,
			directive.effective_to
		)
		notification.document_type = "Tax Directive"
		notification.document_name = directive.name
		notification.for_user = get_hr_admin_users()
		notification.insert(ignore_permissions=True)
	
	frappe.db.commit()
	print(f"✓ Tax Directive Expiry Check: {len(expiring_directives)} directive(s) expiring soon")


# ==================== ETI Eligibility Monitoring ====================

def check_eti_eligibility_changes():
	"""
	Check for ETI eligibility changes:
	1. Employees turning 30 (no longer eligible)
	2. Employees reaching 24-month employment mark
	
	Logs changes and creates notifications.
	"""
	# Check employees turning 30 today
	employees_turning_30 = frappe.db.sql("""
		SELECT name, employee_name, date_of_birth, date_of_joining
		FROM `tabEmployee`
		WHERE status = 'Active'
		AND MONTH(date_of_birth) = MONTH(CURDATE())
		AND DAY(date_of_birth) = DAY(CURDATE())
		AND TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) = 30
	""", as_dict=True)
	
	for emp in employees_turning_30:
		# Create notification
		notify_hr_admin(
			subject=f"ETI Eligibility Lost: {emp.employee_name}",
			message=f"Employee {emp.employee_name} ({emp.name}) turned 30 today and is no longer eligible for Employment Tax Incentive (ETI).",
			doctype="Employee",
			docname=emp.name
		)
	
	# Check employees reaching 24-month mark
	twenty_four_months_ago = add_months(today(), -24)
	
	employees_at_24_months = frappe.get_all(
		"Employee",
		filters={
			"status": "Active",
			"date_of_joining": twenty_four_months_ago
		},
		fields=["name", "employee_name", "date_of_joining"]
	)
	
	for emp in employees_at_24_months:
		notify_hr_admin(
			subject=f"ETI Period Ending: {emp.employee_name}",
			message=f"Employee {emp.employee_name} ({emp.name}) has reached 24 months of employment. ETI eligibility will end after this month. Second 12-month rates apply for the final month.",
			doctype="Employee",
			docname=emp.name
		)
	
	if employees_turning_30 or employees_at_24_months:
		frappe.db.commit()
		print(f"✓ ETI Eligibility Check: {len(employees_turning_30)} turning 30, {len(employees_at_24_months)} at 24 months")


# ==================== ID Number Validation ====================

def validate_employee_id_numbers():
	"""
	Validate SA ID numbers for all active employees:
	1. Check checksum validity
	2. Check for duplicates
	3. Flag invalid entries
	"""
	from za_local.utils.tax_utils import validate_south_african_id
	
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "za_id_number": ["is", "set"]},
		fields=["name", "employee_name", "za_id_number"]
	)
	
	invalid_ids = []
	duplicate_ids = {}
	
	for emp in employees:
		if not emp.za_id_number or len(emp.za_id_number) != 13:
			continue
		
		# Check for duplicates
		if emp.za_id_number in duplicate_ids:
			duplicate_ids[emp.za_id_number].append(emp)
		else:
			duplicate_ids[emp.za_id_number] = [emp]
		
		# Validate checksum
		try:
			if not validate_south_african_id(emp.za_id_number):
				invalid_ids.append(emp)
		except Exception:
			invalid_ids.append(emp)
	
	# Report invalid IDs
	if invalid_ids:
		message = "The following employees have invalid SA ID numbers:\n\n"
		for emp in invalid_ids:
			message += f"- {emp.employee_name} ({emp.name}): {emp.za_id_number}\n"
		
		notify_hr_admin(
			subject="Invalid SA ID Numbers Detected",
			message=message,
			doctype="Employee",
			docname=None
		)
	
	# Report duplicates
	actual_duplicates = {id_num: emps for id_num, emps in duplicate_ids.items() if len(emps) > 1}
	
	if actual_duplicates:
		message = "The following SA ID numbers are assigned to multiple employees:\n\n"
		for id_num, emps in actual_duplicates.items():
			message += f"ID Number {id_num}:\n"
			for emp in emps:
				message += f"  - {emp.employee_name} ({emp.name})\n"
		
		notify_hr_admin(
			subject="Duplicate SA ID Numbers Detected",
			message=message,
			doctype="Employee",
			docname=None
		)
	
	if invalid_ids or actual_duplicates:
		frappe.db.commit()
		print(f"✓ ID Validation: {len(invalid_ids)} invalid, {len(actual_duplicates)} duplicates")


# ==================== SARS Rate Updates ====================

def check_sars_rate_updates():
	"""
	Check for SARS rate updates (placeholder for future API integration).
	
	Currently creates reminder on March 1 (new tax year) to update rates.
	"""
	today_date = getdate(today())
	
	# Reminder on March 1 (new tax year)
	if today_date.month == 3 and today_date.day == 1:
		notify_hr_admin(
			subject="SARS Tax Year Update Required",
			message=f"It's the start of the new tax year ({today_date.year}-{today_date.year + 1}). Please update the following:\n\n"
			"1. Tax Rebates (Payroll Settings)\n"
			"2. ETI Slabs\n"
			"3. Medical Tax Credit Rates\n"
			"4. UIF Income Threshold\n"
			"5. Travel Allowance Rates\n\n"
			"Visit the SARS website for the latest rates.",
			doctype=None,
			docname=None
		)
		frappe.db.commit()
		print("✓ SARS Rate Update Reminder sent for new tax year")


def check_coida_rate_updates():
	"""
	Check for COIDA rate updates (placeholder for future integration).
	
	COIDA rates are updated periodically by the Compensation Fund.
	"""
	# Placeholder for future implementation
	# Could check Compensation Fund website or API
	pass


# ==================== EEA Reporting Reminders ====================

def reminder_for_eea_reporting():
	"""
	Quarterly reminders for Employment Equity reporting.
	
	EEA reports are due January 15 annually.
	"""
	today_date = getdate(today())
	
	# Reminder in December for January 15 deadline
	if today_date.month == 12 and today_date.day == 1:
		notify_hr_admin(
			subject="Employment Equity Report Due Soon",
			message="Reminder: Employment Equity (EEA) reports are due on January 15.\n\n"
			"Please prepare:\n"
			"1. EEA2 - Income Differentials Report\n"
			"2. EEA4 - Employment Equity Plan Report\n"
			"3. EEA13 - Consultation Documentation\n\n"
			"Ensure all employee demographic data is up to date.",
			doctype=None,
			docname=None
		)
		frappe.db.commit()
		print("✓ EEA Reporting Reminder sent")


# ==================== Helper Functions ====================

def get_hr_admin_users():
	"""Get list of users with HR Manager or System Manager role"""
	hr_users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["HR Manager", "System Manager"]]},
		fields=["parent"],
		distinct=True,
		pluck="parent"
	)
	return hr_users[0] if hr_users else "Administrator"


def notify_hr_admin(subject, message, doctype=None, docname=None):
	"""
	Create notification for HR Admin users.
	
	Args:
		subject: Notification subject
		message: Notification message
		doctype: Related DocType (optional)
		docname: Related document name (optional)
	"""
	notification = frappe.new_doc("Notification Log")
	notification.subject = subject
	notification.email_content = message
	
	if doctype:
		notification.document_type = doctype
	if docname:
		notification.document_name = docname
	
	notification.for_user = get_hr_admin_users()
	notification.insert(ignore_permissions=True)

