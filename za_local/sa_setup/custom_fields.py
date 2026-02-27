"""
South African Localization: Custom Fields, Property Setters, and DocType Links

Single module under setup that defines and applies:
1. Custom Field fixtures (source of truth; applied on install/migrate)
2. Cleanup of old custom fields + property setters
3. Custom records (DocType Links for Connections tab)

All three run together via setup_custom_fields() in the same order every time.
"""

import json

import frappe
from za_local.utils.hrms_detection import is_hrms_installed
from za_local.utils.setup_utils import get_property_type


# ---------------------------------------------------------------------------
# Section 1: Custom Field fixtures (source of truth; applied by _apply_custom_field_fixtures)
# ---------------------------------------------------------------------------

CUSTOM_FIELD_FIXTURES_JSON = """
[
  {
    "doctype": "Custom Field",
    "name": "HR Settings-za_amount_per_kilometer",
    "dt": "HR Settings",
    "module": "SA Payroll",
    "label": "Amount Per Kilometer",
    "fieldname": "za_amount_per_kilometer",
    "fieldtype": "Currency",
    "insert_after": "emp_created_by",
    "description": "Reimbursement rate per kilometer for mileage claims"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_south_african_settings_section",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "South African Settings",
    "fieldname": "za_south_african_settings_section",
    "fieldtype": "Section Break",
    "insert_after": "daily_wages_fraction_for_half_day",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_calculate_annual_taxable_amount_based_on",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "Calculate Annual Taxable Amount Based On",
    "fieldname": "za_calculate_annual_taxable_amount_based_on",
    "fieldtype": "Select",
    "options": "\\nJoining and Relieving Date\\nPayroll Period",
    "default": "Payroll Period",
    "insert_after": "za_south_african_settings_section",
    "description": "Method for calculating annual taxable income"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_payroll_column_break",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "fieldname": "za_payroll_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_calculate_annual_taxable_amount_based_on"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_disable_eti_calculation",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "Disable ETI Calculation",
    "fieldname": "za_disable_eti_calculation",
    "fieldtype": "Check",
    "insert_after": "za_payroll_column_break",
    "description": "Disable automatic Employment Tax Incentive calculations"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_statutory_components_section",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "South African Statutory Components",
    "fieldname": "za_statutory_components_section",
    "fieldtype": "Section Break",
    "insert_after": "za_disable_eti_calculation",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_paye_salary_component",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "PAYE Salary Component",
    "fieldname": "za_paye_salary_component",
    "fieldtype": "Link",
    "options": "Salary Component",
    "insert_after": "za_statutory_components_section",
    "description": "Salary Component used for Pay As You Earn (PAYE) tax"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_uif_employee_salary_component",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "UIF Employee Salary Component",
    "fieldname": "za_uif_employee_salary_component",
    "fieldtype": "Link",
    "options": "Salary Component",
    "insert_after": "za_paye_salary_component",
    "description": "Salary Component for UIF employee contribution"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_uif_employer_salary_component",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "UIF Employer Salary Component",
    "fieldname": "za_uif_employer_salary_component",
    "fieldtype": "Link",
    "options": "Salary Component",
    "insert_after": "za_uif_employee_salary_component",
    "description": "Salary Component for UIF employer contribution"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_statutory_column_break",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "fieldname": "za_statutory_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_uif_employer_salary_component"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_sdl_salary_component",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "SDL Salary Component",
    "fieldname": "za_sdl_salary_component",
    "fieldtype": "Link",
    "options": "Salary Component",
    "insert_after": "za_statutory_column_break",
    "description": "Salary Component for Skills Development Levy (SDL)"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Settings-za_coida_salary_component",
    "dt": "Payroll Settings",
    "module": "SA Payroll",
    "label": "COIDA Salary Component",
    "fieldname": "za_coida_salary_component",
    "fieldtype": "Link",
    "options": "Salary Component",
    "insert_after": "za_sdl_salary_component",
    "description": "Salary Component for Compensation for Occupational Injuries and Diseases Act (COIDA)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_south_african_details_section",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "South African Details",
    "fieldname": "za_south_african_details_section",
    "fieldtype": "Section Break",
    "insert_after": "passport_number",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_id_number",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "SA ID Number",
    "fieldname": "za_id_number",
    "fieldtype": "Data",
    "insert_after": "za_south_african_details_section",
    "description": "South African ID Number (13 digits)",
    "length": 13
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_employee_type",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Employee Type",
    "fieldname": "za_employee_type",
    "fieldtype": "Link",
    "options": "Employee Type",
    "insert_after": "za_id_number",
    "description": "South African employee classification",
    "reqd": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_special_economic_zone",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Special Economic Zone",
    "fieldname": "za_special_economic_zone",
    "fieldtype": "Check",
    "insert_after": "za_employee_type",
    "description": "Employee works in a Special Economic Zone (SEZ)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_payroll_column_break",
    "dt": "Employee",
    "module": "SA Payroll",
    "fieldname": "za_payroll_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_special_economic_zone"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_hours_per_month",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Hours Per Month",
    "fieldname": "za_hours_per_month",
    "fieldtype": "Float",
    "insert_after": "za_payroll_column_break",
    "description": "Standard working hours per month for ETI calculations"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_payroll_payable_bank_account",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Payroll Payable Bank Account",
    "fieldname": "za_payroll_payable_bank_account",
    "fieldtype": "Link",
    "options": "Bank Account",
    "insert_after": "za_hours_per_month",
    "description": "Bank account for payroll disbursement"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_personal_information_section",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Additional Information",
    "fieldname": "za_personal_information_section",
    "fieldtype": "Section Break",
    "insert_after": "za_payroll_payable_bank_account",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_nationality",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Nationality",
    "fieldname": "za_nationality",
    "fieldtype": "Link",
    "options": "Country",
    "insert_after": "za_personal_information_section",
    "description": "Employee's nationality (for work permit tracking)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_working_hours_per_week",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Working Hours Per Week",
    "fieldname": "za_working_hours_per_week",
    "fieldtype": "Float",
    "insert_after": "za_nationality",
    "description": "Standard working hours per week for BCEA overtime calculations"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_has_children",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Has Children",
    "fieldname": "za_has_children",
    "fieldtype": "Check",
    "insert_after": "za_working_hours_per_week",
    "description": "Employee has children (for Family Responsibility Leave eligibility)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_additional_column_break",
    "dt": "Employee",
    "module": "SA Payroll",
    "fieldname": "za_additional_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_has_children"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_has_other_employments",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Has Other Employments",
    "fieldname": "za_has_other_employments",
    "fieldtype": "Check",
    "insert_after": "za_additional_column_break",
    "description": "Employee has multiple employers (for PAYE tax directive scenarios)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_number_of_dependants",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Number of Dependants",
    "fieldname": "za_number_of_dependants",
    "fieldtype": "Int",
    "insert_after": "za_has_other_employments",
    "description": "Number of dependants for medical tax credit calculation"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_highest_qualification",
    "dt": "Employee",
    "module": "SA Payroll",
    "label": "Highest Qualification",
    "fieldname": "za_highest_qualification",
    "fieldtype": "Select",
    "options": "\\nMatric\\nNational Certificate\\nNational Diploma\\nBachelor's Degree\\nHonours Degree\\nMaster's Degree\\nDoctorate\\nOther",
    "insert_after": "za_number_of_dependants",
    "description": "Highest educational qualification (for Skills Development reporting)"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_employment_equity_section",
    "dt": "Employee",
    "module": "SA Labour",
    "label": "Employment Equity",
    "fieldname": "za_employment_equity_section",
    "fieldtype": "Section Break",
    "insert_after": "za_highest_qualification",
    "collapsible": 1,
    "description": "Employment Equity Act (EEA) classification fields"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_race",
    "dt": "Employee",
    "module": "SA Labour",
    "label": "Race",
    "fieldname": "za_race",
    "fieldtype": "Select",
    "options": "\\nAfrican\\nColoured\\nIndian\\nWhite\\nOther",
    "insert_after": "za_employment_equity_section",
    "description": "Race classification for Employment Equity Act (EEA) reporting"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_ee_column_break",
    "dt": "Employee",
    "module": "SA Labour",
    "fieldname": "za_ee_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_race"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_is_disabled",
    "dt": "Employee",
    "module": "SA Labour",
    "label": "Is Disabled",
    "fieldname": "za_is_disabled",
    "fieldtype": "Check",
    "insert_after": "za_ee_column_break",
    "description": "Person with disability (PWD) for Employment Equity Act (EEA) reporting"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Structure-company_contribution_section",
    "dt": "Salary Structure",
    "module": "SA Payroll",
    "label": "Company Contribution Section",
    "fieldname": "company_contribution_section",
    "fieldtype": "Section Break",
    "insert_after": "deductions"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Structure-company_contribution",
    "dt": "Salary Structure",
    "module": "SA Payroll",
    "label": "Company Contribution",
    "fieldname": "company_contribution",
    "fieldtype": "Table",
    "options": "Company Contribution",
    "insert_after": "company_contribution_section"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Slip-company_contribution_section",
    "dt": "Salary Slip",
    "module": "SA Payroll",
    "label": "Company Contribution Section",
    "fieldname": "company_contribution_section",
    "fieldtype": "Section Break",
    "insert_after": "deductions"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Slip-company_contribution",
    "dt": "Salary Slip",
    "module": "SA Payroll",
    "label": "Company Contribution",
    "fieldname": "company_contribution",
    "fieldtype": "Table",
    "options": "Company Contribution",
    "insert_after": "company_contribution_section"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Slip-total_company_contribution",
    "dt": "Salary Slip",
    "module": "SA Payroll",
    "label": "Total Company Contribution",
    "fieldname": "total_company_contribution",
    "fieldtype": "Currency",
    "read_only": 1,
    "insert_after": "company_contribution"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_south_african_registration_section",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "South African Registration Details",
    "fieldname": "za_south_african_registration_section",
    "fieldtype": "Section Break",
    "insert_after": "tax_id",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_vat_number",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "VAT Number",
    "fieldname": "za_vat_number",
    "fieldtype": "Data",
    "insert_after": "za_south_african_registration_section",
    "description": "South African VAT Registration Number",
    "length": 10
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_coida_registration_number",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "COIDA Registration Number",
    "fieldname": "za_coida_registration_number",
    "fieldtype": "Data",
    "insert_after": "za_vat_number",
    "description": "Compensation for Occupational Injuries and Diseases Act Registration Number"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_registration_column_break",
    "dt": "Company",
    "module": "SA Payroll",
    "fieldname": "za_registration_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_coida_registration_number"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_sdl_reference_number",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "SDL Reference Number",
    "fieldname": "za_sdl_reference_number",
    "fieldtype": "Data",
    "insert_after": "za_registration_column_break",
    "description": "Skills Development Levy Reference Number"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_uif_reference_number",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "UIF Reference Number",
    "fieldname": "za_uif_reference_number",
    "fieldtype": "Data",
    "insert_after": "za_sdl_reference_number",
    "description": "Unemployment Insurance Fund Reference Number"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_additional_configuration_section",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "Additional Configuration",
    "fieldname": "za_additional_configuration_section",
    "fieldtype": "Section Break",
    "insert_after": "za_uif_reference_number",
    "collapsible": 1
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_seta",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "SETA",
    "fieldname": "za_seta",
    "fieldtype": "Link",
    "options": "SETA",
    "insert_after": "za_additional_configuration_section",
    "description": "Skills Education Training Authority"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_bargaining_council",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "Bargaining Council",
    "fieldname": "za_bargaining_council",
    "fieldtype": "Link",
    "options": "Bargaining Council",
    "insert_after": "za_seta"
  },
  {
    "doctype": "Custom Field",
    "name": "Company-za_sectoral_determination",
    "dt": "Company",
    "module": "SA Payroll",
    "label": "Sectoral Determination",
    "fieldname": "za_sectoral_determination",
    "fieldtype": "Select",
    "options": "\\nDomestic Workers\\nFarm Workers\\nPrivate Security\\nHospitality\\nWholesale/Retail\\nOther",
    "insert_after": "za_bargaining_council"
  },
  {
    "doctype": "Custom Field",
    "name": "Additional Salary-za_is_company_contribution",
    "dt": "Additional Salary",
    "module": "SA Payroll",
    "label": "Is Company Contribution",
    "fieldname": "za_is_company_contribution",
    "fieldtype": "Check",
    "insert_after": "column_break_8",
    "description": "Mark as company contribution for payroll processing"
  },
  {
    "doctype": "Custom Field",
    "name": "Salary Structure Assignment-za_annual_bonus",
    "dt": "Salary Structure Assignment",
    "module": "SA Payroll",
    "label": "Annual Bonus",
    "fieldname": "za_annual_bonus",
    "fieldtype": "Currency",
    "insert_after": "base",
    "allow_on_submit": 1,
    "description": "Annual bonus amount for tax calculations"
  },
  {
    "doctype": "Custom Field",
    "name": "Expense Claim-business_trip",
    "dt": "Expense Claim",
    "module": "SA Payroll",
    "label": "Business Trip",
    "fieldname": "business_trip",
    "fieldtype": "Link",
    "options": "Business Trip",
    "insert_after": "company",
    "read_only": 1,
    "description": "Link to Business Trip if this expense claim was auto-generated"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Employee Detail-za_is_bank_entry_created",
    "dt": "Payroll Employee Detail",
    "module": "SA Payroll",
    "label": "Is Bank Entry Created",
    "fieldname": "za_is_bank_entry_created",
    "fieldtype": "Check",
    "insert_after": "custom_employee_type",
    "read_only": 1,
    "description": "Indicates if bank entry has been created"
  },
  {
    "doctype": "Custom Field",
    "name": "Payroll Employee Detail-za_is_company_contribution_created",
    "dt": "Payroll Employee Detail",
    "module": "SA Payroll",
    "label": "Is Company Contribution Created",
    "fieldname": "za_is_company_contribution_created",
    "fieldtype": "Check",
    "insert_after": "za_is_bank_entry_created",
    "read_only": 1,
    "description": "Indicates if company contribution entry has been created"
  },
  {
    "doctype": "Custom Field",
    "name": "Journal Entry Account-za_is_payroll_entry",
    "dt": "Journal Entry Account",
    "module": "SA Payroll",
    "label": "Is Payroll Entry",
    "fieldname": "za_is_payroll_entry",
    "fieldtype": "Check",
    "insert_after": "reference_name",
    "description": "Mark as payroll-related journal entry"
  },
  {
    "doctype": "Custom Field",
    "name": "Journal Entry Account-za_is_company_contribution",
    "dt": "Journal Entry Account",
    "module": "SA Payroll",
    "label": "Is Company Contribution",
    "fieldname": "za_is_company_contribution",
    "fieldtype": "Check",
    "insert_after": "za_is_payroll_entry",
    "description": "Mark as company contribution entry"
  },
  {
    "doctype": "Custom Field",
    "name": "Customer-za_company_registration",
    "dt": "Customer",
    "module": "SA Payroll",
    "label": "Company Registration Number",
    "fieldname": "za_company_registration",
    "fieldtype": "Data",
    "insert_after": "tax_id",
    "description": "CIPC company registration number"
  },
  {
    "doctype": "Custom Field",
    "name": "Customer-za_is_vat_vendor",
    "dt": "Customer",
    "module": "SA Payroll",
    "label": "Is VAT Vendor",
    "fieldname": "za_is_vat_vendor",
    "fieldtype": "Check",
    "insert_after": "za_company_registration",
    "default": 0,
    "description": "Check if customer is registered for VAT in South Africa"
  },
  {
    "doctype": "Custom Field",
    "name": "Item Group-is_capital_goods",
    "dt": "Item Group",
    "module": "SA Payroll",
    "label": "Is Capital Goods",
    "fieldname": "is_capital_goods",
    "fieldtype": "Check",
    "insert_after": "parent_item_group",
    "default": 0,
    "description": "Mark this item group as capital goods for VAT201 input tax classification. Items in this group will be classified as 'Capital Goods Input' in VAT201 returns."
  }
]
"""


