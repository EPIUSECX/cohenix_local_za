from frappe import _

def get_data():
	return [
		{
			"label": _("SA Payroll"),
			"items": [
				# Employee Configuration Section
				{
					"type": "doctype",
					"name": "Employee Type",
					"description": _("South African employee classification types"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Employee Payroll Frequency",
					"description": _("Configure payroll processing frequencies for employees"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Employee Private Benefit",
					"description": _("Track employee private benefits for tax purposes"),
				},
				
				# Master Data Section
				{
					"type": "doctype",
					"name": "Retirement Fund",
					"description": _("Configure retirement funds (Pension, Provident, Retirement Annuity, Preservation)"),
				},
				{
					"type": "doctype",
					"name": "Travel Allowance Rate",
					"description": _("Configure travel allowance rates for SARS compliance"),
				},
				{
					"type": "doctype",
					"name": "Tax Rebates and Medical Tax Credit",
					"description": _("Configure tax rebates and medical tax credits"),
				},
				{
					"type": "doctype",
					"name": "Retirement Annuity Slab",
					"description": _("Configure retirement annuity contribution slabs"),
				},
				{
					"type": "doctype",
					"name": "Medical Tax Credit Rate",
					"description": _("Medical aid tax credit rates"),
				},
				{
					"type": "doctype",
					"name": "Tax Rebates Rate",
					"description": _("Income tax rebate rates (Primary, Secondary, Tertiary)"),
				},
				{
					"type": "doctype",
					"name": "SARS Vehicle Emissions Rate",
					"description": _("CO2-based vehicle emission rates for company car taxation"),
				},
				{
					"type": "doctype",
					"name": "Holiday List",
					"description": _("South African public holidays for payroll periods"),
				},
				
				# Benefits Section
				{
					"type": "doctype",
					"name": "Company Car Benefit",
					"description": _("Company car benefits with CO2-based taxation"),
				},
				{
					"type": "doctype",
					"name": "Housing Benefit",
					"description": _("Housing benefit tracking and taxation"),
				},
				{
					"type": "doctype",
					"name": "Low Interest Loan Benefit",
					"description": _("Low interest loan benefits for tax calculations"),
				},
				{
					"type": "doctype",
					"name": "Cellphone Benefit",
					"description": _("Cellphone benefit tracking"),
				},
				{
					"type": "doctype",
					"name": "Fuel Card Benefit",
					"description": _("Fuel card benefit tracking"),
				},
				{
					"type": "doctype",
					"name": "Bursary Benefit",
					"description": _("Bursary benefit tracking"),
				},
				{
					"type": "doctype",
					"name": "Fringe Benefit",
					"description": _("Comprehensive fringe benefit management"),
				},
				
				# Business Trip Section
				{
					"type": "doctype",
					"name": "Business Trip Settings",
					"description": _("Configure business trip settings and rates"),
				},
				{
					"type": "doctype",
					"name": "Business Trip Region",
					"description": _("Configure business trip regions and rates"),
				},
				{
					"type": "doctype",
					"name": "Business Trip",
					"description": _("Manage business trips with SARS-compliant allowances"),
				},
				
				# Payments & Settlement Section
				{
					"type": "doctype",
					"name": "Payroll Payment Batch",
					"description": _("Generate EFT payment batches for payroll"),
				},
				{
					"type": "doctype",
					"name": "Employee Final Settlement",
					"description": _("Calculate final settlement on employee termination"),
				},
				{
					"type": "doctype",
					"name": "Leave Encashment SA",
					"description": _("Leave encashment calculations for SA compliance"),
				},
				
				# Sectoral Compliance Section
				{
					"type": "doctype",
					"name": "SETA",
					"description": _("Skills Education Training Authority configuration"),
				},
				{
					"type": "doctype",
					"name": "Bargaining Council",
					"description": _("Bargaining council agreements"),
				},
				{
					"type": "doctype",
					"name": "Sectoral Minimum Wage",
					"description": _("Sectoral minimum wage rates"),
				},
				{
					"type": "doctype",
					"name": "Industry Specific Contribution",
					"description": _("Industry-specific contribution requirements"),
				},
				
				# Reports Section
				{
					"type": "report",
					"name": "Payroll Register",
					"description": _("Comprehensive payroll register report"),
					"is_query_report": True,
				},
				{
					"type": "report",
					"name": "Department Cost Analysis",
					"description": _("Department-wise payroll cost analysis"),
					"is_query_report": True,
				},
				{
					"type": "report",
					"name": "Statutory Submissions Summary",
					"description": _("Summary of all statutory submissions (EMP201, EMP501, etc.)"),
					"is_query_report": True,
				},
			]
		}
	]
