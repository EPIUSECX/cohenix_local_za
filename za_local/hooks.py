from . import __version__ as app_version

app_name = "za_local"
app_title = "South African Localization"
app_publisher = "Cohenix"
app_description = "Comprehensive South African localization for ERPNext covering payroll, tax, VAT, and COIDA compliance"
app_email = "info@cohenix.com"
app_license = "mit"
app_version = app_version

# Apps
# ------------------
required_apps = ["frappe", "erpnext", "hrms"]

# Fixtures
# ------------------
fixtures = [
    # Custom Fields for South African localization
    {"dt": "Custom Field", "filters": [["name", "like", "%-za_%"]]},
    
    # Property Setters
    {"dt": "Property Setter", "filters": [["module", "in", ["SA Payroll", "SA Tax", "SA VAT", "COIDA"]]]},
]

# Includes in <head>
# ------------------
app_include_css = "/assets/za_local/css/za_local.css"

# Include JS in doctype views
# ------------------
doctype_js = {
    "Employee": "public/js/employee.js",
    "Payroll Entry": "public/js/payroll_entry.js",
    "Employee Benefit Claim": "public/js/employee_benefit_claim.js",
    "Salary Structure": "public/js/salary_structure.js",
    "COIDA Annual Return": "public/js/coida_annual_return.js",
    "Workplace Injury": "public/js/workplace_injury.js",
    "OID Claim": "public/js/oid_claim.js",
    "EMP501 Reconciliation": "public/js/emp501_reconciliation.js"
}

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

# DocType Class Overrides
# ------------------
# Override standard doctype classes with South African implementations
override_doctype_class = {
    "Salary Slip": "za_local.overrides.salary_slip.ZASalarySlip",
    "Payroll Entry": "za_local.overrides.payroll_entry.ZAPayrollEntry",
    "Additional Salary": "za_local.overrides.additional_salary.ZAAdditionalSalary"
}

# Document Events
# ------------------
# Hook on document methods and events
doc_events = {
    "Journal Entry": {
        "on_trash": "za_local.overrides.journal_entry.on_trash",
        "on_cancel": "za_local.overrides.journal_entry.on_cancel"
    }
}

# Monkey Patching
# ------------------
# Extend HRMS payroll entry functionality
from hrms.payroll.doctype.payroll_entry import payroll_entry as _payroll_entry
from za_local.overrides import payroll_entry as _za_payroll_entry
_payroll_entry.get_payroll_entry_bank_entries = _za_payroll_entry.get_payroll_entry_bank_entries

# Scheduled Tasks
# ------------------
# scheduler_events = {
#     "daily": [
#         "za_local.tasks.daily"
#     ],
#     "monthly": [
#         "za_local.tasks.monthly"
#     ]
# }

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
# before_request = ["za_local.utils.before_request"]
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