def _apply_custom_field_fixtures():
	"""Apply custom field fixtures from embedded JSON. Skips doctypes that don't exist (e.g. HRMS-only)."""
	data = json.loads(CUSTOM_FIELD_FIXTURES_JSON)
	for d in data:
		if not frappe.db.exists("DocType", d["dt"]):
			continue
		try:
			if frappe.db.exists("Custom Field", d["name"]):
				doc = frappe.get_doc("Custom Field", d["name"])
				doc.update(d)
				doc.flags.ignore_permissions = True
				doc.save()
			else:
				frappe.get_doc(d).insert(ignore_permissions=True)
		except Exception as e:
			print(f"  ! Error applying custom field {d.get('name')}: {e}")
	frappe.db.commit()
	print("  ✓ Custom field fixtures applied")


# ---------------------------------------------------------------------------
# Section 2: Cleanup of old custom fields + property setters
# ---------------------------------------------------------------------------

FIELDS_TO_DELETE_IF_EXIST = {
	"Employee": [
		"custom_id_number", "custom_employee_type", "custom_special_economic_zone",
		"custom_hours_per_month", "payroll_payable_bank_account"
	],
	"Company": [
		"custom_coida_registration_number", "custom_vat_number",
		"custom_sdl_reference_number", "custom_uif_reference_number"
	],
	"Payroll Settings": [
		"custom_coida_salary_component", "custom_disable_eti_calculation"
	],
	"Salary Structure Assignment": ["custom_annual_bonus"],
	"Additional Salary": ["is_company_contribution"],
	"Salary Component": ["is_company_contribution"],
}


