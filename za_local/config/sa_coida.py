from frappe import _

def get_data():
	return [
		{
			"label": _("COIDA Management"),
			"items": [
				{
					"type": "doctype",
					"name": "COIDA Settings",
					"description": _("Configure COIDA settings and industry rates"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "COIDA Annual Return",
					"description": _("Annual Return for Compensation for Occupational Injuries and Diseases Act"),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Workplace Injuries"),
			"items": [
				{
					"type": "doctype",
					"name": "Workplace Injury",
					"description": _("Record and manage workplace injuries"),
				},
				{
					"type": "doctype",
					"name": "OID Claim",
					"description": _("Manage Occupational Injury and Disease claims"),
				}
			]
		}
	]
