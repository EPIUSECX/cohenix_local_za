# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt


class TaxDirective(Document):
	def validate(self):
		"""Validate Tax Directive"""
		self.validate_dates()
		self.validate_directive_details()
		self.check_for_overlapping_directives()
		self.update_status()
		
	def before_submit(self):
		"""Actions before submission"""
		self.status = "Active"
		
	def on_cancel(self):
		"""Actions on cancellation"""
		self.status = "Cancelled"
		
	def validate_dates(self):
		"""Validate effective dates"""
		if not self.effective_from:
			frappe.throw(_("Effective From date is required"))
			
		if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
			frappe.throw(_("Effective To date cannot be before Effective From date"))
			
	def validate_directive_details(self):
		"""Validate directive-specific details"""
		if self.directive_type == "Reduced Tax Rate":
			if not self.tax_rate_override and self.tax_rate_override != 0:
				frappe.throw(_("Tax Rate Override is required for Reduced Tax Rate directive"))
				
		elif self.directive_type == "Fixed Amount":
			if not self.fixed_amount:
				frappe.throw(_("Fixed Monthly Amount is required for Fixed Amount directive"))
				
		elif self.directive_type == "Garnishee Order":
			if not self.garnishee_creditor:
				frappe.throw(_("Creditor Name is required for Garnishee Order"))
			if not self.garnishee_amount and not self.garnishee_percentage:
				frappe.throw(_("Either Garnishee Amount or Percentage must be specified"))
				
	def check_for_overlapping_directives(self):
		"""Check for overlapping active directives for the same employee"""
		overlapping = frappe.db.sql("""
			SELECT name, directive_number
			FROM `tabTax Directive`
			WHERE employee = %(employee)s
				AND name != %(name)s
				AND docstatus = 1
				AND status = 'Active'
				AND effective_from <= COALESCE(%(effective_to)s, '2099-12-31')
				AND COALESCE(effective_to, '2099-12-31') >= %(effective_from)s
		""", {
			"employee": self.employee,
			"name": self.name or "New",
			"effective_from": self.effective_from,
			"effective_to": self.effective_to or "2099-12-31"
		}, as_dict=True)
		
		if overlapping:
			frappe.throw(
				_("There is already an active Tax Directive ({0}) for employee {1} with overlapping dates").format(
					overlapping[0].directive_number, self.employee
				)
			)
			
	def update_status(self):
		"""Update status based on effective dates"""
		if not self.effective_from:
			return
			
		current_date = getdate(today())
		effective_from = getdate(self.effective_from)
		
		if effective_from > current_date:
			self.status = "Pending"
		elif self.effective_to and getdate(self.effective_to) < current_date:
			self.status = "Expired"
		elif self.docstatus == 1:
			self.status = "Active"
			
	def apply_to_salary_slip(self, salary_slip):
		"""
		Apply tax directive to salary slip calculation
		
		Args:
			salary_slip: SalarySlip document
			
		Returns:
			dict: Modified tax calculation details
		"""
		if self.status != "Active":
			return None
			
		# Check if salary slip is within directive period
		slip_date = getdate(salary_slip.posting_date)
		if slip_date < getdate(self.effective_from):
			return None
		if self.effective_to and slip_date > getdate(self.effective_to):
			return None
			
		result = {
			"directive_applied": True,
			"directive_number": self.directive_number,
			"directive_type": self.directive_type
		}
		
		if self.directive_type == "Reduced Tax Rate":
			result["tax_rate_override"] = flt(self.tax_rate_override)
			
		elif self.directive_type == "Fixed Amount":
			result["fixed_tax_amount"] = flt(self.fixed_amount)
			
		elif self.directive_type == "Garnishee Order":
			result["garnishee_creditor"] = self.garnishee_creditor
			result["garnishee_amount"] = flt(self.garnishee_amount)
			result["garnishee_percentage"] = flt(self.garnishee_percentage)
			
		return result


@frappe.whitelist()
def get_active_directive(employee, date=None):
	"""
	Get active tax directive for an employee on a specific date
	
	Args:
		employee: Employee ID
		date: Date to check (defaults to today)
		
	Returns:
		Tax Directive document or None
	"""
	if not date:
		date = today()
		
	directives = frappe.get_all(
		"Tax Directive",
		filters={
			"employee": employee,
			"docstatus": 1,
			"status": "Active",
			"effective_from": ["<=", date],
		},
		or_filters=[
			["effective_to", ">=", date],
			["effective_to", "is", "not set"]
		],
		order_by="effective_from desc",
		limit=1
	)
	
	if directives:
		return frappe.get_doc("Tax Directive", directives[0].name)
	
	return None

