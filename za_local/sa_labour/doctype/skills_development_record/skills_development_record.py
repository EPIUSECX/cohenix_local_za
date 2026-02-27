# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months


class SkillsDevelopmentRecord(Document):
	def validate(self):
		"""Validate SkillsDevelopmentRecord"""
		pass

	def calculate_bec_points(self):
		"""TODO: Implement calculate_bec_points"""
		pass
	
	def validate_training_dates(self):
		"""TODO: Implement validate_training_dates"""
		pass
