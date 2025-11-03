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

# Setup Wizard Integration
# ------------------
setup_wizard_requires = "assets/za_local/js/setup_wizard.js"
setup_wizard_stages = "za_local.setup.setup_wizard.get_sa_localization_stages"

# DocType Class Overrides
# ------------------
# Override standard doctype classes with South African implementations
override_doctype_class = {
    "Salary Slip": "za_local.overrides.salary_slip.ZASalarySlip",
    "Payroll Entry": "za_local.overrides.payroll_entry.ZAPayrollEntry",
    "Additional Salary": "za_local.overrides.additional_salary.ZAAdditionalSalary",
    "Leave Application": "za_local.overrides.leave_application.ZALeaveApplication",
    "Employee Separation": "za_local.overrides.employee_separation.ZAEmployeeSeparation"
}

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
# Extend HRMS payroll entry functionality
from hrms.payroll.doctype.payroll_entry import payroll_entry as _payroll_entry
from za_local.overrides import payroll_entry as _za_payroll_entry
_payroll_entry.get_payroll_entry_bank_entries = _za_payroll_entry.get_payroll_entry_bank_entries

# Custom Records (DocType Links for Bidirectional Connections)
# ------------------
# Creates links between za_local DocTypes and standard DocTypes
# These appear in the "Connections" tab of documents
za_local_custom_records = [
	# Employee-related DocTypes (13 links)
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Tax & Compliance",
		"link_doctype": "Tax Directive",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Fringe Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Company Car Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Housing Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Low Interest Loan Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Cellphone Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Fuel Card Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Benefits",
		"link_doctype": "Bursary Benefit",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Payroll",
		"link_doctype": "Leave Encashment SA",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Separation",
		"link_doctype": "Employee Final Settlement",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Tax & Compliance",
		"link_doctype": "UIF U19 Declaration",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Payroll",
		"link_doctype": "NAEDO Deduction",
		"link_fieldname": "employee",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Employee",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Training & Development",
		"link_doctype": "Skills Development Record",
		"link_fieldname": "employee",
		"custom": 1,
	},
	
	# Company-related DocTypes (4 links)
	{
		"doctype": "DocType Link",
		"parent": "Company",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Payroll",
		"link_doctype": "Retirement Fund",
		"link_fieldname": "company",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Company",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Payroll",
		"link_doctype": "Travel Allowance Rate",
		"link_fieldname": "company",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Company",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Training & Development",
		"link_doctype": "Workplace Skills Plan",
		"link_fieldname": "company",
		"custom": 1,
	},
	{
		"doctype": "DocType Link",
		"parent": "Company",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Training & Development",
		"link_doctype": "Annual Training Report",
		"link_fieldname": "company",
		"custom": 1,
	},
	
	# Payroll Entry-related DocTypes (1 link)
	# Note: EMP201 Submission link removed - field doesn't exist in DocType
	{
		"doctype": "DocType Link",
		"parent": "Payroll Entry",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Payroll",
		"link_doctype": "Payroll Payment Batch",
		"link_fieldname": "payroll_entry",
		"custom": 1,
	},
	
	# Bargaining Council-related (1 link)
	{
		"doctype": "DocType Link",
		"parent": "Bargaining Council",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Sectoral Compliance",
		"link_doctype": "Industry Specific Contribution",
		"link_fieldname": "bargaining_council",
		"custom": 1,
	},
	
	# Expense Claim link to Business Trip
	{
		"doctype": "DocType Link",
		"parent": "Expense Claim",
		"parentfield": "links",
		"parenttype": "DocType",
		"group": "Travel",
		"link_doctype": "Business Trip",
		"link_fieldname": "expense_claim",
		"custom": 1,
	},
]

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
