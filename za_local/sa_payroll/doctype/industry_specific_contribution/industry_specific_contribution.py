# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months, date_diff


class IndustrySpecificContribution(Document):
	def validate(self):
		"""Validate IndustrySpecificContribution"""
		pass

