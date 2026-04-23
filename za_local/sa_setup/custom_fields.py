"""
South African Localization: Custom Fields and DocType Links

Single module under setup that defines and applies:
1. Custom Field fixtures (source of truth; applied on install/migrate)
2. Cleanup of old custom fields
3. Custom records (DocType Links for Connections tab)

Property setters are centralized in `sa_setup/property_setters.py` and applied by
`sa_setup/install.py` so there is a single source of truth.
"""

import json

import frappe

from za_local.utils.hrms_detection import is_hrms_installed

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
    "description": "South African employee classification. Required during payroll processing.",
    "reqd": 0
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
    "name": "Employee-za_occupational_level",
    "dt": "Employee",
    "module": "SA Labour",
    "label": "Occupational Level",
    "fieldname": "za_occupational_level",
    "fieldtype": "Select",
    "options": "\\nTop Management\\nSenior Management\\nProfessionally Qualified\\nSkilled Technical\\nSemi-Skilled\\nUnskilled\\nTemporary Employees\\nNon-Permanent",
    "insert_after": "za_race",
    "description": "Occupational level for Employment Equity Act (EEA) reporting"
  },
  {
    "doctype": "Custom Field",
    "name": "Employee-za_ee_column_break",
    "dt": "Employee",
    "module": "SA Labour",
    "fieldname": "za_ee_column_break",
    "fieldtype": "Column Break",
    "insert_after": "za_occupational_level"
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


def _get_irp5_custom_field_fixtures():
	"""Additional custom fields required for SARS-aligned IRP5/IT3(a) generation."""
	return [
		{
			"doctype": "Custom Field",
			"name": "Salary Component-za_sars_payroll_code",
			"dt": "Salary Component",
			"module": "SA Payroll",
			"label": "SARS Payroll Code",
			"fieldname": "za_sars_payroll_code",
			"fieldtype": "Link",
			"options": "SARS Payroll Code",
			"insert_after": "type",
			"description": "SARS payroll code used for IRP5 / IT3(a) certificate mapping",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_tax_certificate_section",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "South African Tax Certificate",
			"fieldname": "za_tax_certificate_section",
			"fieldtype": "Section Break",
			"insert_after": "za_is_disabled",
			"collapsible": 1,
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_identity_type",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Identity Type",
			"fieldname": "za_identity_type",
			"fieldtype": "Select",
			"options": "\\nSouth African ID\\nPassport\\nAsylum Seeker\\nPermit\\nOther",
			"insert_after": "za_tax_certificate_section",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_income_tax_reference_number",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Income Tax Reference Number",
			"fieldname": "za_income_tax_reference_number",
			"fieldtype": "Data",
			"insert_after": "za_identity_type",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_passport_country_of_issue",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Passport Country of Issue",
			"fieldname": "za_passport_country_of_issue",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "za_income_tax_reference_number",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_nature_of_person",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Nature of Person",
			"fieldname": "za_nature_of_person",
			"fieldtype": "Select",
			"options": "\\nIndividual\\nDirector\\nTrust Beneficiary\\nLabour Broker\\nPersonal Service Provider\\nForeign Employee\\nOther",
			"insert_after": "za_passport_country_of_issue",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_tax_certificate_column_break",
			"dt": "Employee",
			"module": "SA Payroll",
			"fieldname": "za_tax_certificate_column_break",
			"fieldtype": "Column Break",
			"insert_after": "za_nature_of_person",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_residential_address",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Residential Address",
			"fieldname": "za_residential_address",
			"fieldtype": "Link",
			"options": "Address",
			"insert_after": "za_tax_certificate_column_break",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_postal_address",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Postal Address",
			"fieldname": "za_postal_address",
			"fieldtype": "Link",
			"options": "Address",
			"insert_after": "za_residential_address",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_business_address_override",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Business Address Override",
			"fieldname": "za_business_address_override",
			"fieldtype": "Link",
			"options": "Address",
			"insert_after": "za_postal_address",
			"description": "Optional alternate business address for SARS certificates",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_not_paid_electronically",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Not Paid Electronically",
			"fieldname": "za_not_paid_electronically",
			"fieldtype": "Check",
			"insert_after": "za_business_address_override",
			"description": "Tick if remuneration is not paid through electronic banking",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_tax_certificate_bank_section",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Bank Account for Tax Certificate",
			"fieldname": "za_tax_certificate_bank_section",
			"fieldtype": "Section Break",
			"insert_after": "za_not_paid_electronically",
			"collapsible": 1,
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_bank_account_type",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Bank Account Type",
			"fieldname": "za_bank_account_type",
			"fieldtype": "Select",
			"options": "\\nCheque\\nSavings\\nTransmission\\nCredit Card\\nBond\\nOther",
			"insert_after": "za_tax_certificate_bank_section",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_bank_account_holder_name",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Bank Account Holder Name",
			"fieldname": "za_bank_account_holder_name",
			"fieldtype": "Data",
			"insert_after": "za_bank_account_type",
		},
		{
			"doctype": "Custom Field",
			"name": "Employee-za_bank_account_holder_relationship",
			"dt": "Employee",
			"module": "SA Payroll",
			"label": "Account Holder Relationship",
			"fieldname": "za_bank_account_holder_relationship",
			"fieldtype": "Select",
			"options": "\\nEmployee\\nSpouse\\nParent\\nGuardian\\nTrust\\nOther",
			"insert_after": "za_bank_account_holder_name",
		},
		{
			"doctype": "Custom Field",
			"name": "Company-za_paye_reference_number",
			"dt": "Company",
			"module": "SA Payroll",
			"label": "PAYE Reference Number",
			"fieldname": "za_paye_reference_number",
			"fieldtype": "Data",
			"insert_after": "za_uif_reference_number",
			"description": "South African PAYE employer reference number",
		},
		{
			"doctype": "Custom Field",
			"name": "Company-za_trading_name",
			"dt": "Company",
			"module": "SA Payroll",
			"label": "Trading Name",
			"fieldname": "za_trading_name",
			"fieldtype": "Data",
			"insert_after": "za_paye_reference_number",
		},
		{
			"doctype": "Custom Field",
			"name": "Company-za_business_address",
			"dt": "Company",
			"module": "SA Payroll",
			"label": "Business Address",
			"fieldname": "za_business_address",
			"fieldtype": "Link",
			"options": "Address",
			"insert_after": "za_trading_name",
			"description": "Structured business address for SARS certificates. Falls back to the primary company address.",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_south_african_address_section",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "South African Address Detail",
			"fieldname": "za_south_african_address_section",
			"fieldtype": "Section Break",
			"insert_after": "pincode",
			"collapsible": 1,
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_unit_no",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Unit No",
			"fieldname": "za_unit_no",
			"fieldtype": "Data",
			"insert_after": "za_south_african_address_section",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_complex_name",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Complex Name",
			"fieldname": "za_complex_name",
			"fieldtype": "Data",
			"insert_after": "za_unit_no",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_street_no",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Street No",
			"fieldname": "za_street_no",
			"fieldtype": "Data",
			"insert_after": "za_complex_name",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_suburb_or_district",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Suburb or District",
			"fieldname": "za_suburb_or_district",
			"fieldtype": "Data",
			"insert_after": "za_street_no",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_country_code",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Country Code",
			"fieldname": "za_country_code",
			"fieldtype": "Data",
			"insert_after": "za_suburb_or_district",
			"default": "ZA",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_address_column_break",
			"dt": "Address",
			"module": "SA Payroll",
			"fieldname": "za_address_column_break",
			"fieldtype": "Column Break",
			"insert_after": "za_country_code",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_postal_address_type",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Postal Address Type",
			"fieldname": "za_postal_address_type",
			"fieldtype": "Select",
			"options": "\\nStreet\\nPO Box\\nPrivate Bag\\nPost Office\\nCare Of\\nOther",
			"insert_after": "za_address_column_break",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_care_of",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Care Of",
			"fieldname": "za_care_of",
			"fieldtype": "Data",
			"insert_after": "za_postal_address_type",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_postal_service_number",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Postal Service Number",
			"fieldname": "za_postal_service_number",
			"fieldtype": "Data",
			"insert_after": "za_care_of",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_address_line_3",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Address Line 3",
			"fieldname": "za_address_line_3",
			"fieldtype": "Data",
			"insert_after": "za_postal_service_number",
		},
		{
			"doctype": "Custom Field",
			"name": "Address-za_address_line_4",
			"dt": "Address",
			"module": "SA Payroll",
			"label": "Address Line 4",
			"fieldname": "za_address_line_4",
			"fieldtype": "Data",
			"insert_after": "za_address_line_3",
		},
	]


def _apply_custom_field_fixtures():
	"""Apply custom field fixtures from embedded JSON. Skips doctypes that don't exist (e.g. HRMS-only)."""
	data = json.loads(CUSTOM_FIELD_FIXTURES_JSON)
	data.extend(_get_irp5_custom_field_fixtures())
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
# Section 2: Cleanup of old custom fields
# ---------------------------------------------------------------------------

FIELDS_TO_DELETE_IF_EXIST = {
	"Employee": [
		"custom_id_number", "custom_employee_type", "custom_special_economic_zone",
		"custom_hours_per_month", "payroll_payable_bank_account",
		"custom_tax_number", "custom_residential_address",
	],
	"Company": [
		"custom_coida_registration_number", "custom_vat_number",
		"custom_sdl_reference_number", "custom_uif_reference_number",
		"custom_paye_reference_number",
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
					deleted_count += 1
					print(f"  ✓ Deleted old custom field: {custom_field_name}")
				except Exception as e:
					print(f"  ! Error deleting custom field {custom_field_name}: {e}")
	if deleted_count > 0:
		frappe.db.commit()
		print(f"  ✓ Cleaned up {deleted_count} old custom field(s)")


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
	Apply custom fields, cleanup, and custom records in one order.
	Called from install.py sync_za_local() on install and migrate.
	"""
	_apply_custom_field_fixtures()
	_cleanup_old_custom_fields()
	insert_custom_records()
