from frappe import _

def get_data():
	return [
		{
			"label": _("South Africa"),
			"items": [
				{
					"type": "doctype",
					"name": "ZA Local Setup",
					"description": _("South African localization and company registration settings"),
					"onboard": 1,
				},
			]
		},
	]
