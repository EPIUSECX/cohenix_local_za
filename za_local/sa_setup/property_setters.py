# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Property Setters for za_local app.

Provides default values and UI customizations for standard Frappe/ERPNext DocTypes
to align with South African business practices and compliance requirements.
"""

import frappe
from frappe.custom.doctype.customize_form.customize_form import (
	doctype_properties,
	docfield_properties,
)
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from za_local.utils.hrms_detection import is_hrms_installed

# DocTypes that require protected file attachments for SARS audit compliance
PROTECTED_FILE_DOCTYPES = (
	# Payroll Documents
	"Salary Slip",
	"Payroll Entry",
	"Additional Salary",
	
	# SARS Tax Documents
	"IRP5 Certificate",
	"EMP201 Submission",
	"EMP501 Reconciliation",
	"Tax Directive",
	
	# VAT Documents
	"VAT201 Return",
	
	# COIDA Documents
	"COIDA Annual Return",
	"Workplace Injury",
	"OID Claim",
	
	# Sales & Purchase (for VAT audit trail)
	"Quotation",
	"Sales Order",
	"Delivery Note",
	"Sales Invoice",
	"Request for Quotation",
	"Supplier Quotation",
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	
	# Financial Documents
	"Journal Entry",
	"Payment Entry",
	"Asset",
	"Asset Depreciation Schedule",
	"POS Invoice",
	"Period Closing Voucher",
	"Contract",
	
	# HR Documents
	"Leave Application",
	"Employee Separation",
	"Expense Claim",
	
	# SA-specific Documents
	"Employee Final Settlement",
	"UIF U19 Declaration",
	"Business Trip",
)


def get_property_setters():
	"""
	Returns property setters for South African localization.
	
	Property setters modify default values and behavior of standard DocTypes
	without creating custom fields.
	
	Format: (fieldname, property, value) or (None, property, value) for DocType-level
	"""
	return {
		"Employee": [
			# Set default currency to South African Rand
			("salary_currency", "default", "ZAR"),
			
			# Default salary payment mode to Bank (EFT is standard in SA)
			("salary_mode", "default", "Bank"),
			
			# Hide accommodation type fields (not commonly used in SA HR)
			("permanent_accommodation_type", "hidden", 1),
			("current_accommodation_type", "hidden", 1),
		],
		
		"Company": [
			# Set default currency to ZAR for SA companies
			("default_currency", "default", "ZAR"),
		],
		
		"Salary Structure": [
			# Default currency for salary structures
			("currency", "default", "ZAR"),
			
			# Hide Flexible Benefits section - not used in South African payroll
			# Flexible benefits are for cafeteria-style plans (US/UK), not SA payroll
			# Note: The actual fieldname is "employee_benefits" (child table), not "flexible_benefit"
			("employee_benefits", "hidden", 1),
			("max_benefits", "hidden", 1),
		],
		
		"Salary Structure Assignment": [
			# Hide Flexible Benefits section - not used in South African payroll
			# Flexible benefits are for cafeteria-style plans (US/UK), not SA payroll
			("employee_benefits_section", "hidden", 1),
			("employee_benefits", "hidden", 1),
			("max_benefits", "hidden", 1),
		],
		
		"Salary Component": [
			# Add "Company Contribution" as a Type option alongside Earning and Deduction
			("type", "options", "Earning\nDeduction\nCompany Contribution"),
		],
		
		# Protect attachments on submitted documents (SARS audit requirement)
		PROTECTED_FILE_DOCTYPES: [
			(None, "protect_attached_files", 1),
		],
	}


def apply_property_setters():
	"""Create South African localization property setters from one central definition map."""
	print("Creating property setters...")

	hrms_installed = is_hrms_installed()
	hrms_only_doctypes = {
		"Salary Component",
		"Salary Slip",
		"Salary Structure",
		"Salary Structure Assignment",
		"Payroll Entry",
		"Additional Salary",
	}

	for doctypes, property_setters in get_property_setters().items():
		if isinstance(doctypes, str):
			doctypes = (doctypes,)

		for doctype in doctypes:
			if doctype in hrms_only_doctypes and not hrms_installed:
				print(f"  ⊙ Skipping property setters for {doctype} (HRMS not installed)")
				continue

			if not frappe.db.exists("DocType", doctype):
				print(f"  ⊙ Skipping property setters for {doctype} (DocType not found)")
				continue

			for property_setter in property_setters:
				if property_setter[0]:
					for_doctype = False
					property_type = docfield_properties[property_setter[1]]
				else:
					for_doctype = True
					property_type = doctype_properties[property_setter[1]]

				make_property_setter(
					doctype=doctype,
					fieldname=property_setter[0],
					property=property_setter[1],
					value=property_setter[2],
					property_type=property_type,
					for_doctype=for_doctype,
					validate_fields_for_doctype=False,
				)

	print("✓ Property setters created successfully")
