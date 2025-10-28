# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months, date_diff


class BursaryBenefit(Document):
	def validate(self):
		"""Validate BursaryBenefit"""
		pass

	def calculate_taxable_amount(self):
		"""TODO: Implement calculate_taxable_amount"""
		pass

