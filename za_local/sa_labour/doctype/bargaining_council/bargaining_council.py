# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class BargainingCouncil(Document):
	def validate(self):
		"""Validate BargainingCouncil"""
		pass

