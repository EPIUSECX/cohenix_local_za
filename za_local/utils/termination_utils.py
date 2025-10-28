"""
Termination & Settlement Utility Functions
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff


def calculate_bcea_notice_period(employee, termination_date):
	"""
	Calculate BCEA minimum notice period.
	
	Args:
		employee: Employee ID or doc
		termination_date: Date of termination
		
	Returns:
		int: Notice period in days
	"""
	if isinstance(employee, str):
		employee = frappe.get_doc("Employee", employee)
		
	if not employee.date_of_joining:
		return 28  # Default to 4 weeks
		
	tenure_days = date_diff(termination_date, employee.date_of_joining)
	tenure_years = tenure_days / 365.25
	
	if tenure_years < 0.5:
		return 7  # 1 week
	elif tenure_years < 1:
		return 14  # 2 weeks
	else:
		return 28  # 4 weeks


def calculate_severance_pay(employee, termination_date, termination_type):
	"""
	Calculate severance pay per BCEA.
	
	BCEA: 1 week's remuneration per completed year.
	Only for operational dismissals.
	
	Args:
		employee: Employee ID or doc
		termination_date: Date of termination
		termination_type: Type of termination
		
	Returns:
		float: Severance pay amount
	"""
	if termination_type != "Dismissal - Operational":
		return 0.0
		
	if isinstance(employee, str):
		employee = frappe.get_doc("Employee", employee)
		
	if not employee.date_of_joining:
		return 0.0
		
	# Completed years only
	tenure_days = date_diff(termination_date, employee.date_of_joining)
	completed_years = int(tenure_days / 365.25)
	
	if completed_years < 1:
		return 0.0
		
	# Get last salary
	salary = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee.name, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1
	)
	
	if not salary:
		return 0.0
		
	monthly_salary = flt(salary[0].base)
	weekly_salary = monthly_salary / 4.33
	
	return weekly_salary * completed_years


def calculate_leave_payout_on_termination(employee):
	"""
	Calculate leave payout for untaken annual leave.
	
	Args:
		employee: Employee ID
		
	Returns:
		dict: {"days": float, "amount": float}
	"""
	# Get leave balance
	leave_balance = frappe.db.sql("""
		SELECT SUM(total_leave_days) as balance
		FROM `tabLeave Allocation`
		WHERE employee = %(employee)s
			AND docstatus = 1
			AND leave_type LIKE '%%Annual%%'
	""", {"employee": employee}, as_dict=1)
	
	if not leave_balance or not leave_balance[0].balance:
		return {"days": 0, "amount": 0}
		
	total_days = flt(leave_balance[0].balance)
	
	# Get daily rate
	salary = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1
	)
	
	if not salary:
		return {"days": total_days, "amount": 0}
		
	monthly_salary = flt(salary[0].base)
	daily_rate = monthly_salary / 30
	
	return {
		"days": total_days,
		"amount": daily_rate * total_days
	}


def calculate_severance_tax(severance_amount):
	"""
	Calculate tax on severance pay.
	
	SARS: First R500,000 is tax-free, remainder taxed at lump sum rates.
	
	Args:
		severance_amount: Severance amount
		
	Returns:
		float: Tax amount
	"""
	tax_free_portion = 500000
	
	if severance_amount <= tax_free_portion:
		return 0.0
		
	taxable = severance_amount - tax_free_portion
	
	# Simplified lump sum tax (18% placeholder)
	# TODO: Implement proper SARS lump sum tax tables
	return taxable * 0.18
