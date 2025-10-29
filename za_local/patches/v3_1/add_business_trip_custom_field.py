# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patch: Add business_trip custom field to Expense Claim

Adds the business_trip link field to Expense Claim for tracking
expense claims generated from Business Trip documents.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add business_trip field to Expense Claim"""
	
	custom_fields = {
		"Expense Claim": [
			{
				"fieldname": "business_trip",
				"label": "Business Trip",
				"fieldtype": "Link",
				"options": "Business Trip",
				"insert_after": "company",
				"read_only": 1,
				"description": "Link to Business Trip if this expense claim was auto-generated"
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	
	print("✓ Added business_trip field to Expense Claim")

