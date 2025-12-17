# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PayrollPaymentBatch(Document):
	def validate(self):
		"""Validate PayrollPaymentBatch"""
		pass
	
	def on_submit(self):
		"""Actions on submission"""
		pass

	@frappe.whitelist()
	def set_eft_generated(self, file_url: str | None = None):
		"""Mark EFT file as generated and update totals.
		Also stores the file URL if provided.
		"""
		if not self.payroll_entry:
			frappe.throw("Payroll Entry is required")

		# Compute totals from salary slips linked to the payroll entry
		slips = frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": self.payroll_entry, "docstatus": 1},
			fields=["name", "net_pay"],
		)
		self.total_employees = len(slips)
		self.total_amount = sum(flt(s["net_pay"]) for s in slips)
		self.eft_file_generated = 1
		if file_url:
			self.eft_file_path = file_url
		self.save(ignore_permissions=True)
		return {"ok": True}
