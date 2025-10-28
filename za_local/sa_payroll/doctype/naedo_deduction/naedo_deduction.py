# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class NaedoDeduction(Document):
	def validate(self):
		"""Validate NaedoDeduction"""
		pass
	
	def on_submit(self):
		"""Actions on submission"""
		pass
