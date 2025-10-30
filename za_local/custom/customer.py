# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import re


def validate(doc, method):
	"""Validate SA VAT number format for South African customers"""
	# Only validate if company is in South Africa
	if doc.tax_id and frappe.db.exists("Company", {"name": getattr(doc, "company", None), "country": "South Africa"}):
		validate_sa_vat_number(doc)


def validate_sa_vat_number(doc):
	"""
	Validate South African VAT registration number format
	
	SA VAT format: 10 digits, usually starts with 4
	Example: 4123456789
	"""
	if not doc.tax_id:
		return
	
	# Remove spaces and hyphens
	vat_number = doc.tax_id.replace(" ", "").replace("-", "")
	
	# Check if it's 10 digits
	if not re.match(r'^\d{10}$', vat_number):
		frappe.msgprint(
			_("VAT number should be 10 digits (e.g., 4123456789)"),
			title=_("Invalid VAT Format"),
			indicator="orange",
			alert=True
		)
		return
	
	# Check if it starts with 4 (most SA VAT numbers do)
	if not vat_number.startswith('4'):
		frappe.msgprint(
			_("SA VAT numbers typically start with 4. Please verify the number is correct."),
			title=_("VAT Number Warning"),
			indicator="yellow",
			alert=True
		)
	
	# Update the field with cleaned format
	doc.tax_id = vat_number