def _cleanup_old_custom_fields():
	"""Remove old/renamed custom fields from previous installations."""
	deleted_count = 0
	for doctype, fieldnames in FIELDS_TO_DELETE_IF_EXIST.items():
		for fieldname in fieldnames:
			custom_field_name = f"{doctype}-{fieldname}"
			if frappe.db.exists("Custom Field", custom_field_name):
				try:
					frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
					frappe.db.commit()
					deleted_count += 1
					print(f"  ✓ Deleted old custom field: {custom_field_name}")
				except Exception as e:
					print(f"  ! Error deleting custom field {custom_field_name}: {e}")
	if deleted_count > 0:
		print(f"  ✓ Cleaned up {deleted_count} old custom field(s)")


def setup_property_setters():
	"""Property setters for standard field behaviours (labels, hidden, read_only)."""
	hrms_installed = is_hrms_installed()
	hrms_only_doctypes = {"Salary Structure Assignment", "Salary Slip"}
	properties = {
		"Salary Structure Assignment": {
			"variable": {"hidden": 0, "read_only": 0},
			"base": {"hidden": 0, "read_only": 0}
		},
		"Salary Slip": {"payroll_entry": {"hidden": 0}},
		"Customer": {
			"tax_id": {
				"label": "VAT Registration Number",
				"description": "South African VAT registration number (format: 4XXXXXXXXXX)"
			}
		}
	}
	for doctype, field_properties in properties.items():
		if doctype in hrms_only_doctypes and not hrms_installed:
			continue
		if not frappe.db.exists("DocType", doctype):
			continue
		for fieldname, props in field_properties.items():
			for prop, value in props.items():
				try:
					frappe.make_property_setter({
						"doctype": doctype,
						"fieldname": fieldname,
						"property": prop,
						"value": value,
						"property_type": get_property_type(value)
					})
				except Exception as e:
					print(f"Error setting property {prop} for {doctype}.{fieldname}: {e}")
	print("✓ Property setters configured")


