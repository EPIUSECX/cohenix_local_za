# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patch: Add additional employee fields

Adds 7 new fields to Employee DocType for enhanced SA compliance:
- Nationality (work permit tracking)
- Working hours per week (BCEA overtime)
- Has children (Family Responsibility Leave)
- Has other employments (multiple employer PAYE)
- Number of dependants (medical tax credit)
- Highest qualification (Skills Development)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add additional employee fields for SA compliance"""
	
	custom_fields = {
		"Employee": [
			{
				"fieldname": "za_personal_information_section",
				"label": "Additional Information",
				"fieldtype": "Section Break",
				"insert_after": "za_payroll_payable_bank_account",
				"collapsible": 1
			},
			{
				"fieldname": "za_nationality",
				"label": "Nationality",
				"fieldtype": "Link",
				"options": "Country",
				"insert_after": "za_personal_information_section",
				"description": "Employee's nationality (for work permit tracking)"
			},
			{
				"fieldname": "za_working_hours_per_week",
				"label": "Working Hours Per Week",
				"fieldtype": "Float",
				"insert_after": "za_nationality",
				"description": "Standard working hours per week for BCEA overtime calculations"
			},
			{
				"fieldname": "za_has_children",
				"label": "Has Children",
				"fieldtype": "Check",
				"insert_after": "za_working_hours_per_week",
				"description": "Employee has children (for Family Responsibility Leave eligibility)"
			},
			{
				"fieldname": "za_additional_column_break",
				"fieldtype": "Column Break",
				"insert_after": "za_has_children"
			},
			{
				"fieldname": "za_has_other_employments",
				"label": "Has Other Employments",
				"fieldtype": "Check",
				"insert_after": "za_additional_column_break",
				"description": "Employee has multiple employers (for PAYE tax directive scenarios)"
			},
			{
				"fieldname": "za_number_of_dependants",
				"label": "Number of Dependants",
				"fieldtype": "Int",
				"insert_after": "za_has_other_employments",
				"description": "Number of dependants for medical tax credit calculation"
			},
			{
				"fieldname": "za_highest_qualification",
				"label": "Highest Qualification",
				"fieldtype": "Select",
				"options": "\nMatric\nNational Certificate\nNational Diploma\nBachelor's Degree\nHonours Degree\nMaster's Degree\nDoctorate\nOther",
				"insert_after": "za_number_of_dependants",
				"description": "Highest educational qualification (for Skills Development reporting)"
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	
	print("✓ Added 7 additional employee fields")

