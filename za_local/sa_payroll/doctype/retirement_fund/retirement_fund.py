# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, getdate, today


class RetirementFund(Document):
	def validate(self):
		"""Validate RetirementFund"""
		if not self.fund_name:
			frappe.throw(_("Fund Name is required"))

	def calculate_employee_contribution(self, pensionable_amount=0):
		"""Calculate the employee contribution from a pensionable amount."""
		return flt(pensionable_amount) * flt(self.employee_contribution_percentage) / 100

	def calculate_employer_contribution(self, pensionable_amount=0):
		"""Calculate the employer contribution from a pensionable amount."""
		return flt(pensionable_amount) * flt(self.employer_contribution_percentage) / 100

	def calculate_tax_deduction(self, taxable_income=0, contribution_amount=0):
		"""Apply the configured tax-deductible percentage limit."""
		limit = flt(taxable_income) * flt(self.tax_deductible_limit) / 100
		return min(flt(contribution_amount), limit) if limit else flt(contribution_amount)
