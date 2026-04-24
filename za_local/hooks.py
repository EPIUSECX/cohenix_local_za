
app_name = "za_local"
app_title = "SA Localisation"
app_publisher = "Cohenix"
app_description = "Comprehensive South African localization for ERPNext covering payroll, tax, VAT, and COIDA compliance"
app_email = "info@cohenix.com"
app_license = "mit"
app_logo_url = "/assets/za_local/images/sa_map_icon.png"
app_home = "/desk/sa-overview"

# Import hook utility functions for conditional configuration
# These are called at import time to generate configuration dynamically
from za_local.sa_setup.custom_fields import get_za_local_custom_records
from za_local.utils.hooks_utils import get_hrms_doctype_js, get_override_doctype_class

# Add to Apps Screen (Frappe v16 desk: one App tile with map logo; workspace icons nest under it)
# ------------------
add_to_apps_screen = [
	{
		"name": "za_local",
		"title": "SA Localisation",
		"logo": "/assets/za_local/images/sa_map_icon.png",
		"route": "/desk/sa-overview",
	}
]

# Apps
# ------------------
# Note: HRMS is optional - za_local works with or without HRMS
# If HRMS is not installed, payroll/HR features will be disabled
required_apps = ["erpnext"]

# Fixtures
# ------------------
fixtures = [
    # Custom Fields: source of truth is setup/custom_fields.py (applied on install/migrate)
    # Property Setters
    {"dt": "Property Setter", "filters": [["module", "in", ["SA Localisation", "SA Payroll", "SA VAT", "SA Labour", "SA COIDA", "SA Setup"]]]},

    # SA-compliant Print Formats
    {
        "dt": "Print Format",
        "filters": [
            ["name", "in", [
                "SA Sales Invoice",
                "SA Quotation",
                "SA Sales Order",
                "SA Delivery Note",
                "SA Purchase Invoice",
                "SA Purchase Order",
                "SA Payment Entry",
                "SA Credit Note",
                "SA Debit Note"
            ]]
        ]
    },

    # App doctype for v16 compatibility
    # Required for proper app deployment and management in Frappe v16+
    {"dt": "App", "filters": [["name", "=", "za_local"]]},
]

# Includes in <head>
# ------------------
app_include_css = "/assets/za_local/css/za_local.css"

# Include JS in doctype views
# ------------------
# Base JS files (always available)
doctype_js = {
    "COIDA Annual Return": "public/js/coida_annual_return.js",
    "Workplace Injury": "public/js/workplace_injury.js",
    "OID Claim": "public/js/oid_claim.js",
    "EMP501 Reconciliation": "public/js/emp501_reconciliation.js",
    "Sales Invoice": "public/js/vat_tax_calculation.js",
    "Purchase Invoice": "public/js/vat_tax_calculation.js",
}

# Merge HRMS-dependent JS files conditionally
doctype_js.update(get_hrms_doctype_js())

doctype_list_js = {
    "EMP501 Reconciliation": "public/js/emp501_reconciliation_list.js"
}

# Installation
# ------------------
before_install = "za_local.sa_setup.install.before_install"
after_install = "za_local.sa_setup.install.after_install"
before_migrate = ["za_local.sa_setup.install.before_migrate"]
after_migrate = ["za_local.sa_setup.install.after_migrate"]

# Uninstallation
# ------------------
after_uninstall = "za_local.sa_setup.uninstall.after_uninstall"

# Setup Wizard Integration
# ------------------
setup_wizard_requires = "assets/za_local/js/setup_wizard.js"
setup_wizard_stages = "za_local.sa_setup.setup_wizard.get_sa_localization_stages"

# Override Whitelisted Methods
# ------------------
# Override ERPNext's get_charts_for_country to use our whitelisted wrapper
# This allows the setup wizard to call the function via API
override_whitelisted_methods = {
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country":
		"za_local.accounts.setup_chart.get_charts_for_country_with_za",
}

# DocType Class Overrides
# ------------------
# Override standard doctype classes with South African implementations
# Only register HRMS overrides if HRMS is installed
override_doctype_class = get_override_doctype_class()

# Document Events
# ------------------
# Hook on document methods and events
doc_events = {
    # Journal Entry events (existing)
    "Journal Entry": {
        "on_trash": "za_local.overrides.journal_entry.on_trash",
        "on_cancel": "za_local.overrides.journal_entry.on_cancel"
    },

    # Sales document deletion protection (SARS audit trail)
    "Quotation": {
        "on_trash": "za_local.custom.sales.on_trash",
    },
    "Sales Order": {
        "on_trash": "za_local.custom.sales.on_trash",
    },
    "Sales Invoice": {
        "on_trash": "za_local.custom.sales.on_trash",
    },

    # Customer validation for SA VAT numbers
    "Customer": {
        "validate": "za_local.custom.customer.validate",
    },

    # Keep ERPNext's zero-rated item contract aligned with za_local VAT categories
    "Item": {
        "validate": "za_local.sa_vat.item_sync.sync_item_zero_rated_flag",
    },

    # Purchase document deletion protection (SARS audit trail)
    "Request for Quotation": {
        "on_trash": "za_local.custom.purchase.on_trash",
    },
    "Supplier Quotation": {
        "on_trash": "za_local.custom.purchase.on_trash",
    },
    "Purchase Order": {
        "on_trash": "za_local.custom.purchase.on_trash",
    },
    "Purchase Receipt": {
        "on_trash": "za_local.custom.purchase.on_trash",
    },
    "Purchase Invoice": {
        "on_trash": "za_local.custom.purchase.on_trash",
    },
}

# Monkey Patching
# ------------------
# Monkey patches are now applied during installation/migration via setup.monkey_patches
# This ensures patches are applied at the right time, not at import time

# Custom Records (DocType Links for Bidirectional Connections)
# ------------------
# Creates links between za_local DocTypes and standard DocTypes
# These appear in the "Connections" tab of documents
# HRMS-dependent links are filtered conditionally
za_local_custom_records = get_za_local_custom_records()


# Scheduled Tasks
# ------------------
# Automated compliance monitoring and reminders
scheduler_events = {
	"all": [
		"za_local.tasks.all"
	],
	"daily": [
		"za_local.tasks.daily"
	],
	"weekly": [
		"za_local.tasks.weekly"
	],
	"monthly": [
		"za_local.tasks.monthly"
	]
}

# Permissions
# ------------------
# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

# Document Events for Specific Workflows
# ------------------
# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# Request Events
# ------------------
# Apply ZA chart patches in the current web / API worker so that the
# setup wizard and any CoA-related flows understand the ZA template.
before_request = ["za_local.accounts.setup_chart.apply_chart_patches_on_request"]

# Job Events
# ------------------
# before_job = ["za_local.utils.before_job"]
# after_job = ["za_local.utils.after_job"]

# User Data Protection
# ------------------
# user_data_fields = [
#     {
#         "doctype": "{doctype_1}",
#         "filter_by": "{filter_by}",
#         "redact_fields": ["{field_1}", "{field_2}"],
#         "partial": 1,
#     },
# ]

# Authentication and authorization
# ------------------
# auth_hooks = [
#     "za_local.auth.validate"
# ]

# Translation
# ------------------
# Make all summary doctype labels for South African localization
# override_doctype_dashboards = {
#     "Task": "za_local.task.get_dashboard_data"
# }
