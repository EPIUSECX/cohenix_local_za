# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, getdate, today


class LeaveEncashmentSa(Document):
	def validate(self):
		"""Validate LeaveEncashmentSa"""
		self.calculate_leave_payout()
		self.calculate_leave_payout_tax()

	def calculate_leave_payout(self):
		"""Return the configured leave payout amount.

		The DocType stores the practitioner-approved payout value; payroll posting
		is handled through HRMS salary components/additional salary.
		"""
		return flt(self.encashment_amount)

	def calculate_leave_payout_tax(self):
		"""Calculate a conservative withholding estimate for the payout."""
		self.tax_amount = flt(self.encashment_amount) * 0.25
		self.net_amount = flt(self.encashment_amount) - flt(self.tax_amount)
		return self.tax_amount

	def create_additional_salary(self):
		"""Create an HRMS Additional Salary record for the leave payout."""
		if not self.employee:
			frappe.throw(_("Employee is required"))
		if not self.encashment_date:
			frappe.throw(_("Encashment Date is required"))
		if not flt(self.encashment_amount):
			frappe.throw(_("Encashment Amount is required"))

		component = "Leave Encashment"
		if not frappe.db.exists("Salary Component", component):
			component = frappe.db.get_value("Salary Component", {"type": "Earning"}, "name")
		if not component:
			frappe.throw(_("No earning Salary Component is available for leave encashment"))

		existing = frappe.db.exists(
			"Additional Salary",
			{
				"employee": self.employee,
				"salary_component": component,
				"payroll_date": self.encashment_date,
				"ref_doctype": self.doctype,
				"ref_docname": self.name,
			},
		)
		if existing:
			return existing

		additional_salary = frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"employee": self.employee,
				"salary_component": component,
				"payroll_date": self.encashment_date,
				"amount": flt(self.encashment_amount),
				"company": frappe.db.get_value("Employee", self.employee, "company"),
				"ref_doctype": self.doctype,
				"ref_docname": self.name,
			}
		)
		additional_salary.insert(ignore_permissions=True)
		return additional_salary.name
