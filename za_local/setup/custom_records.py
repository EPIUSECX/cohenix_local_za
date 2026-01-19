"""
Custom Records for ZA Local

This module defines custom records (DocType Links) that create bidirectional
connections between za_local DocTypes and standard ERPNext/HRMS DocTypes.
These appear in the "Connections" tab of documents.
"""

from za_local.utils.hrms_detection import is_hrms_installed


def get_za_local_custom_records():
	"""
	Get custom records conditionally based on HRMS availability.
	
	Returns:
		list: List of custom record dictionaries for DocType Links
	"""
	hrms_installed = is_hrms_installed()
	
	records = [
		# Employee-related DocTypes (13 links)
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Tax & Compliance",
			"link_doctype": "Tax Directive",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Fringe Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Company Car Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Housing Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Low Interest Loan Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Cellphone Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Fuel Card Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Bursary Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Leave Encashment SA",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Separation",
			"link_doctype": "Employee Final Settlement",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Tax & Compliance",
			"link_doctype": "UIF U19 Declaration",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "NAEDO Deduction",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Skills Development Record",
			"link_fieldname": "employee",
			"custom": 1,
		},
		
		# Company-related DocTypes (4 links)
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Retirement Fund",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Travel Allowance Rate",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Workplace Skills Plan",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Annual Training Report",
			"link_fieldname": "company",
			"custom": 1,
		},
		
		# Payroll Entry-related DocTypes (1 link)
		# Note: EMP201 Submission link removed - field doesn't exist in DocType
		{
			"doctype": "DocType Link",
			"parent": "Payroll Entry",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Payroll Payment Batch",
			"link_fieldname": "payroll_entry",
			"custom": 1,
		},
		
		# Bargaining Council-related (1 link)
		{
			"doctype": "DocType Link",
			"parent": "Bargaining Council",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Sectoral Compliance",
			"link_doctype": "Industry Specific Contribution",
			"link_fieldname": "bargaining_council",
			"custom": 1,
		},
		
		# Expense Claim link to Business Trip
		{
			"doctype": "DocType Link",
			"parent": "Expense Claim",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Travel",
			"link_doctype": "Business Trip",
			"link_fieldname": "expense_claim",
			"custom": 1,
		},
	]
	
	# Filter out HRMS-dependent links if HRMS is not installed
	if not hrms_installed:
		# HRMS-dependent parent doctypes
		hrms_parents = ["Employee", "Payroll Entry", "Expense Claim"]
		records = [r for r in records if r.get("parent") not in hrms_parents]
	
	return records
