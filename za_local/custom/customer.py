# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _


def validate(doc, method):
	"""Validate tax IDs explicitly marked as South African VAT registrations."""
	if doc.tax_id and getattr(doc, "za_is_vat_vendor", 0):
		validate_sa_vat_number(doc)


def validate_sa_vat_number(doc):
	"""Normalise and validate a South African VAT registration number."""
	if not doc.tax_id:
		return

	vat_number = re.sub(r"[\s-]+", "", doc.tax_id)

	if not re.fullmatch(r"\d{10}", vat_number):
		frappe.throw(
			_("South African VAT Registration Number must be 10 digits."),
			title=_("Invalid VAT Registration Number"),
		)

	if not vat_number.startswith("4"):
		frappe.msgprint(
			_("South African VAT Registration Numbers typically start with 4. Please verify this number."),
			title=_("VAT Registration Number Warning"),
			indicator="yellow",
			alert=True,
		)

	doc.tax_id = vat_number
