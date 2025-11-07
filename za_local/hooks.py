from . import __version__ as app_version

app_name = "za_local"
app_title = "South Africa"
app_publisher = "Cohenix"
app_description = "Comprehensive South African localization for ERPNext covering payroll, tax, VAT, and COIDA compliance"
app_email = "info@cohenix.com"
app_license = "mit"
app_version = app_version

# App logo for toolbar and app switcher
# Path must be under public/ to be served as /assets/za_local/...
app_logo_url = "/assets/za_local/images/sa_map.jpg"

# Apps
# ------------------
# Note: HRMS is optional - za_local works with or without HRMS
# If HRMS is not installed, payroll/HR features will be disabled
required_apps = ["frappe", "erpnext"]

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
    
    # SA Payroll Workspace
    {"dt": "Workspace", "filters": [["name", "=", "SA Payroll"]]},
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
    "EMP501 Reconciliation": "public/js/emp501_reconciliation.js"
}

# HRMS-dependent JS files (added conditionally)
def get_hrms_doctype_js():
	"""Conditionally add HRMS-dependent doctype JS files"""
	from za_local.utils.hrms_detection import is_hrms_installed
	hrms_js = {}
	if is_hrms_installed():
		hrms_js.update({
			"Employee": "public/js/employee.js",
			"Payroll Entry": "public/js/payroll_entry.js",
			"Employee Benefit Claim": "public/js/employee_benefit_claim.js",
			"Salary Structure": "public/js/salary_structure.js",
			"Salary Structure Assignment": "public/js/salary_structure_assignment.js",
		})
	return hrms_js

# Merge HRMS-dependent JS if HRMS is installed
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

# DocType Class Overrides
# ------------------
# Override standard doctype classes with South African implementations
# Only register HRMS overrides if HRMS is installed
def get_override_doctype_class():
	"""Get override doctype classes conditionally based on HRMS availability"""
	from za_local.utils.hrms_detection import is_hrms_installed
	overrides = {}
	if is_hrms_installed():
		overrides.update({
    "Salary Slip": "za_local.overrides.salary_slip.ZASalarySlip",
    "Payroll Entry": "za_local.overrides.payroll_entry.ZAPayrollEntry",
    "Additional Salary": "za_local.overrides.additional_salary.ZAAdditionalSalary",
    "Leave Application": "za_local.overrides.leave_application.ZALeaveApplication",
    "Employee Separation": "za_local.overrides.employee_separation.ZAEmployeeSeparation"
		})
	return overrides

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
# Extend HRMS payroll entry functionality (only if HRMS is installed)
def setup_hrms_monkey_patches():
	"""Conditionally setup HRMS monkey patches"""
	from za_local.utils.hrms_detection import is_hrms_installed
	if is_hrms_installed():
		try:
			from hrms.payroll.doctype.payroll_entry import payroll_entry as _payroll_entry
			from za_local.overrides import payroll_entry as _za_payroll_entry
			_payroll_entry.get_payroll_entry_bank_entries = _za_payroll_entry.get_payroll_entry_bank_entries
		except ImportError:
			# HRMS not fully installed or version mismatch
			pass

# Setup monkey patches after hooks are loaded
setup_hrms_monkey_patches()

# Custom Records (DocType Links for Bidirectional Connections)
# ------------------
# Creates links between za_local DocTypes and standard DocTypes
# These appear in the "Connections" tab of documents
# HRMS-dependent links are filtered conditionally
def get_za_local_custom_records():
	"""Get custom records conditionally based on HRMS availability"""
	from za_local.utils.hrms_detection import is_hrms_installed
	hrms_installed = is_hrms_installed()
	
	records = [
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
	
	# Filter out HRMS-dependent links if HRMS is not installed
	if not hrms_installed:
		# HRMS-dependent parent doctypes
		hrms_parents = ["Employee", "Payroll Entry", "Expense Claim"]
		records = [r for r in records if r.get("parent") not in hrms_parents]
	
	return records

# Assign custom records conditionally
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
