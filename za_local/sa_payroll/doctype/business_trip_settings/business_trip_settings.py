# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Business Trip Settings

Configuration settings for Business Trip management including:
- Mileage allowance rates (SARS compliance)
- Default expense claim types
- Workflow settings
"""

import frappe
from frappe import _
from frappe.model.document import Document


class BusinessTripSettings(Document):
	"""Single DocType for Business Trip configuration settings"""
	
	def validate(self):
		"""Validate settings before save"""
		self.validate_mileage_rate()
		self.validate_expense_claim_types()
	
	def validate_mileage_rate(self):
		"""Ensure mileage rate is within reasonable bounds"""
		if self.mileage_allowance_rate:
			if self.mileage_allowance_rate < 0:
				frappe.throw(_("Mileage Allowance Rate cannot be negative"))
			
			if self.mileage_allowance_rate > 50:
				frappe.msgprint(
					_("Mileage Allowance Rate seems high. SARS recommended rate is R4.25/km (2024)"),
					alert=True,
					indicator="orange"
				)
	
	def validate_expense_claim_types(self):
		"""Validate that expense claim types exist if specified"""
		claim_type_fields = [
			"mileage_expense_claim_type",
			"meal_expense_claim_type",
			"incidental_expense_claim_type"
		]
		
		for field in claim_type_fields:
			claim_type = self.get(field)
			if claim_type and not frappe.db.exists("Expense Claim Type", claim_type):
				frappe.throw(_("Expense Claim Type {0} does not exist").format(claim_type))


@frappe.whitelist()
def get_mileage_rate():
	"""
	Get the configured mileage allowance rate.
	
	Returns:
		float: Mileage rate per kilometer, defaults to 4.25 (SARS 2024 rate)
	"""
	settings = frappe.get_single("Business Trip Settings")
	return settings.mileage_allowance_rate or 4.25


@frappe.whitelist()
def get_expense_claim_types():
	"""
	Get all configured expense claim types for business trips.
	
	Returns:
		dict: Dictionary of expense claim types
	"""
	settings = frappe.get_single("Business Trip Settings")
	return {
		"mileage": settings.mileage_expense_claim_type,
		"meal": settings.meal_expense_claim_type,
		"incidental": settings.incidental_expense_claim_type
	}

