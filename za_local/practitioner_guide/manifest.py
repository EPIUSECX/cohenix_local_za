"""Structure of the South African localisation Wiki guides.

This manifest is the single source of truth for the navigation trees. ``stage.py``
walks it to create/update each Wiki Space, its section groups, and the leaf pages.

Two guides are published as separate Wiki Spaces:

- **SA Practitioner Guide** (``/sa-guide``) — for the consultant/admin who installs
  and configures the localisation.
- **SA End-User Guide** (``/sa-user-guide``) — for the day-to-day user who captures
  transactions, runs payroll and pulls reports.

Routes are explicit and stable so staging is idempotent: a page is matched by its
route, and its markdown content is refreshed on every run (existing pages are
updated in place, not duplicated).

To add a page: drop a markdown file in ``content/`` and add an entry to the
relevant group's ``pages`` list. To add a section: append a new group dict. To add
a whole guide: append a new ``{"space": ..., "groups": [...]}`` dict to ``GUIDES``.
"""

# --- Practitioner guide -----------------------------------------------------

SPACE = {
	"space_name": "SA Practitioner Guide",
	"route": "sa-guide",
}

# Each group is a section in the sidebar. Each page is a leaf document whose
# body is loaded from content/<file>. Order in these lists drives sort_order.
GROUPS = [
	{
		"key": "getting-started",
		"title": "Getting Started",
		"pages": [
			{"slug": "overview", "title": "Overview & Architecture", "file": "01_overview.md"},
			{"slug": "prerequisites-installation", "title": "Prerequisites & Installation", "file": "02_prerequisites_installation.md"},
			{"slug": "choosing-your-track", "title": "Choosing Your Track", "file": "03_choosing_your_track.md"},
			{"slug": "post-install-verification", "title": "Post-Install Verification", "file": "04_post_install_verification.md"},
		],
	},
	{
		"key": "foundation-setup-both-tracks",
		"title": "Foundation Setup (Both Tracks)",
		"pages": [
			{"slug": "company-registration", "title": "Company & SA Registration Details", "file": "10_company_registration.md"},
			{"slug": "chart-of-accounts", "title": "Chart of Accounts", "file": "11_chart_of_accounts.md"},
			{"slug": "za-local-setup", "title": "ZA Local Setup & Fiscal Year", "file": "12_za_local_setup.md"},
		],
	},
	{
		"key": "erpnext-only-track-vat-documents",
		"title": "ERPNext-Only Track: VAT & Documents",
		"pages": [
			{"slug": "vat-settings", "title": "South Africa VAT Settings", "file": "20_vat_settings.md"},
			{"slug": "tax-templates-item-categories", "title": "Tax Templates & Item VAT Categories", "file": "21_tax_templates_item_categories.md"},
			{"slug": "customer-supplier-vat", "title": "Customer & Supplier VAT Fields", "file": "22_customer_supplier_vat.md"},
			{"slug": "print-formats", "title": "SA Print Formats & Tax Invoices", "file": "23_print_formats.md"},
			{"slug": "vat201-return", "title": "VAT201 Return Workflow & Reports", "file": "24_vat201_return.md"},
		],
	},
	{
		"key": "full-suite-payroll-foundations",
		"title": "Full Suite: Payroll Foundations",
		"pages": [
			{"slug": "payroll-prerequisites-settings", "title": "Payroll Prerequisites & Settings", "file": "30_payroll_prerequisites_settings.md"},
			{"slug": "statutory-rate-data", "title": "Statutory Rate Data", "file": "31_statutory_rate_data.md"},
			{"slug": "sars-payroll-codes", "title": "SARS Payroll Codes", "file": "32_sars_payroll_codes.md"},
			{"slug": "salary-components", "title": "Salary Components & SA Treatment", "file": "33_salary_components.md"},
			{"slug": "salary-structures", "title": "Salary Structures & Assignments", "file": "34_salary_structures.md"},
			{"slug": "retirement-and-benefits", "title": "Retirement Funds & Private Benefits", "file": "35_retirement_and_benefits.md"},
		],
	},
	{
		"key": "full-suite-employees",
		"title": "Full Suite: Employees",
		"pages": [
			{"slug": "employee-master", "title": "Employee Master & SA Details", "file": "40_employee_master.md"},
		],
	},
	{
		"key": "full-suite-running-payroll",
		"title": "Full Suite: Running Payroll",
		"pages": [
			{"slug": "payroll-entry-salary-slips", "title": "Payroll Entry & Salary Slips", "file": "50_payroll_entry.md"},
			{"slug": "understanding-the-salary-slip", "title": "Understanding the SA Salary Slip", "file": "51_understanding_salary_slip.md"},
			{"slug": "review-submit-post", "title": "Review, Submit & Post to the Ledger", "file": "52_review_submit_post.md"},
			{"slug": "payments-and-reports", "title": "Payroll Payments & Reports", "file": "53_payments_and_reports.md"},
		],
	},
	{
		"key": "full-suite-statutory-submissions",
		"title": "Full Suite: Statutory Submissions",
		"pages": [
			{"slug": "emp201", "title": "EMP201 Monthly Declaration", "file": "60_emp201.md"},
			{"slug": "irp5-it3", "title": "IRP5 / IT3(a) Certificates", "file": "61_irp5_it3.md"},
			{"slug": "emp501", "title": "EMP501 Annual Reconciliation", "file": "62_emp501.md"},
			{"slug": "directives-and-final-settlements", "title": "Tax Directives & Final Settlements", "file": "63_directives_final_settlements.md"},
		],
	},
	{
		"key": "sa-labour-coida",
		"title": "SA Labour & COIDA",
		"pages": [
			{"slug": "sa-labour", "title": "SA Labour: SETA, Skills, EE & Travel", "file": "70_sa_labour.md"},
			{"slug": "sa-coida", "title": "SA COIDA: Injuries, Claims & Annual Return", "file": "71_sa_coida.md"},
		],
	},
	{
		"key": "reference-operations",
		"title": "Reference & Operations",
		"pages": [
			{"slug": "custom-fields-reference", "title": "Custom Fields Reference", "file": "80_custom_fields_reference.md"},
			{"slug": "annual-statutory-update", "title": "Annual Statutory Update", "file": "81_annual_statutory_update.md"},
			{"slug": "troubleshooting-faq", "title": "Troubleshooting, FAQ & Glossary", "file": "82_troubleshooting_faq.md"},
		],
	},
]


