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
    "Employee Separation": "za_local.overrides.employee_separation.ZAEmployeeSeparation",
    "Salary Structure Assignment": "za_local.overrides.salary_structure_assignment.ZASalaryStructureAssignment"
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
			from hrms.payroll.doctype.payroll_entry import payroll_entry as _payroll_entry  # type: ignore
			from za_local.overrides import payroll_entry as _za_payroll_entry
			_payroll_entry.get_payroll_entry_bank_entries = _za_payroll_entry.get_payroll_entry_bank_entries
		except ImportError:
			# HRMS not fully installed or version mismatch
			pass

# Setup monkey patches after hooks are loaded
setup_hrms_monkey_patches()

# Chart of Accounts Integration
# ------------------
# 1) Extend ERPNext's chart discovery to include South African Chart of Accounts
# 2) Make financial report template sync robust for custom ZA charts (avoid setup failure)

def extend_charts_for_country():
	"""Extend ERPNext's chart discovery to include za_local charts."""
	try:
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore
		from za_local.accounts.setup_chart import get_chart_template_name
		from functools import wraps
		import frappe  # type: ignore

		# Check if function exists and hasn't been wrapped already
		if not hasattr(coa_module, "get_charts_for_country"):
			return

		# Avoid double wrapping
		if getattr(coa_module.get_charts_for_country, "_za_wrapped", False):
			return

		original_get_charts = coa_module.get_charts_for_country

		@wraps(original_get_charts)
		def get_charts_for_country_with_za(country, with_standard: bool = False):
			"""Return core charts plus ZA template for South Africa."""
			try:
				charts = original_get_charts(country, with_standard)
			except Exception:
				# Hard fallback to original behaviour if wrapper misbehaves
				try:
					return original_get_charts(country, with_standard)
				except Exception:
					return []

			# Inject ZA chart name only for South Africa
			if country == "South Africa" and isinstance(charts, list):
				try:
					chart_name = get_chart_template_name()
					if chart_name and chart_name not in charts:
						# Add at the beginning so it's the default suggestion
						charts.insert(0, chart_name)
				except Exception as e:
					try:
						frappe.log_error(f"Could not load ZA chart template name: {e}", "ZA Chart Extension")
					except Exception:
						# Logging failure should not break chart discovery
						pass

			return charts

		# Mark as wrapped to avoid double wrapping
		get_charts_for_country_with_za._za_wrapped = True
		coa_module.get_charts_for_country = get_charts_for_country_with_za
	except Exception:
		# Chart discovery extension is optional, never break hooks loading
		pass


def extend_chart_loader():
	"""
	Extend ERPNext's get_chart so ZA template JSON can be used as a full chart.

	When the selected chart template name matches the ZA chart template, we
	load the JSON from za_local and return its `tree` so that
	`create_charts` imports the entire South African chart as the company's
	Chart of Accounts (full replacement pattern).
	"""

	try:
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore
		from za_local.accounts.setup_chart import get_chart_template_name, get_za_chart_tree
		from functools import wraps

		if not hasattr(coa_module, "get_chart"):
			return

		# Avoid double wrapping
		if getattr(coa_module.get_chart, "_za_wrapped", False):
			return

		original_get_chart = coa_module.get_chart
		za_template_name = get_chart_template_name()

		@wraps(original_get_chart)
		def get_chart_with_za(chart_template, existing_company=None):
			"""
			If chart_template is ZA template name, return ZA JSON tree;
			otherwise delegate to core get_chart.
			"""
			try:
				if za_template_name and chart_template == za_template_name:
					tree = get_za_chart_tree()
					if tree:
						return tree
			except Exception:
				# Silently ignore and fall through to original_get_chart
				pass

			return original_get_chart(chart_template, existing_company)

		get_chart_with_za._za_wrapped = True
		coa_module.get_chart = get_chart_with_za
	except Exception:
		# Loader extension is optional, never break hooks loading
		pass

def patch_financial_report_templates_sync():
	"""Monkey patch sync_financial_report_templates to tolerate unknown COA names.

	When a custom ZA chart template is selected, ERPNext's default implementation
	calls get_chart(chart_of_accounts) and assumes it returns a dict. For
	non-ERPNext charts (e.g. from za_local), this returns None which causes:

	    AttributeError: 'NoneType' object has no attribute 'get'

	This crashes Company creation during setup, so no Company is saved.

	This patch safely handles the "chart not found" case by:
	- Treating it as if disable_default_financial_report_template == False
	- Still syncing default templates for all installed apps
	"""

	try:
		from erpnext.accounts.doctype.financial_report_template import financial_report_template as frt_module  # type: ignore
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore
		import frappe  # local import to avoid circular issues

		if not hasattr(frt_module, "sync_financial_report_templates"):
			return

		# Avoid double patching
		if getattr(frt_module.sync_financial_report_templates, "_za_patched", False):
			return

		original_sync = frt_module.sync_financial_report_templates

		def safe_sync_financial_report_templates(chart_of_accounts, existing_company=None):
			# For existing companies, keep behaviour unchanged
			if existing_company:
				return original_sync(chart_of_accounts, existing_company)

			disable_default_financial_report_template = False

			if chart_of_accounts:
				try:
					coa = coa_module.get_chart(chart_of_accounts)
				except Exception:
					coa = None

				# Only look for override flag when we have a valid chart dict
				if isinstance(coa, dict):
					disable_default_financial_report_template = coa.get(
						"disable_default_financial_report_template", False
					)

			installed_apps = frappe.get_installed_apps()

			for app in installed_apps:
				# If a regional chart disables ERPNext defaults, honour that
				if disable_default_financial_report_template and app == "erpnext":
					continue

				frt_module._sync_templates_for(app)

		safe_sync_financial_report_templates._za_patched = True
		frt_module.sync_financial_report_templates = safe_sync_financial_report_templates
	except Exception:
		# Never break setup due to patching issues
		try:
			import frappe
			frappe.log_error("Failed to patch sync_financial_report_templates", "ZA Local Setup")
		except Exception:
			pass


# Apply monkey patches after hooks are loaded
extend_charts_for_country()
extend_chart_loader()
patch_financial_report_templates_sync()

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

# Whitelisted Method Overrides
# ------------------
# Provide overrides for core methods so we can hook into setup wizard flows
override_whitelisted_methods = {
	# ERPNext Chart of Accounts discovery used during Company / Setup Wizard
	# Core method is not whitelisted in this ERPNext version, so we expose a
	# safe wrapper that delegates to the (possibly monkey-patched) implementation.
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country":
		"za_local.accounts.setup_chart.get_charts_for_country_with_za",
}

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
