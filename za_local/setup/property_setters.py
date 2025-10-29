# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Property Setters for za_local app.

Provides default values and UI customizations for standard Frappe/ERPNext DocTypes
to align with South African business practices and compliance requirements.
"""

# DocTypes that require protected file attachments for SARS audit compliance
PROTECTED_FILE_DOCTYPES = (
	# Payroll Documents
	"Salary Slip",
	"Payroll Entry",
	"Additional Salary",
	
	# SARS Tax Documents
	"IRP5 Certificate",
	"IT3b Certificate",
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
		],
		
		# Protect attachments on submitted documents (SARS audit requirement)
		PROTECTED_FILE_DOCTYPES: [
			(None, "protect_attached_files", 1),
		],
	}

