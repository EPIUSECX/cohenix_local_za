"""
South African Employee Separation Override

Extends HRMS Employee Separation with BCEA compliance and SA calculations.

Note: This module only works when HRMS is installed.
"""

import frappe
from frappe import _
from frappe.utils import getdate, flt, date_diff
from za_local.utils.hrms_detection import require_hrms, get_hrms_doctype_class

# Conditionally import HRMS classes
EmployeeSeparation = get_hrms_doctype_class(
    "hrms.hr.doctype.employee_separation.employee_separation",
    "EmployeeSeparation"
)

if EmployeeSeparation is None:
    # HRMS not available - create a dummy class to prevent import errors
    class EmployeeSeparation:
        pass


class ZAEmployeeSeparation(EmployeeSeparation):
	"""
	South African Employee Separation implementation.
	
	Extends standard Employee Separation with:
	- BCEA notice period calculations
	- Severance pay calculations (operational dismissals)
	- Leave payout calculations
	- Final settlement generation
	"""
	
	def __init__(self, *args, **kwargs):
		"""Ensure HRMS is available before initialization"""
		if EmployeeSeparation is None:
			require_hrms("Employee Separation")
		super().__init__(*args, **kwargs)
	
	def validate(self):
		"""Validate with SA-specific checks"""
		require_hrms("Employee Separation")
		super().validate()
		self.calculate_notice_period()
		self.calculate_severance_pay()
		self.calculate_leave_payout()
		
	def calculate_notice_period(self):
		"""
		Calculate BCEA minimum notice periods based on tenure.
		
		BCEA minimums:
		- < 6 months: 1 week
		- 6 months to 1 year: 2 weeks
		- > 1 year: 4 weeks
		"""
		if not self.resignation_letter_date:
			return
			
		termination_date = getdate(self.resignation_letter_date)
		employee = frappe.get_doc("Employee", self.employee)
		
		if not employee.date_of_joining:
			return
			
		# Calculate tenure
		tenure_days = date_diff(termination_date, employee.date_of_joining)
		tenure_years = tenure_days / 365.25
		
		# BCEA notice periods
		if tenure_years < 0.5:
			notice_days = 7  # 1 week
		elif tenure_years < 1:
			notice_days = 14  # 2 weeks
		else:
			notice_days = 28  # 4 weeks
			
		# Store for reference
		self.za_notice_period_days = notice_days
		
		frappe.msgprint(
			_("BCEA minimum notice period: {0} days").format(notice_days),
			indicator="blue"
		)
		
	def calculate_severance_pay(self):
		"""
		Calculate severance pay for operational dismissals.
		
		BCEA: 1 week's remuneration per completed year of service.
		Only applicable for dismissals due to operational requirements.
		"""
		if not hasattr(self, "za_termination_type"):
			return
			
		if self.za_termination_type != "Dismissal - Operational":
			self.za_severance_pay = 0
			return
			
		employee = frappe.get_doc("Employee", self.employee)
		
		if not employee.date_of_joining:
			return
			
		# Calculate completed years
		termination_date = getdate(self.resignation_letter_date or today())
		tenure_days = date_diff(termination_date, employee.date_of_joining)
		completed_years = int(tenure_days / 365.25)
		
		if completed_years < 1:
			self.za_severance_pay = 0
			return
			
		# Get weekly remuneration
		last_salary = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1
		)
		
		if not last_salary:
			return
			
		monthly_salary = flt(last_salary[0].base)
		weekly_salary = monthly_salary / 4.33  # Average weeks per month
		
		self.za_severance_pay = weekly_salary * completed_years
		
		frappe.msgprint(
			_("Severance pay calculated: R{0} ({1} weeks × {2} years)").format(
				flt(self.za_severance_pay, 2),
				flt(weekly_salary, 2),
				completed_years
			),
			indicator="green"
		)
		
	def calculate_leave_payout(self):
		"""
		Calculate leave payout for untaken annual leave.
		"""
		# Get outstanding leave balance
		leave_balance = frappe.db.sql("""
			SELECT leave_type, SUM(total_leave_days) as balance
			FROM `tabLeave Allocation`
			WHERE employee = %(employee)s
				AND docstatus = 1
				AND leave_type LIKE '%%Annual%%'
			GROUP BY leave_type
		""", {"employee": self.employee}, as_dict=1)
		
		if not leave_balance:
			self.za_leave_payout = 0
			return
			
		# Get daily rate
		last_salary = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1
		)
		
		if not last_salary:
			return
			
		monthly_salary = flt(last_salary[0].base)
		daily_rate = monthly_salary / 30
		
		total_days = sum([flt(row.balance) for row in leave_balance])
		self.za_leave_payout = daily_rate * total_days
		
		frappe.msgprint(
			_("Leave payout calculated: R{0} ({1} days × R{2})").format(
				flt(self.za_leave_payout, 2),
				flt(total_days, 1),
				flt(daily_rate, 2)
			),
			indicator="green"
		)
		
	@frappe.whitelist()
	def create_final_settlement(self):
		"""Create Employee Final Settlement document"""
		if not self.docstatus == 1:
			frappe.throw(_("Employee Separation must be submitted first"))
			
		# Check if settlement already exists
		existing = frappe.db.exists("Employee Final Settlement", {"employee": self.employee})
		if existing:
			frappe.throw(_("Final Settlement already created: {0}").format(existing))
			
		# Create settlement
		settlement = frappe.get_doc({
			"doctype": "Employee Final Settlement",
			"employee": self.employee,
			"separation_date": self.resignation_letter_date,
			"termination_type": getattr(self, "za_termination_type", ""),
			"notice_period_days": getattr(self, "za_notice_period_days", 0),
			"severance_pay": getattr(self, "za_severance_pay", 0),
			"leave_payout": getattr(self, "za_leave_payout", 0),
		})
		settlement.insert()
		
		frappe.msgprint(_("Final Settlement created: {0}").format(settlement.name))
		return settlement.name
