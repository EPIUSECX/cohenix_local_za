"""Structure of the SA Practitioner Guide Wiki Space.

The manifest is the single source of truth for the navigation tree. ``stage.py``
walks it to create/update the Wiki Space, its section groups, and the leaf pages.

Routes are explicit and stable so staging is idempotent: a page is matched by
its route, and its markdown content is refreshed on every run.

To add a page: drop a markdown file in ``content/`` and add an entry to the
relevant group's ``pages`` list. To add a section: append a new group dict.
"""

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
