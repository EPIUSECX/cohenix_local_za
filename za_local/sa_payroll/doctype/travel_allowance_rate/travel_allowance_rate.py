# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, getdate, today


class TravelAllowanceRate(Document):
	def validate(self):
		"""Validate TravelAllowanceRate"""
		self.validate_effective_date()

	def get_current_rate(self):
		"""Return the latest configured travel allowance rate for this company."""
		filters = {"company": self.company} if self.company else {}
		rows = frappe.get_all(
			"Travel Allowance Rate",
			filters=filters,
			fields=["name", "reimbursive_rate_per_km", "fixed_allowance_rate"],
			order_by="effective_from desc",
			limit=1,
		)
		return rows[0] if rows else None

	def validate_effective_date(self):
		if not self.effective_from:
			frappe.throw(_("Effective From is required"))
