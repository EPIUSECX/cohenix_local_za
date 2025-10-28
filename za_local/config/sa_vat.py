from frappe import _

def get_data():
    return [
        {
            "label": _("VAT Settings"),
            "items": [
                {
                    "type": "doctype",
                    "name": "SA VAT Settings",
                    "description": _("Configure South African VAT settings and rates"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "VAT Vendor Type",
                    "description": _("VAT vendor classification types"),
                },
            ]
        },
        {
            "label": _("VAT Returns"),
            "items": [
                {
                    "type": "doctype",
                    "name": "VAT201 Return",
                    "description": _("VAT201 Return for SARS submission"),
                    "onboard": 1,
                },
            ]
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "VAT Analysis",
                    "doctype": "VAT201 Return",
                    "is_query_report": True,
                    "description": _("Detailed VAT transaction analysis"),
                }
            ]
        }
    ]

