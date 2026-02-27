from frappe import _

def get_data():
	return [
		{
			"label": _("Skills Development"),
			"items": [
				{
					"type": "doctype",
					"name": "Workplace Skills Plan",
					"description": _("Annual Workplace Skills Plan (WSP)"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Annual Training Report",
					"description": _("Annual Training Report (ATR)"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Skills Development Record",
					"description": _("Skills development and training records"),
				},
				{
					"type": "doctype",
					"name": "SETA",
					"description": _("Skills Education Training Authority configuration"),
				},
			]
		},
		{
			"label": _("Employment Equity"),
			"items": [
				{
					"type": "report",
					"name": "Ee Workforce Profile",
					"doctype": "Employee",
					"is_query_report": True,
					"description": _("Employment equity workforce profile"),
				},
				{
					"type": "report",
					"name": "Eea2 Income Differentials",
					"is_query_report": True,
					"description": _("EEA2 income differentials report"),
				},
				{
					"type": "report",
					"name": "Eea4 Employment Equity Plan",
					"is_query_report": True,
					"description": _("EEA4 employment equity plan report"),
				},
			]
		},
		{
			"label": _("Business Trips"),
			"items": [
				{
					"type": "doctype",
					"name": "Business Trip Settings",
					"description": _("Configure business trip settings and rates"),
					"onboard": 1,
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
			]
		},
		{
			"label": _("Sectoral & Bargaining"),
			"items": [
				{
					"type": "doctype",
					"name": "Sectoral Minimum Wage",
					"description": _("Sectoral minimum wage rates"),
				},
				{
					"type": "doctype",
					"name": "Bargaining Council",
					"description": _("Bargaining council agreements"),
				},
				{
					"type": "doctype",
					"name": "Industry Specific Contribution",
					"description": _("Industry-specific contribution requirements"),
				},
			]
		},
	]
