# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months


class AnnualTrainingReport(Document):
	def validate(self):
		"""Validate AnnualTrainingReport"""
		pass

	def generate_atr_report(self):
		"""TODO: Implement generate_atr_report"""
		pass
	
	def calculate_actual_spend(self):
		"""TODO: Implement calculate_actual_spend"""
		pass
