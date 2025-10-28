# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months


class TravelAllowanceRate(Document):
	def validate(self):
		"""Validate TravelAllowanceRate"""
		pass

	def get_current_rate(self):
		"""TODO: Implement get_current_rate"""
		pass
	
	def validate_effective_date(self):
		"""TODO: Implement validate_effective_date"""
		pass