# --- End-user guide ---------------------------------------------------------

USER_SPACE = {
	"space_name": "SA End-User Guide",
	"route": "sa-user-guide",
}

USER_GROUPS = [
	{
		"key": "getting-started",
		"title": "Getting Started",
		"pages": [
			{"slug": "welcome", "title": "Welcome & How to Use This Guide", "file": "u01_welcome.md"},
			{"slug": "navigating-workspaces", "title": "Finding Your Way: SA Workspaces", "file": "u02_navigating_workspaces.md"},
		],
	},
	{
		"key": "first-time-configuration",
		"title": "First-Time Configuration",
		"pages": [
			{"slug": "before-you-begin", "title": "Before You Begin: What Must Be Set Up", "file": "u10_before_you_begin.md"},
			{"slug": "confirm-company-settings", "title": "Confirm Company, VAT & Payroll Settings", "file": "u11_confirm_settings.md"},
			{"slug": "everyday-masters", "title": "Everyday Masters: Customers, Suppliers, Items, Employees", "file": "u12_everyday_masters.md"},
		],
	},
	{
		"key": "working-with-vat",
		"title": "Working with VAT",
		"pages": [
			{"slug": "sales-invoice-vat", "title": "Create a Sales Invoice with VAT", "file": "u20_sales_invoice_vat.md"},
			{"slug": "tax-invoices-credit-notes", "title": "Tax Invoices, Credit & Debit Notes", "file": "u21_tax_invoices_credit_notes.md"},
			{"slug": "purchases-input-vat", "title": "Purchase Invoices & Input VAT", "file": "u22_purchases_input_vat.md"},
			{"slug": "vat201-return", "title": "Prepare & Review the VAT201 Return", "file": "u23_vat201_return.md"},
		],
	},
	{
		"key": "running-payroll",
		"title": "Running Payroll",
		"pages": [
			{"slug": "monthly-payroll-run", "title": "Run a Monthly Payroll", "file": "u30_monthly_payroll_run.md"},
			{"slug": "reviewing-a-payslip", "title": "Reviewing a Salary Slip", "file": "u31_reviewing_a_payslip.md"},
			{"slug": "pay-employees", "title": "Pay Employees & Distribute Payslips", "file": "u32_pay_employees.md"},
			{"slug": "emp201-monthly", "title": "Submit the Monthly EMP201", "file": "u33_emp201_monthly.md"},
			{"slug": "year-end-irp5-emp501", "title": "Year-End: IRP5 & EMP501", "file": "u34_year_end.md"},
		],
	},
	{
		"key": "reports",
		"title": "Reports",
		"pages": [
			{"slug": "finding-reports", "title": "Finding & Running Reports", "file": "u40_finding_reports.md"},
			{"slug": "vat-reports", "title": "VAT Reports", "file": "u41_vat_reports.md"},
			{"slug": "payroll-reports", "title": "Payroll Reports", "file": "u42_payroll_reports.md"},
			{"slug": "labour-coida-reports", "title": "Labour & COIDA Reports", "file": "u43_labour_coida_reports.md"},
			{"slug": "exporting-printing", "title": "Exporting & Printing Reports", "file": "u44_exporting_printing.md"},
		],
	},
	{
		"key": "help",
		"title": "Help",
		"pages": [
			{"slug": "faq-glossary", "title": "FAQ & Glossary", "file": "u50_faq_glossary.md"},
		],
	},
]


# --- All guides staged by stage.py ------------------------------------------

PRACTITIONER_GUIDE = {"space": SPACE, "groups": GROUPS}
USER_GUIDE = {"space": USER_SPACE, "groups": USER_GROUPS}

GUIDES = [PRACTITIONER_GUIDE, USER_GUIDE]
