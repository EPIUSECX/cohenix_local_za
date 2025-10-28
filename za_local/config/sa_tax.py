from frappe import _

def get_data():
    return [
        {
            "label": _("SARS Submissions"),
            "items": [
                {
                    "type": "doctype",
                    "name": "EMP201 Submission",
                    "description": _("Monthly SARS EMP201 Return for PAYE, UIF, SDL and ETI"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "EMP501 Reconciliation",
                    "description": _("Bi-annual Employer Reconciliation Declaration"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "IRP5 Certificate",
                    "description": _("Employee Tax Certificate"),
                    "onboard": 1,
                },
            ]
        },
        {
            "label": _("Employment Tax Incentive"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Employee ETI Log",
                    "description": _("Employment Tax Incentive (ETI) calculation log"),
                },
                {
                    "type": "doctype",
                    "name": "ETI Slab",
                    "description": _("ETI calculation slabs and formulas"),
                },
            ]
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "EMP201 Report",
                    "doctype": "EMP201 Submission",
                    "is_query_report": True,
                    "description": _("Analysis report for EMP201 submissions"),
                }
            ]
        }
    ]

