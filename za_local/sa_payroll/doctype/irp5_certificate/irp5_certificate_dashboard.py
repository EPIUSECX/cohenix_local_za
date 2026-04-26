from frappe import _


def get_data():
	return {
		"internal_links": {
			"EMP501 Reconciliation": "emp501_reconciliation",
		},
		"transactions": [
			{
				"label": _("Payroll Compliance"),
				"items": ["EMP501 Reconciliation"],
			}
		],
	}
