# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class CellphoneBenefit(Document):
	def validate(self):
		"""Validate CellphoneBenefit"""
		self.calculate_monthly_benefit()

	def calculate_monthly_benefit(self):
		"""Calculate the taxable private-use portion of a cellphone contract."""
		business_use = flt(self.business_use_percentage)
		private_use = flt(self.private_use_percentage)
		if not private_use and business_use:
			private_use = max(100 - business_use, 0)
			self.private_use_percentage = private_use
		elif not private_use and not business_use:
			private_use = 100
			self.private_use_percentage = private_use

		self.monthly_taxable_value = flt(self.contract_value) * (private_use / 100)
		return self.monthly_taxable_value
