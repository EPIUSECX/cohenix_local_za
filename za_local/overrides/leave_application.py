"""
South African Leave Application Override

Extends HRMS Leave Application with BCEA compliance checks.

Note: This module only works when HRMS is installed.
"""

import frappe
from frappe import _
from frappe.utils import getdate, date_diff
from za_local.utils.hrms_detection import require_hrms, get_hrms_doctype_class

# Conditionally import HRMS classes
LeaveApplication = get_hrms_doctype_class(
    "hrms.hr.doctype.leave_application.leave_application",
    "LeaveApplication"
)

if LeaveApplication is None:
    # HRMS not available - create a dummy class to prevent import errors
    class LeaveApplication:
        pass


class ZALeaveApplication(LeaveApplication):
	"""
	South African Leave Application implementation.
	
	Extends standard Leave Application with:
	- BCEA compliance validations
	- Medical certificate requirements
	- Gender-specific leave types
	- Leave accrual validations
	"""
	
	def __init__(self, *args, **kwargs):
		"""Ensure HRMS is available before initialization"""
		if LeaveApplication is None:
			require_hrms("Leave Application")
		super().__init__(*args, **kwargs)
	
	def validate(self):
		"""Validate leave application with SA-specific checks"""
		require_hrms("Leave Application")
		super().validate()
		self.validate_medical_certificate()
		self.validate_bcea_requirements()
		self.validate_gender_specific_leave()
		
	def validate_medical_certificate(self):
		"""
		Validate medical certificate requirement for sick leave.
		BCEA requires medical certificate for sick leave > 2 consecutive days.
		"""
		if not self.leave_type:
			return
			
		# Get leave type details
		leave_type = frappe.get_doc("Leave Type", self.leave_type)
		
		# Check if this is sick leave requiring medical certificate
		if "sick" in self.leave_type.lower():
			days_required = getattr(leave_type, "za_medical_certificate_required_after", 2)
			
			if self.total_leave_days > days_required:
				# Check if medical certificate is attached
				attachments = frappe.get_all(
					"File",
					filters={
						"attached_to_doctype": self.doctype,
						"attached_to_name": self.name
					}
				)
				
				if not attachments:
					frappe.msgprint(
						_(f"Medical certificate is required for sick leave exceeding {days_required} days"),
						indicator="orange",
						title=_("Medical Certificate Required")
					)
					
	def validate_bcea_requirements(self):
		"""
		Validate BCEA compliance requirements.
		- Annual leave: Minimum 21 consecutive days per year
		- Sick leave: 36 days per 3-year cycle
		- Family responsibility: 3 days per year
		"""
		if not self.leave_type:
			return
			
		leave_type = frappe.get_doc("Leave Type", self.leave_type)
		
		# Check if leave type is BCEA compliant
		if not getattr(leave_type, "za_bcea_compliant", False):
			return
			
		# Validate based on leave type
		if "annual" in self.leave_type.lower():
			self.validate_annual_leave_bcea()
		elif "sick" in self.leave_type.lower():
			self.validate_sick_leave_bcea()
		elif "family" in self.leave_type.lower():
			self.validate_family_leave_bcea()
			
	def validate_annual_leave_bcea(self):
		"""
		Validate annual leave BCEA compliance.
		BCEA allows at least one period of 21 consecutive days per year.
		"""
		# This is informational - employees are entitled to take 21 consecutive days
		if self.total_leave_days >= 21:
			frappe.msgprint(
				_("This leave application uses the BCEA minimum of 21 consecutive days annual leave"),
				indicator="blue",
				title=_("BCEA Compliance")
			)
			
	def validate_sick_leave_bcea(self):
		"""
		Validate sick leave BCEA compliance.
		36 days per 3-year cycle for employees working at least 4 days per week.
		"""
		# Get employee working days
		employee = frappe.get_doc("Employee", self.employee)
		
		# BCEA sick leave entitlement
		# This is tracked by the leave allocation - just validate consistency
		pass
		
	def validate_family_leave_bcea(self):
		"""
		Validate family responsibility leave BCEA compliance.
		3 days per annual leave cycle.
		"""
		# Check total family leave taken in current cycle
		from_date = getdate(self.from_date)
		year_start = from_date.replace(month=1, day=1)
		year_end = from_date.replace(month=12, day=31)
		
		total_family_leave = frappe.db.sql("""
			SELECT SUM(total_leave_days)
			FROM `tabLeave Application`
			WHERE employee = %(employee)s
				AND leave_type = %(leave_type)s
				AND from_date >= %(year_start)s
				AND to_date <= %(year_end)s
				AND docstatus = 1
				AND name != %(name)s
		""", {
			"employee": self.employee,
			"leave_type": self.leave_type,
			"year_start": year_start,
			"year_end": year_end,
			"name": self.name or "New"
		})[0][0] or 0
		
		total_with_current = total_family_leave + self.total_leave_days
		
		if total_with_current > 3:
			frappe.throw(
				_("Family responsibility leave exceeds BCEA limit of 3 days per year. "
				  "Already taken: {0} days").format(total_family_leave)
			)
			
	def validate_gender_specific_leave(self):
		"""
		Validate gender-specific leave types (e.g., maternity leave).
		"""
		if not self.leave_type:
			return
			
		leave_type = frappe.get_doc("Leave Type", self.leave_type)
		applicable_gender = getattr(leave_type, "za_applicable_gender", None)
		
		if applicable_gender:
			employee = frappe.get_doc("Employee", self.employee)
			
			if employee.gender != applicable_gender:
				frappe.throw(
					_("Leave type {0} is only applicable to {1} employees").format(
						self.leave_type, applicable_gender
					)
				)


# Override the standard Leave Application class
def override_leave_application():
	"""Register the override in hooks.py"""
	pass

