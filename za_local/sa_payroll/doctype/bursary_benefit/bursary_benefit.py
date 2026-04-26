# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class BursaryBenefit(Document):
	def validate(self):
		"""Validate BursaryBenefit"""
		self.calculate_taxable_amount()

	def calculate_taxable_amount(self):
		"""Calculate taxable bursary value.

		Employee bursaries are treated as taxable by default. Dependent bursaries
		can be marked taxable by the practitioner when the exemption conditions are
		not met.
		"""
		if self.beneficiary_type == "Employee":
			self.is_taxable = 1
		self.taxable_amount = flt(self.bursary_amount) if self.is_taxable else 0
		return self.taxable_amount
