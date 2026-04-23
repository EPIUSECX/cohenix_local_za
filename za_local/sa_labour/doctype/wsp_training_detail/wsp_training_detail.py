# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, getdate, today


class WspTrainingDetail(Document):
	def validate(self):
		"""Validate WspTrainingDetail"""
		pass

