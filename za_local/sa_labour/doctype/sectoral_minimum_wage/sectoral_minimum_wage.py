# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class SectoralMinimumWage(Document):
	def validate(self):
		"""Validate SectoralMinimumWage"""
		pass

	def validate_employee_salary(self):
		"""TODO: Implement validate_employee_salary"""
		pass