# ---------------------------------------------------------------------------
# Section 3: Custom records (DocType Links for Connections tab)
# ---------------------------------------------------------------------------

def _get_doctype_link_records():
	"""DocType Link records; filtered by HRMS availability."""
	hrms_installed = is_hrms_installed()
	records = [
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Tax & Compliance", "link_doctype": "Tax Directive", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Fringe Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Company Car Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Housing Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Low Interest Loan Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Cellphone Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Fuel Card Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Benefits", "link_doctype": "Bursary Benefit", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Payroll", "link_doctype": "Leave Encashment SA", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Separation", "link_doctype": "Employee Final Settlement", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Tax & Compliance", "link_doctype": "UIF U19 Declaration", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Employee", "parentfield": "links", "parenttype": "DocType", "group": "Training & Development", "link_doctype": "Skills Development Record", "link_fieldname": "employee", "custom": 1},
		{"doctype": "DocType Link", "parent": "Company", "parentfield": "links", "parenttype": "DocType", "group": "Payroll", "link_doctype": "Retirement Fund", "link_fieldname": "company", "custom": 1},
		{"doctype": "DocType Link", "parent": "Company", "parentfield": "links", "parenttype": "DocType", "group": "Payroll", "link_doctype": "Travel Allowance Rate", "link_fieldname": "company", "custom": 1},
		{"doctype": "DocType Link", "parent": "Company", "parentfield": "links", "parenttype": "DocType", "group": "Training & Development", "link_doctype": "Workplace Skills Plan", "link_fieldname": "company", "custom": 1},
		{"doctype": "DocType Link", "parent": "Company", "parentfield": "links", "parenttype": "DocType", "group": "Training & Development", "link_doctype": "Annual Training Report", "link_fieldname": "company", "custom": 1},
		{"doctype": "DocType Link", "parent": "Payroll Entry", "parentfield": "links", "parenttype": "DocType", "group": "Payroll", "link_doctype": "Payroll Payment Batch", "link_fieldname": "payroll_entry", "custom": 1},
		{"doctype": "DocType Link", "parent": "Bargaining Council", "parentfield": "links", "parenttype": "DocType", "group": "Sectoral Compliance", "link_doctype": "Industry Specific Contribution", "link_fieldname": "bargaining_council", "custom": 1},
		{"doctype": "DocType Link", "parent": "Expense Claim", "parentfield": "links", "parenttype": "DocType", "group": "Travel", "link_doctype": "Business Trip", "link_fieldname": "expense_claim", "custom": 1},
	]
	if not hrms_installed:
		hrms_parents = ["Employee", "Payroll Entry", "Expense Claim"]
		records = [r for r in records if r.get("parent") not in hrms_parents]
	return records


def get_za_local_custom_records():
	"""Used by hooks: returns list of DocType Link records (for Connections tab)."""
	return _get_doctype_link_records()


def insert_custom_records():
	"""Insert DocType Link records. Idempotent (skips existing)."""
	print("Inserting custom records...")
	for custom_record in _get_doctype_link_records():
		filters = {k: v for k, v in custom_record.items() if not isinstance(v, (list, dict))}
		if not frappe.db.exists(filters):
			frappe.get_doc(custom_record).insert(ignore_if_duplicate=True)
	print("✓ Custom records inserted successfully")


# ---------------------------------------------------------------------------
# Single entry point: run all three sections in order
# ---------------------------------------------------------------------------

def setup_custom_fields():
	"""
	Apply custom fields, cleanup, property setters, and custom records in one order.
	Called from install.py sync_za_local() on install and migrate.
	"""
	_apply_custom_field_fixtures()
	_cleanup_old_custom_fields()
	setup_property_setters()
	insert_custom_records()
