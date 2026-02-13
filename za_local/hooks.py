
app_name = "za_local"
app_title = "South Africa"
app_publisher = "Cohenix"
app_description = "Comprehensive South African localization for ERPNext covering payroll, tax, VAT, and COIDA compliance"
app_email = "info@cohenix.com"
app_license = "mit"
app_logo_url = "/assets/za_local/images/sa_map_icon.png"


# Import hook utility functions for conditional configuration
# These are called at import time to generate configuration dynamically
from za_local.utils.hooks_utils import get_hrms_doctype_js, get_override_doctype_class
from za_local.setup.custom_records import get_za_local_custom_records


# Add to Apps Screen
# ------------------
# Standard Frappe localization - app appears in module navigation automatically
# No custom workspace routing needed

# Apps
# ------------------
# Note: HRMS is optional - za_local works with or without HRMS
# If HRMS is not installed, payroll/HR features will be disabled
required_apps = ["frappe", "erpnext"]

# Fixtures
# ------------------
fixtures = [
    # Custom Fields for South African localization
    # Includes za_ prefixed fields and other za_local custom fields
    # Note: Fixtures are automatically imported from fixtures/ directory during installation
    # This filter is used when exporting fixtures
    {"dt": "Custom Field", "filters": [["name", "like", "%-za_%"]]},
    
    # Property Setters
    {"dt": "Property Setter", "filters": [["module", "in", ["SA Payroll", "SA Tax", "SA VAT", "COIDA"]]]},
    
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
before_install = "za_local.setup.install.before_install"
after_install = "za_local.setup.install.after_install"
after_migrate = ["za_local.setup.install.after_migrate"]

# Uninstallation
# ------------------
after_uninstall = "za_local.setup.uninstall.after_uninstall"

# Setup Wizard Integration
# ------------------
setup_wizard_requires = "assets/za_local/js/setup_wizard.js"
setup_wizard_stages = "za_local.setup.setup_wizard.get_sa_localization_stages"

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
# before_request / after_request not used
# after_request = ["za_local.utils.after_request"]

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
