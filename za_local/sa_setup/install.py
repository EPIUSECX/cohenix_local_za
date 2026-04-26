"""
Installation and Setup Functions for ZA Local

This module handles installation, uninstallation, and migration setup
for the South African localization app.
"""

import copy
import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils.fixtures import import_fixtures

from za_local.sa_setup.custom_fields import setup_custom_fields
from za_local.sa_setup.monkey_patches import setup_all_monkey_patches
from za_local.sa_setup.property_setters import apply_property_setters
from za_local.sa_vat.setup import (
	ensure_vat_custom_fields,
	migrate_legacy_vat_account_rows,
	seed_vat_vendor_types,
)
from za_local.utils.hrms_detection import is_hrms_installed

UIF_FORMULA = "(gross_pay * 0.01) if (gross_pay * 0.01) <= 177.12 else 177.12"
SDL_FORMULA = "gross_pay * 0.01"

DEFAULT_SARS_PAYROLL_CODES = [
	{
		"code": "3601",
		"description": "Income - Gross Remuneration",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 10,
	},
	{
		"code": "3605",
		"description": "Income - Annual Payment",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 20,
	},
	{
		"code": "3607",
		"description": "Income - Overtime",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 30,
	},
	{
		"code": "3701",
		"description": "Income - Travel Allowance",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 40,
	},
	{
		"code": "3702",
		"description": "Income - Other Allowances",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 50,
	},
	{
		"code": "3704",
		"description": "Income - Subsistence Allowance",
		"category": "Income",
		"tax_treatment": "Non-Taxable",
		"print_sequence": 60,
	},
	{
		"code": "3713",
		"description": "Income - Uniform Allowance",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 70,
	},
	{
		"code": "3802",
		"description": "Income - Use of Motor Vehicle",
		"category": "Income",
		"tax_treatment": "Taxable",
		"print_sequence": 80,
	},
	{
		"code": "4001",
		"description": "Deduction - Pension / Provident Fund",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 100,
	},
	{
		"code": "4005",
		"description": "Deduction - Medical Scheme Fees",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 110,
	},
	{
		"code": "4006",
		"description": "Deduction - Retirement Annuity Fund",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 120,
	},
	{
		"code": "4007",
		"description": "Deduction - Group Life Insurance",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 130,
	},
	{
		"code": "4008",
		"description": "Deduction - Disability Insurance",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 140,
	},
	{
		"code": "4010",
		"description": "Deduction - Loan Repayment",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 150,
	},
	{
		"code": "4102",
		"description": "Deduction - PAYE",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 160,
	},
	{
		"code": "4116",
		"description": "Tax Credit - Medical Scheme Fees Tax Credit",
		"category": "Tax Credit",
		"tax_treatment": "Reference",
		"print_sequence": 170,
	},
	{
		"code": "4118",
		"description": "Tax Credit - Employment Tax Incentive",
		"category": "Tax Credit",
		"tax_treatment": "Reference",
		"print_sequence": 175,
	},
	{
		"code": "4120",
		"description": "Tax Credit - Additional Medical Expenses Tax Credit",
		"category": "Tax Credit",
		"tax_treatment": "Reference",
		"print_sequence": 180,
	},
	{
		"code": "4141",
		"description": "Deduction / Contribution - UIF",
		"category": "Deduction",
		"tax_treatment": "Reference",
		"print_sequence": 190,
	},
	{
		"code": "4142",
		"description": "Employer Contribution - SDL",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 200,
	},
	{
		"code": "4472",
		"description": "Employer Contribution - Pension Fund",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 210,
	},
	{
		"code": "4474",
		"description": "Employer Contribution - Medical Scheme",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 220,
	},
	{
		"code": "4475",
		"description": "Employer Contribution - Group Life Insurance",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 230,
	},
	{
		"code": "4476",
		"description": "Employer Contribution - Disability Insurance",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 240,
	},
	{
		"code": "4477",
		"description": "Employer Contribution - Funeral Benefit",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 250,
	},
	{
		"code": "4497",
		"description": "Employer Contribution - Other Employer Contributions",
		"category": "Employer Contribution",
		"tax_treatment": "Reference",
		"print_sequence": 260,
	},
]

DEFAULT_SALARY_COMPONENT_SARS_CODES = {
	"Basic Salary": "3601",
	"Basic": "3601",
	"Gross Salary": "3601",
	"Bonus": "3605",
	"Annual Bonus": "3605",
	"Performance Bonus": "3605",
	"Commission": "3605",
	"13th Cheque": "3605",
	"Overtime": "3607",
	"Travel Allowance": "3701",
	"Transport Allowance": "3701",
	"Housing Allowance": "3702",
	"Accommodation Allowance": "3702",
	"Cell Phone Allowance": "3702",
	"Subsistence Allowance": "3704",
	"Business Reimbursement": "3704",
	"Uniform Allowance": "3713",
	"Company Car Benefit": "3802",
	"Use of Motor Vehicle": "3802",
	"PAYE": "4102",
	"Income Tax": "4102",
	"Employment Tax Incentive": "4118",
	"ETI": "4118",
	"UIF Employee Contribution": "4141",
	"UIF Employer Contribution": "4141",
	"UIF": "4141",
	"SDL Contribution": "4142",
	"SDL": "4142",
	"Skills Development Levy": "4142",
	"Pension Fund": "4001",
	"Provident Fund": "4001",
	"Retirement Fund": "4001",
	"Retirement Annuity Fund": "4006",
	"Medical Aid": "4005",
	"Medical Scheme": "4005",
	"Medical Insurance": "4005",
	"Group Life Insurance": "4007",
	"Disability Insurance": "4008",
	"Loan Repayment": "4010",
	"Staff Loan Repayment": "4010",
}

DEFAULT_IRP5_EXCLUDED_SALARY_COMPONENTS = {
	"Garnishee Order",
	"Union Subscription",
}


def sync_za_local():
	"""
	Unified sync: import standard fixtures, then apply centralized custom-field setup.

	Custom fields, cleanup, and custom DocType Links live in ``custom_fields.py``.
	Property setters are applied separately from ``property_setters.py`` so there is a
	single authoritative source for standard DocType overrides.
	"""
	import_fixtures("za_local")
	setup_custom_fields()
	ensure_vat_custom_fields()


def before_install():
	"""
	Run before app installation.

	Creates essential DocTypes that are required before the app is fully installed:
	- Company Contribution (child table for Salary Structure) - only if HRMS is installed
	"""
	# Only create Company Contribution if HRMS is available
	# This is called during install, so we check if HRMS will be available
	try:
		create_company_contribution_doctype()
	except Exception as e:
		# Don't fail installation if this can't be created
		print(f"  ! Could not create Company Contribution DocType: {e}")
		print("  Note: This is only needed when HRMS is installed")


def after_install():
	"""
	Run after app installation.

	Unified setup order (sync_za_local): fixtures → custom fields + property setters → custom records.
	Then: make_property_setters, monkey patches, default data, master data, workspace/module visibility.

	Note: All setup tasks are handled here, not in patches.txt.
	Patches should only be used for one-time data migrations, not setup tasks.
	"""
	cleanup_invalid_doctype_links()
	sync_za_local()  # fixtures → custom fields (cleanup + property setters) → custom records
	make_property_setters()
	setup_all_monkey_patches()
	setup_default_data()
	seed_vat_vendor_types()
	migrate_legacy_vat_account_rows()
	apply_statutory_formulas()
	import_master_data()
	seed_sars_payroll_codes()
	migrate_irp5_legacy_source_fields()
	cleanup_orphaned_workspace_records()
	ensure_sa_localisation_module_def()
	ensure_modules_visible()
	set_accounts_settings_for_za_vat()
	migrate_workspace_sa_localisation_to_sa_overview()
	sync_sa_workspaces()
	rebuild_za_local_workspace_sidebars()
	sync_za_local_desktop_icons()
	ensure_sa_payroll_print_formats()
	frappe.db.commit()
	print("\n" + "=" * 80)
	print("South African Localization installed successfully!")
	print("=" * 80)
	print("\nNext steps:")
	print("1. Configure Company SA registration numbers")
	print("2. Set up Payroll Settings with SA statutory components")
	print("3. Configure ETI Slabs and Tax Rebates")
	print("4. Set up COIDA and VAT settings if applicable")
	print("5. Configure Business Trip Settings for travel allowances")
	print("=" * 80 + "\n")


def after_migrate():
	"""
	Run after migrations.

	Same sync order as install (sync_za_local): fixtures → custom fields + property setters → custom records.
	Then: make_property_setters, monkey patches, statutory formulas, workspace/module visibility.
	"""
	cleanup_invalid_doctype_links()
	sync_za_local()  # fixtures → custom fields (cleanup + property setters) → custom records
	make_property_setters()
	setup_all_monkey_patches()
	apply_statutory_formulas()
	seed_vat_vendor_types()
	migrate_legacy_vat_account_rows()
	seed_sars_payroll_codes()
	migrate_irp5_legacy_source_fields()
	cleanup_orphaned_workspace_records()
	ensure_sa_localisation_module_def()
	ensure_modules_visible()
	set_accounts_settings_for_za_vat()
	migrate_workspace_sa_localisation_to_sa_overview()
	sync_sa_workspaces()
	rebuild_za_local_workspace_sidebars()
	sync_za_local_desktop_icons()
	ensure_sa_payroll_print_formats()
	frappe.db.commit()


def set_accounts_settings_for_za_vat():
	"""
	Set Accounts Settings for ZA VAT so tax rows come from document templates only.
	- add_taxes_from_taxes_and_charges_template = 1: Sales/Purchase Templates define tax rows (VAT Collected / VAT Paid).
	- add_taxes_from_item_tax_template = 0: Item templates only affect rate per item, not which accounts appear.
	This prevents VAT Collected (sales) from appearing on Purchase Invoices when items have a Sales-oriented template.
	"""
	try:
		if not frappe.db.table_exists("Accounts Settings"):
			return
		settings = frappe.get_single("Accounts Settings")
		settings.add_taxes_from_taxes_and_charges_template = 1
		settings.add_taxes_from_item_tax_template = 0
		settings.flags.ignore_permissions = True
		settings.save()
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="ZA Local: Set Accounts Settings for VAT",
		)


def cleanup_invalid_doctype_links():
	"""
	Remove invalid DocType Links from the database.

	These links may exist from previous installations and cause
	validation errors when creating property setters.
	"""
	print("\nCleaning up invalid DocType Links...")

	# List of invalid links to remove: (parent_doctype, link_doctype, link_fieldname)
	invalid_links = [
		("Payroll Entry", "EMP201 Submission", "payroll_entry"),
		("IRP5 Certificate", "EMP501 Reconciliation", "emp501_reconciliation"),
	]

	for parent_dt, link_dt, link_field in invalid_links:
		# Find and delete invalid links
		links_to_delete = frappe.db.sql(
			"""
			SELECT name
			FROM `tabDocType Link`
			WHERE parent = %s
				AND link_doctype = %s
				AND link_fieldname = %s
		""",
			(parent_dt, link_dt, link_field),
			as_dict=1,
		)

		for link in links_to_delete:
			try:
				frappe.delete_doc("DocType Link", link.name, force=True, ignore_permissions=True)
				print(f"  ✓ Removed invalid link: {parent_dt} → {link_dt}.{link_field}")
			except Exception as e:
				print(f"  ! Error removing link {link.name}: {e}")

		frappe.db.commit()
		print("  ✓ Invalid DocType Links cleaned up\n")


def ensure_sa_payroll_print_formats():
	"""Keep South African print formats owned by za_local and available after migrate."""
	if not frappe.db.table_exists("Print Format"):
		return

	print("\nEnsuring South African print formats...")

	print_formats = {
		"SA Sales Invoice": {
			"module": "SA VAT",
			"doc_type": "Sales Invoice",
			"html": '{% set za_print_title = "TAX INVOICE" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Bill To" %}\n{% set za_footer_text = "System-generated South African tax invoice. Sequential document numbering and supporting records should be retained for the statutory retention period." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Full Tax Invoice": {
			"module": "SA VAT",
			"doc_type": "Sales Invoice",
			"html": '{% set za_print_title = "FULL TAX INVOICE" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Bill To" %}\n{% set za_footer_text = "Full South African tax invoice for taxable supplies above the abridged invoice threshold. Verify customer VAT registration details where required." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Abridged Tax Invoice": {
			"module": "SA VAT",
			"doc_type": "Sales Invoice",
			"html": '{% set za_print_title = "ABRIDGED TAX INVOICE" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Bill To" %}\n{% set za_footer_text = "Abridged South African tax invoice. Use for supplies within the SARS abridged-invoice threshold and retain supporting records." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Credit Note": {
			"module": "SA VAT",
			"doc_type": "Sales Invoice",
			"html": '{% set za_print_title = "CREDIT NOTE" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Credit To" %}\n{% set za_footer_text = "South African credit note. Retain with the original tax invoice and supporting adjustment records." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Delivery Note": {
			"module": "SA VAT",
			"doc_type": "Delivery Note",
			"html": '{% set za_print_title = "DELIVERY NOTE" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Deliver To" %}\n{% set za_footer_text = "South African delivery note. This is not a tax invoice unless explicitly stated and should be retained with the related transaction records." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Payment Entry": {
			"module": "SA VAT",
			"doc_type": "Payment Entry",
			"html": '{% include "za_local/templates/print_format/sa_payment_entry.html" %}',
		},
		"SA Purchase Invoice": {
			"module": "SA VAT",
			"doc_type": "Purchase Invoice",
			"html": '{% set za_print_title = "PURCHASE INVOICE" %}\n{% set za_party_doctype = "Supplier" %}\n{% set za_party_label = "Supplier" %}\n{% set za_footer_text = "South African purchase invoice record. Retain supplier tax invoice evidence for VAT input-claim support." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Debit Note": {
			"module": "SA VAT",
			"doc_type": "Purchase Invoice",
			"html": '{% set za_print_title = "DEBIT NOTE" %}\n{% set za_party_doctype = "Supplier" %}\n{% set za_party_label = "Supplier" %}\n{% set za_footer_text = "South African debit note. Retain with the original supplier tax invoice and supporting adjustment records." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Purchase Order": {
			"module": "SA VAT",
			"doc_type": "Purchase Order",
			"html": '{% set za_print_title = "PURCHASE ORDER" %}\n{% set za_party_doctype = "Supplier" %}\n{% set za_party_label = "Supplier" %}\n{% set za_footer_text = "South African purchase order. This is not a tax invoice and does not support VAT input claims without supplier tax invoice evidence." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Quotation": {
			"module": "SA VAT",
			"doc_type": "Quotation",
			"html": '{% set za_print_title = "QUOTATION" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Quoted To" %}\n{% set za_footer_text = "South African quotation. This is not a tax invoice and should be converted to a tax invoice once goods or services are supplied." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"SA Sales Order": {
			"module": "SA VAT",
			"doc_type": "Sales Order",
			"html": '{% set za_print_title = "SALES ORDER" %}\n{% set za_party_doctype = "Customer" %}\n{% set za_party_label = "Customer" %}\n{% set za_footer_text = "South African sales order. This is not a tax invoice and should be retained with the related fulfilment and invoice records." %}\n{% include "za_local/templates/print_format/sa_commercial_document.html" %}',
		},
		"IRP5 Employee Certificate": {
			"module": "SA Payroll",
			"doc_type": "IRP5 Certificate",
			"html": '{% include "za_local/templates/print_format/irp5_employee_certificate.html" %}',
		},
		"IRP5-it3 Certificate": {
			"module": "SA Payroll",
			"doc_type": "IRP5 Certificate",
			"html": '{% include "za_local/templates/print_format/irp5_employee_certificate.html" %}',
		},
		"SA Salary Slip": {
			"module": "SA Payroll",
			"doc_type": "Salary Slip",
			"html": '{% include "za_local/templates/print_format/sa_salary_slip.html" %}',
		},
	}

	for name, values in print_formats.items():
		if values["doc_type"] == "Salary Slip" and not is_hrms_installed():
			continue
		if values["doc_type"] == "Salary Slip" and not frappe.db.exists("DocType", "Salary Slip"):
			continue

		if frappe.db.exists("Print Format", name):
			frappe.db.set_value(
				"Print Format",
				name,
				{
					"module": values["module"],
					"doc_type": values["doc_type"],
					"custom_format": 1,
					"standard": "Yes",
					"disabled": 0,
					"print_format_type": "Jinja",
					"html": values["html"],
				},
			)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Print Format",
					"name": name,
					"module": values["module"],
					"doc_type": values["doc_type"],
					"custom_format": 1,
					"standard": "Yes",
					"disabled": 0,
					"print_format_type": "Jinja",
					"html": values["html"],
				}
			)
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)

	if frappe.db.exists("DocType", "IRP5 Certificate"):
		frappe.db.set_value("DocType", "IRP5 Certificate", "default_print_format", "IRP5 Employee Certificate")
	if is_hrms_installed() and frappe.db.exists("DocType", "Salary Slip") and frappe.db.exists("Print Format", "SA Salary Slip"):
		frappe.db.set_value("DocType", "Salary Slip", "default_print_format", "SA Salary Slip")

	print("  ✓ South African print formats are available")


def cleanup_orphaned_workspace_records():
	"""
	Historical no-op: we intentionally keep za_local workspaces and desktop
	icons so that SA Localisation and related workspaces remain available.
	Left in place so older migrations that still call this function continue
	to succeed without modifying workspace data.
	"""
	print("\nSkipping cleanup of za_local workspaces and desktop icons (kept by design).\n")


def ensure_sa_localisation_module_def():
	"""
	Desk-only module from modules.txt: Frappe may not create Module Def until
	content sync runs; Workspace validation requires the module to exist.
	"""
	if not frappe.db.table_exists("Module Def"):
		return
	if frappe.db.exists("Module Def", "SA Localisation"):
		return
	try:
		m = frappe.new_doc("Module Def")
		m.module_name = "SA Localisation"
		m.app_name = "za_local"
		m.custom = 0
		m.flags.ignore_permissions = True
		m.insert(ignore_permissions=True)
		frappe.clear_cache()
		print("  ✓ Created Module Def 'SA Localisation'")
	except Exception as e:
		print(f"  ! Could not create Module Def SA Localisation: {e}")


def migrate_workspace_sa_localisation_to_sa_overview():
	"""
	Desktop Icon autoname is `label`: App tile uses label 'SA Localisation' (app_title)
	and cannot share the same name as the Link icon for the hub workspace.
	Rename hub workspace and related desk rows to 'SA Overview'.
	"""
	if not frappe.db.table_exists("Workspace"):
		return
	if not frappe.db.exists("Workspace", "SA Localisation"):
		return
	if frappe.db.exists("Workspace", "SA Overview"):
		print("  ⊙ SA Overview workspace already exists; skipping SA Localisation → SA Overview rename")
		return
	try:
		from frappe.model.rename_doc import rename_doc

		rename_doc("Workspace", "SA Localisation", "SA Overview", force=True, ignore_permissions=True)

		frappe.db.sql(
			"UPDATE `tabDesktop Icon` SET link_to=%s WHERE link_to=%s",
			("SA Overview", "SA Localisation"),
		)

		if frappe.db.table_exists("Workspace Sidebar Item"):
			frappe.db.sql(
				"""UPDATE `tabWorkspace Sidebar Item` SET link_to=%s
				WHERE link_type='Workspace' AND link_to=%s""",
				("SA Overview", "SA Localisation"),
			)

		if frappe.db.exists("Workspace Sidebar", "SA Localisation"):
			rename_doc(
				"Workspace Sidebar",
				"SA Localisation",
				"SA Overview",
				force=True,
				ignore_permissions=True,
			)

		for icon_name in frappe.get_all(
			"Desktop Icon",
			filters={"label": "SA Localisation", "icon_type": "Link"},
			pluck="name",
		):
			rename_doc("Desktop Icon", icon_name, "SA Overview", force=True, ignore_permissions=True)

		print("  ✓ Renamed hub workspace SA Localisation → SA Overview (desktop icon PK fix)")
	except Exception as e:
		print(f"  ! Could not rename hub workspace to SA Overview: {e}")


def _strip_workspace_content_chart_blocks(data: dict, allowed_chart_names: set | None) -> None:
	"""
	Remove chart blocks from Workspace.content JSON.
	If allowed_chart_names is None, drop every chart block.
	If a set (possibly empty), keep only blocks whose chart_name is in the set.
	"""
	raw = data.get("content")
	if not raw:
		return
	try:
		blocks = json.loads(raw)
	except Exception:
		return
	if not isinstance(blocks, list):
		return
	out = []
	for block in blocks:
		if block.get("type") != "chart":
			out.append(block)
			continue
		name = (block.get("data") or {}).get("chart_name")
		if allowed_chart_names is None:
			continue
		if name in allowed_chart_names:
			out.append(block)
	data["content"] = json.dumps(out)


def _sanitize_workspace_dashboard_charts(data: dict) -> None:
	"""
	In-place: drop Workspace.charts rows when the Dashboard Chart doc is missing.
	Also remove matching chart widgets from content so validate/save does not fail.

	Sites without HRMS often lack chart \"Outgoing Salary\"; without this, sync_sa_workspaces
	can fail to create or update SA Payroll and the workspace disappears from the desk.
	"""
	charts = data.get("charts")
	if not charts:
		return

	if not frappe.db.table_exists("Dashboard Chart"):
		data["charts"] = []
		_strip_workspace_content_chart_blocks(data, None)
		return

	kept = []
	for row in charts:
		cn = row.get("chart_name")
		if cn and frappe.db.exists("Dashboard Chart", cn):
			kept.append(row)

	if len(kept) == len(charts):
		return

	data["charts"] = kept
	allowed = {row.get("chart_name") for row in kept if row.get("chart_name")}
	_strip_workspace_content_chart_blocks(data, allowed)


def sync_sa_workspaces():
	"""
	Ensure ZA Local workspaces defined in the app (e.g. SA Localisation, SA VAT)
	are present in the Workspace table.

	Frappe v16 does not expose a generic sync_workspaces helper, so we load the
	app's workspace JSON files directly and upsert the corresponding Workspace
	records in the current site.
	"""
	from pathlib import Path

	def _upsert_workspace(json_path: Path):
		if not json_path.exists():
			return

		try:
			with open(json_path) as f:
				data = json.load(f)
		except Exception as e:
			print(f"  ! Could not read workspace definition {json_path}: {e}")
			return

		if not isinstance(data, dict) or data.get("doctype") != "Workspace":
			return

		# Use the file's name/title as the workspace key
		ws_name = data.get("name") or data.get("title")
		if not ws_name:
			return

		data = copy.deepcopy(data)
		_sanitize_workspace_dashboard_charts(data)

		immutable_keys = {
			"name",
			"doctype",
			"creation",
			"modified",
			"owner",
			"modified_by",
			"docstatus",
			"idx",
		}

		if frappe.db.exists("Workspace", ws_name):
			try:
				doc = frappe.get_doc("Workspace", ws_name)
				for key, value in data.items():
					if key in immutable_keys:
						continue
					doc.set(key, value)
				doc.flags.ignore_permissions = True
				doc.save()
				print(f"  ✓ Updated Workspace from file: {ws_name}")
			except Exception as e:
				print(f"  ! Could not update Workspace {ws_name}: {e}")
		else:
			try:
				doc = frappe.get_doc(data)
				doc.insert(ignore_permissions=True)
				print(f"  ✓ Created Workspace from file: {ws_name}")
			except Exception as e:
				print(f"  ! Could not create Workspace {ws_name}: {e}")

	try:
		base = Path(frappe.get_app_path("za_local"))
		for rel in (
			base / "sa_setup" / "workspace" / "sa_localisation" / "sa_localisation.json",
			base / "sa_vat" / "workspace" / "sa_vat" / "sa_vat.json",
			base / "sa_payroll" / "workspace" / "sa_payroll" / "sa_payroll.json",
			base / "sa_labour" / "workspace" / "sa_labour" / "sa_labour.json",
			base / "sa_coida" / "workspace" / "sa_coida" / "sa_coida.json",
		):
			_upsert_workspace(rel)
		frappe.db.commit()
	except Exception as e:
		# Do not fail install/migrate if workspace sync has issues
		print(f"  ! Could not sync za_local workspaces: {e}")


# Lucide icon names for Workspace Sidebar rows (match Frappe HR Payroll sidebar style).
_SIDEBAR_DOCTYPE_ICONS = {
	"Payroll Entry": "banknote-arrow-up",
	"Salary Structure Assignment": "loan",
	"Salary Slip": "accounting",
	"Additional Salary": "piggy-bank",
	"Salary Withholding": "banknote-x",
	"Payroll Settings": "settings",
	"Payroll Period": "calendar",
	"Income Tax Slab": "percent",
	"Salary Component": "package",
	"Salary Structure": "layers",
	"Journal Entry": "book-open",
	"Payment Entry": "wallet",
	"ZA Local Setup": "settings",
	"EMP201 Submission": "file-spreadsheet",
	"EMP501 Reconciliation": "clipboard-list",
	"Tax Rebates and Medical Tax Credit": "percent",
	"Retirement Fund": "landmark",
	"Employee Benefit Application": "heart-handshake",
	"Employee Incentive": "sparkles",
	"Retention Bonus": "award",
	"Bulk Salary Structure Assignment": "users-round",
	"Account": "book-open",
	"Cost Center": "target",
	"Accounts Settings": "settings",
	"Accounting Dimension": "boxes",
	"Currency": "coins",
}

_SIDEBAR_REPORT_ICONS = {
	"Salary Register": "notepad-text",
	"Bank Remittance": "landmark",
	"Income Tax Computation": "percent",
	"Payroll Register": "notepad-text",
	"EMP201 Report": "file-spreadsheet",
	"Statutory Submissions Summary": "clipboard-list",
	"Department Cost Analysis": "chart-column",
	"Salary Payments Based On Payment Mode": "wallet",
	"Salary Payments via ECS": "landmark",
	"Retirement Fund Deductions": "piggy-bank",
	"Income Tax Deductions": "percent",
	"General Ledger": "book-open",
	"Accounts Payable": "circle-arrow-down",
	"Accounts Receivable": "circle-arrow-up",
}


def _sidebar_section_icon(card_label: str) -> str:
	if not card_label:
		return "folder"
	t = card_label.lower()
	if "report" in t:
		return "notepad-text"
	if "master" in t or "setup" in t:
		return "database"
	if "transaction" in t:
		return "circle-dollar-sign"
	if "accounting" in t:
		return "book-open"
	if "statutory" in t or "south africa" in t:
		return "flag"
	if "coida" in t:
		return "hard-hat"
	if "configuration" in t:
		return "settings"
	if "organisation" in t or "organization" in t or "company" in t:
		return "building-2"
	if "labour" in t or "labor" in t or "employee" in t:
		return "users"
	if "equity" in t:
		return "clipboard-list"
	if "return" in t or "incident" in t:
		return "life-buoy"
	if "tax" in t or "vat" in t:
		return "percent"
	if "overview" in t or "hub" in t:
		return "layout-grid"
	if t == "payroll":
		return "circle-dollar-sign"
	if "incentive" in t:
		return "piggy-bank"
	return "folder"


def _sidebar_icon_for_target(link_type: str, link_to: str) -> str:
	if link_type == "DocType":
		return _SIDEBAR_DOCTYPE_ICONS.get(link_to, "circle-dot")
	if link_type == "Report":
		return _SIDEBAR_REPORT_ICONS.get(link_to, "file-text")
	if link_type == "Workspace":
		return "home"
	if link_type == "Dashboard":
		return "layout-dashboard"
	if link_type == "URL":
		return "layout-grid"
	return "file-text"


def _sidebar_icon_for_url_shortcut(label: str) -> str:
	m = {
		"SA Payroll": "accounting",
		"SA VAT": "sell",
		"SA Labour": "hr",
		"SA COIDA": "hard-hat",
	}
	return m.get(label, "layout-grid")


# Pinned to sidenav bottom (do not use broad "* Settings" — e.g. Accounts Settings stays in Accounting).
_SETTINGS_SIDEBAR_FOOTER_DOCTYPES = frozenset(
	{
		"ZA Local Setup",
		"Payroll Settings",
		"South Africa VAT Settings",
		"COIDA Settings",
		"Business Trip Settings",
	}
)


def _is_sidebar_settings_footer_link(link_type: str, link_to: str, workspace_name: str | None = None) -> bool:
	# SA Overview hub intentionally lists setup DocTypes in cards (not a pinned footer).
	if workspace_name == "SA Overview":
		return False
	if link_type != "DocType" or not link_to:
		return False
	return link_to in _SETTINGS_SIDEBAR_FOOTER_DOCTYPES


def _strip_nested_workspace_sidebar_icons(parent_name: str):
	"""Force empty icon on nested sidebar links (child=1). Fixes stale DB rows after partial saves."""
	if not parent_name or not frappe.db.table_exists("Workspace Sidebar Item"):
		return
	frappe.db.sql(
		"""
		UPDATE `tabWorkspace Sidebar Item`
		SET icon = ''
		WHERE parent = %s AND parenttype = 'Workspace Sidebar'
		  AND type = 'Link' AND IFNULL(`child`, 0) = 1
		""",
		parent_name,
	)


def rebuild_za_local_workspace_sidebars():
	"""
	Rebuild Workspace Sidebar items from each Workspace's shortcuts + link cards.
	Run after workspace JSON sync so sidenav matches workspace definition (like HR Payroll).
	"""
	if not frappe.db.table_exists("Workspace Sidebar"):
		return

	for workspace_name in (
		"SA Overview",
		"SA VAT",
		"SA Payroll",
		"SA Labour",
		"SA COIDA",
	):
		if not frappe.db.exists("Workspace", workspace_name):
			continue
		try:
			_rebuild_single_za_local_workspace_sidebar(workspace_name)
		except Exception as e:
			print(f"  ! Could not rebuild Workspace Sidebar '{workspace_name}': {e}")


def _rebuild_single_za_local_workspace_sidebar(workspace_name: str):
	"""
	Build Workspace Sidebar rows like Frappe HR Payroll: top-level Home (and optional
	Dashboard) + shortcut links with Lucide icons; Card Break → Section Break with
	indent/collapsible/keep_closed; links under each card as child rows (child=1, icon '')
	so the sidebar nests and does not fall back to the default 'list' icon.
	"""
	ws = frappe.get_doc("Workspace", workspace_name)
	rows = []
	idx = 0

	def add_row(data: dict):
		nonlocal idx
		r = dict(data)
		r["idx"] = idx
		idx += 1
		rows.append(r)

	shortcut_keys = set()
	for s in ws.shortcuts or []:
		st = getattr(s, "type", None)
		if st == "URL":
			shortcut_keys.add(("URL", getattr(s, "url", None) or ""))
		else:
			shortcut_keys.add((st, getattr(s, "link_to", None)))

	settings_footer = []
	settings_footer_keys = set()

	def queue_settings_footer(label: str, link_type: str, link_to: str):
		key = (link_type, link_to)
		if key in settings_footer_keys:
			return
		settings_footer_keys.add(key)
		settings_footer.append({"label": label, "link_type": link_type, "link_to": link_to})

	# Home must remain the first sidebar row (idx 0) after rebuild.
	add_row(
		{
			"type": "Link",
			"label": "Home",
			"link_type": "Workspace",
			"link_to": workspace_name,
			"icon": "home",
			"child": 0,
			"collapsible": 1,
			"indent": 0,
			"keep_closed": 0,
			"show_arrow": 0,
		}
	)

	# Dashboard link row only when a Dashboard *document* exists with this name.
	# Workspace names (e.g. SA Payroll) are not valid link_to for link_type Dashboard;
	# charts still render on the workspace home without this sidebar entry.
	if ws.get("charts") and frappe.db.exists("Dashboard", workspace_name):
		add_row(
			{
				"type": "Link",
				"label": "Dashboard",
				"link_type": "Dashboard",
				"link_to": workspace_name,
				"icon": "layout-dashboard",
				"child": 0,
				"collapsible": 1,
				"indent": 0,
				"keep_closed": 0,
				"show_arrow": 0,
			}
		)

	for s in ws.shortcuts or []:
		st = getattr(s, "type", None)
		if _is_sidebar_settings_footer_link(st, getattr(s, "link_to", None), workspace_name):
			queue_settings_footer(s.label, st, s.link_to)
			continue
		row = {
			"type": "Link",
			"label": s.label,
			"link_type": st,
			"icon": (
				_sidebar_icon_for_url_shortcut(s.label)
				if st == "URL"
				else _sidebar_icon_for_target(st, getattr(s, "link_to", None) or "")
			),
			"child": 0,
			"collapsible": 1,
			"indent": 0,
			"keep_closed": 0,
			"show_arrow": 0,
		}
		if st == "URL":
			row["url"] = getattr(s, "url", None) or ""
			row["link_to"] = ""
		else:
			row["link_to"] = s.link_to
		add_row(row)

	current_card_label = None
	pending_card_links = []

	def flush_card():
		nonlocal current_card_label, pending_card_links
		if not current_card_label or not pending_card_links:
			current_card_label = None
			pending_card_links = []
			return
		add_row(
			{
				"type": "Section Break",
				"label": current_card_label,
				"link_type": "DocType",
				"icon": _sidebar_section_icon(current_card_label),
				"child": 0,
				"collapsible": 1,
				"indent": 1,
				"keep_closed": 1,
				"show_arrow": 0,
			}
		)
		for L in pending_card_links:
			# Match Frappe HR Payroll sidebar: section row has icon; nested links are text-only
			# (icon "" — Frappe skips the default list glyph for child rows under indent sections).
			add_row(
				{
					"type": "Link",
					"label": L.label,
					"link_type": L.link_type,
					"link_to": L.link_to,
					"icon": "",
					"child": 1,
					"collapsible": 1,
					"indent": 0,
					"keep_closed": 0,
					"show_arrow": 0,
				}
			)
		current_card_label = None
		pending_card_links = []

	for link in ws.get("links") or []:
		if getattr(link, "hidden", 0):
			continue
		lt = getattr(link, "type", None)
		if lt == "Card Break":
			flush_card()
			current_card_label = link.label
		elif lt == "Link" and current_card_label is not None:
			if _is_sidebar_settings_footer_link(link.link_type, link.link_to, workspace_name):
				queue_settings_footer(link.label, link.link_type, link.link_to)
				continue
			key = (link.link_type, link.link_to)
			if key in shortcut_keys:
				continue
			pending_card_links.append(link)
		elif lt == "Link":
			if _is_sidebar_settings_footer_link(link.link_type, link.link_to, workspace_name):
				queue_settings_footer(link.label, link.link_type, link.link_to)
			else:
				# Link before any Card Break: top-level with icon (rare)
				add_row(
					{
						"type": "Link",
						"label": link.label,
						"link_type": link.link_type,
						"link_to": link.link_to,
						"icon": _sidebar_icon_for_target(link.link_type, link.link_to),
						"child": 0,
						"collapsible": 1,
						"indent": 0,
						"keep_closed": 0,
						"show_arrow": 0,
					}
				)

	flush_card()

	for item in settings_footer:
		add_row(
			{
				"type": "Link",
				"label": item["label"],
				"link_type": item["link_type"],
				"link_to": item["link_to"],
				"icon": "settings",
				"child": 0,
				"collapsible": 1,
				"indent": 0,
				"keep_closed": 0,
				"show_arrow": 0,
			}
		)

	# Frappe HR Payroll: section headers keep icons; nested dropdown rows never do.
	for r in rows:
		if r.get("type") == "Link" and frappe.utils.cint(r.get("child")):
			r["icon"] = ""

	for i, r in enumerate(rows):
		r["idx"] = i

	if frappe.db.exists("Workspace Sidebar", workspace_name):
		# Hard-delete child rows first. `sidebar.items = []` alone can leave merged/stale rows
		# (SA Payroll had many links; icons on "nested" rows were almost always stale DB, not COIDA).
		frappe.db.delete(
			"Workspace Sidebar Item",
			{"parent": workspace_name, "parenttype": "Workspace Sidebar"},
		)
		sidebar = frappe.get_doc("Workspace Sidebar", workspace_name)
	else:
		sidebar = frappe.new_doc("Workspace Sidebar")
		sidebar.title = workspace_name

	sidebar.header_icon = ws.icon
	sidebar.module = "SA Localisation"
	for r in rows:
		sidebar.append("items", r)

	sidebar.flags.ignore_permissions = True
	if sidebar.is_new():
		sidebar.insert(ignore_permissions=True)
		print(f"  ✓ Created Workspace Sidebar '{workspace_name}' ({len(rows)} items)")
	else:
		sidebar.save(ignore_permissions=True)
		print(f"  ✓ Rebuilt Workspace Sidebar '{workspace_name}' ({len(rows)} items)")

	_strip_nested_workspace_sidebar_icons(sidebar.name)


def sync_za_local_workspace_sidebar_modules():
	"""Group all SA area sidebars under module SA Localisation (HR-style switcher)."""
	if not frappe.db.table_exists("Workspace Sidebar"):
		return
	for title in (
		"SA Overview",
		"SA VAT",
		"SA Payroll",
		"SA Labour",
		"SA COIDA",
	):
		if frappe.db.exists("Workspace Sidebar", title):
			try:
				frappe.db.set_value(
					"Workspace Sidebar",
					title,
					"module",
					"SA Localisation",
					update_modified=False,
				)
			except Exception as e:
				print(f"  ! Could not set Workspace Sidebar module for {title}: {e}")


def sync_za_local_desktop_icons():
	"""
	One App tile on the desk (map logo) like Frappe HR; workspace links nest under it (parent_icon).
	Nested icons must NOT use hidden=1 — Frappe's desk prepare() drops hidden icons from the graph,
	so the App would have no child_icons and would navigate via link instead of opening the workspace modal.
	Uses add_to_apps_screen + app_title from hooks.
	"""
	if not frappe.db.table_exists("Desktop Icon"):
		return

	app_name = "za_local"
	try:
		app_title = frappe.get_hooks("app_title", app_name=app_name)[0]
	except (IndexError, TypeError):
		print("  ⊙ Skipping za_local desktop sync (no app_title hook)")
		return

	details = frappe.get_hooks("add_to_apps_screen", app_name=app_name)
	if not details:
		print("  ⊙ Skipping za_local desktop sync (no add_to_apps_screen)")
		return

	route = details[0].get("route", "/desk/sa-overview")
	logo = details[0].get("logo", "/assets/za_local/images/sa_map_icon.png")

	# Desktop Icon PK = label; App tile label must not clash with a Link row of the same label.
	for row in frappe.get_all("Desktop Icon", filters={"label": app_title}, fields=["name", "icon_type"]):
		if row.icon_type == "App":
			continue
		try:
			frappe.delete_doc("Desktop Icon", row.name, force=True, ignore_permissions=True)
			print(
				f"  ✓ Removed conflicting Desktop Icon '{row.name}' ({row.icon_type}) "
				f"so App tile '{app_title}' can use that label"
			)
		except Exception as e:
			print(f"  ! Could not remove conflicting desktop icon {row.name}: {e}")

	app_icon_name = frappe.db.get_value(
		"Desktop Icon",
		{"icon_type": "App", "app": app_name},
		"name",
	)
	if not app_icon_name:
		app_icon_name = frappe.db.get_value(
			"Desktop Icon",
			{"icon_type": "App", "label": "South Africa"},
			"name",
		)

	try:
		if app_icon_name:
			di = frappe.get_doc("Desktop Icon", app_icon_name)
		else:
			di = frappe.new_doc("Desktop Icon")
			di.icon_type = "App"
			di.app = app_name

		di.label = app_title
		di.link_type = "External"
		di.link = route
		di.logo_url = logo
		di.standard = 1
		di.flags.ignore_permissions = True
		if di.is_new():
			di.insert(ignore_permissions=True)
			print(f"  ✓ Created App desktop icon '{app_title}'")
		else:
			di.save(ignore_permissions=True)
			print(f"  ✓ Updated App desktop icon '{app_title}'")
	except Exception as e:
		print(f"  ! Could not upsert App desktop icon: {e}")
		return

	ws_labels = [
		"SA Overview",
		"SA VAT",
		"SA Payroll",
		"SA Labour",
		"SA COIDA",
	]
	for label in ws_labels:
		if not frappe.db.exists("Workspace", label):
			continue
		icons = frappe.get_all(
			"Desktop Icon",
			filters={"label": label, "icon_type": "Link"},
			fields=["name"],
		)
		if not icons:
			try:
				ws_icon = frappe.db.get_value("Workspace", label, "icon")
				link = frappe.new_doc("Desktop Icon")
				link.label = label
				link.icon_type = "Link"
				link.link_type = "Workspace Sidebar"
				link.link_to = label
				link.icon = ws_icon
				link.app = app_name
				link.parent_icon = app_title
				link.hidden = 0
				link.standard = 1
				link.flags.ignore_permissions = True
				link.insert(ignore_permissions=True)
				print(f"  ✓ Created nested desktop link icon for workspace '{label}'")
			except Exception as e:
				print(f"  ! Could not create desktop link icon for {label}: {e}")
			continue

		for row in icons:
			try:
				icon = frappe.get_doc("Desktop Icon", row.name)
				icon.app = app_name
				icon.parent_icon = app_title
				icon.hidden = 0
				ws_icon = frappe.db.get_value("Workspace", label, "icon")
				if ws_icon:
					icon.icon = ws_icon
				icon.flags.ignore_permissions = True
				icon.save(ignore_permissions=True)
			except Exception as e:
				print(f"  ! Could not update desktop icon {label}: {e}")

	try:
		frappe.cache.delete_key("desktop_icons")
		frappe.cache.delete_key("bootinfo")
	except Exception:
		pass
	print("  ✓ SA Localisation desk: App tile + nested workspace icons (modal picker)")


def before_migrate():
	"""
	Run before schema sync during bench migrate.
	- Rename module "COIDA" to "SA COIDA" in DB so Frappe loads za_local.sa_coida (not za_local.coida).
	- Clear app_modules cache so module list is rebuilt from modules.txt.
	"""
	if not frappe.db:
		return
	try:
		stabilize_sa_vat_doctype_metadata()
		# Update any DocType or Report that still has module "COIDA" to "SA COIDA"
		for dt in ("DocType", "Report"):
			if frappe.db.table_exists(dt):
				frappe.db.sql("UPDATE `tab{0}` SET module = 'SA COIDA' WHERE module = 'COIDA'".format(dt))
		frappe.db.commit()
		# Ensure cache is cleared so app_modules is rebuilt from modules.txt (SA COIDA not COIDA)
		frappe.cache().delete_value("app_modules")
		frappe.cache().delete_value("installed_app_modules")
	except Exception as e:
		frappe.log_error(f"before_migrate (za_local): {e}", "ZA Local before_migrate")
		# Don't fail migrate
		pass


def stabilize_sa_vat_doctype_metadata():
	"""Ensure the new SA VAT child doctypes stay app-owned and reloadable."""
	doctypes = (
		"South Africa VAT Settings",
		"South Africa VAT Tax Account",
		"VAT201 Return Transaction",
	)
	for doctype in doctypes:
		if frappe.db.exists("DocType", doctype):
			frappe.db.set_value("DocType", doctype, {"module": "SA VAT", "custom": 0}, update_modified=False)

	for doctype in ("south_africa_vat_tax_account", "vat201_return_transaction", "south_africa_vat_settings"):
		try:
			frappe.reload_doc("sa_vat", "doctype", doctype)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"ZA Local VAT pre-migrate reload failed: {doctype}")


def ensure_modules_visible():
	"""
	Ensure all za_local modules are visible in the sidebar navigation.

	In Frappe, modules appear in the sidebar if they have DocTypes assigned
	and the modules are properly configured. This function ensures all
	za_local modules are set up correctly.
	"""
	print("\nEnsuring za_local modules are visible...")

	# List of za_local modules from modules.txt
	za_local_modules = [
		"SA Localisation",
		"SA Setup",
		"SA VAT",
		"SA Payroll",
		"SA Labour",
		"SA COIDA",
	]

	for module_name in za_local_modules:
		# Check if module exists
		if not frappe.db.exists("Module Def", module_name):
			print(f"  ⊙ Module '{module_name}' does not exist (will be created by Frappe)")
			continue

		try:
			module_doc = frappe.get_doc("Module Def", module_name)

			# Ensure module is properly configured
			if module_doc.app_name != "za_local":
				module_doc.app_name = "za_local"
				module_doc.save(ignore_permissions=True)
				print(f"  ✓ Updated module '{module_name}' app_name to 'za_local'")

			# Ensure module is not custom (app modules should have custom=0)
			if module_doc.custom != 0:
				module_doc.custom = 0
				module_doc.save(ignore_permissions=True)
				print(f"  ✓ Updated module '{module_name}' to non-custom")

			# Check if module has DocTypes
			doctype_count = frappe.db.count("DocType", {"module": module_name})
			if doctype_count > 0:
				print(f"  ✓ Module '{module_name}' has {doctype_count} DocType(s)")
			else:
				print(f"  ⚠ Module '{module_name}' has no DocTypes (may not appear in sidebar)")

		except Exception as e:
			print(f"  ! Could not check/update module '{module_name}': {e}")

	frappe.db.commit()
	print("  ✓ Module visibility check complete\n")


def create_company_contribution_doctype():
	"""
	Create Company Contribution DocType if it doesn't exist.

	This is a child table used in Salary Structure for company contributions
	like UIF employer portion, SDL, COIDA, etc.

	Note: Only creates if HRMS is installed, as it's used by Salary Structure.
	"""
	if not is_hrms_installed():
		print("  ⊙ Skipping Company Contribution DocType (HRMS not installed)")
		return

	if frappe.db.exists("DocType", "Company Contribution"):
		print("Company Contribution DocType already exists")
		return

	print("Creating Company Contribution DocType...")

	# Determine module - use Payroll if available, otherwise SA Payroll
	module_name = "Payroll"  # HRMS module
	if not frappe.db.exists("Module Def", "Payroll"):
		module_name = "SA Payroll"  # Fallback to our module

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Company Contribution",
			"module": module_name,
			"custom": 1,
			"istable": 1,
			"editable_grid": 1,
			"track_changes": 1,
			"fields": [
				{
					"fieldname": "salary_component",
					"label": "Salary Component",
					"fieldtype": "Link",
					"options": "Salary Component",
					"in_list_view": 1,
					"reqd": 1,
				},
				{
					"fieldname": "abbr",
					"label": "Abbr",
					"fieldtype": "Data",
					"fetch_from": "salary_component.salary_component_abbr",
					"read_only": 1,
				},
				{
					"fieldname": "amount",
					"label": "Amount",
					"fieldtype": "Currency",
					"options": "currency",
					"in_list_view": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "condition_and_formula_section",
					"label": "Condition and Formula",
					"fieldtype": "Section Break",
					"collapsible": 1,
				},
				{
					"fieldname": "condition",
					"label": "Condition",
					"fieldtype": "Code",
					"fetch_from": "salary_component.condition",
					"allow_on_submit": 1,
				},
				{"fieldname": "column_break_6", "fieldtype": "Column Break"},
				{
					"fieldname": "amount_based_on_formula",
					"label": "Amount based on formula",
					"fieldtype": "Check",
					"default": "0",
					"fetch_from": "salary_component.amount_based_on_formula",
					"allow_on_submit": 1,
				},
				{
					"fieldname": "formula",
					"label": "Formula",
					"fieldtype": "Code",
					"fetch_from": "salary_component.formula",
					"allow_on_submit": 1,
				},
			],
			"permissions": [
				{"role": "HR Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
				{"role": "HR User", "read": 1, "write": 1, "create": 1},
			],
		}
	)

	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print("✓ Company Contribution DocType created successfully")


def setup_default_data():
	"""
	Set up default data required for South African localization.

	Creates:
	- Default ETI Slabs
	- Default Tax Rebates
	- Default Medical Tax Credit Rates
	"""
	print("Setting up default data...")

	# ETI Slabs will be created when the ETI Slab doctype is migrated
	# Tax Rebates will be created when the Tax Rebates doctype is migrated
	# For now, we just print a message

	print("✓ Default data setup complete")
	print("  Note: Configure ETI Slabs, Tax Rebates, and other settings manually")


def seed_sars_payroll_codes():
	"""Ensure the SARS Payroll Code master data exists and link known default salary components."""
	if not frappe.db.exists("DocType", "SARS Payroll Code"):
		return

	for row in DEFAULT_SARS_PAYROLL_CODES:
		if frappe.db.exists("SARS Payroll Code", row["code"]):
			doc = frappe.get_doc("SARS Payroll Code", row["code"])
			doc.update(row)
			doc.flags.ignore_permissions = True
			doc.save()
		else:
			doc = frappe.get_doc({"doctype": "SARS Payroll Code", **row, "active": 1})
			doc.insert(ignore_permissions=True)

	if frappe.db.exists("DocType", "Salary Component"):
		for salary_component, code in DEFAULT_SALARY_COMPONENT_SARS_CODES.items():
			if frappe.db.exists("Salary Component", salary_component):
				frappe.db.set_value(
					"Salary Component",
					salary_component,
					"za_sars_payroll_code",
					code,
					update_modified=False,
				)
		if frappe.db.has_column("Salary Component", "za_exclude_from_irp5"):
			for salary_component in DEFAULT_IRP5_EXCLUDED_SALARY_COMPONENTS:
				if frappe.db.exists("Salary Component", salary_component):
					frappe.db.set_value(
						"Salary Component",
						salary_component,
						"za_exclude_from_irp5",
						1,
						update_modified=False,
					)

	frappe.db.commit()
	print("  ✓ SARS Payroll Codes seeded")


def migrate_irp5_legacy_source_fields():
	"""Move legacy site-specific IRP5 source fields into app-owned za_local fields."""
	if frappe.db.exists("DocType", "Company") and frappe.db.has_column(
		"Company", "custom_paye_reference_number"
	):
		for company in frappe.get_all(
			"Company", fields=["name", "za_paye_reference_number", "custom_paye_reference_number"]
		):
			if company.za_paye_reference_number:
				continue
			if company.custom_paye_reference_number:
				frappe.db.set_value(
					"Company",
					company.name,
					"za_paye_reference_number",
					company.custom_paye_reference_number,
					update_modified=False,
				)

	if frappe.db.exists("DocType", "Employee") and frappe.db.has_column("Employee", "custom_tax_number"):
		for employee in frappe.get_all(
			"Employee",
			fields=["name", "za_income_tax_reference_number", "custom_tax_number"],
		):
			if employee.za_income_tax_reference_number:
				continue
			if employee.custom_tax_number:
				frappe.db.set_value(
					"Employee",
					employee.name,
					"za_income_tax_reference_number",
					employee.custom_tax_number,
					update_modified=False,
				)

	if frappe.db.exists("DocType", "Employee") and frappe.db.has_column(
		"Employee", "custom_residential_address"
	):
		for employee in frappe.get_all(
			"Employee",
			fields=["name", "employee_name", "za_residential_address", "custom_residential_address"],
		):
			if employee.za_residential_address:
				continue
			address_text = (employee.custom_residential_address or "").strip()
			if not address_text:
				continue

			address_name = _create_irp5_address_from_legacy_text(
				employee.name, employee.employee_name, address_text
			)
			if address_name:
				frappe.db.set_value(
					"Employee",
					employee.name,
					"za_residential_address",
					address_name,
					update_modified=False,
				)

	frappe.db.commit()
	print("  ✓ Migrated legacy IRP5 source fields")


def _create_irp5_address_from_legacy_text(
	employee_name: str, employee_display_name: str | None, address_text: str
):
	title = employee_display_name or employee_name
	existing = frappe.get_all(
		"Address",
		filters={"address_title": title, "address_type": "Personal"},
		fields=["name", "address_line1", "address_line2"],
		limit=1,
	)
	if existing:
		return existing[0].name

	lines = [line.strip() for line in address_text.splitlines() if line.strip()]
	if not lines:
		return None

	address = frappe.new_doc("Address")
	address.address_title = title
	address.address_type = "Personal"
	address.address_line1 = lines[0]
	if len(lines) > 1:
		address.address_line2 = lines[1]
	if len(lines) > 2:
		address.city = lines[2][:140]
	if len(lines) > 3:
		address.pincode = lines[3][:10]
	address.append(
		"links",
		{
			"link_doctype": "Employee",
			"link_name": employee_name,
			"link_title": employee_display_name or employee_name,
		},
	)
	address.flags.ignore_permissions = True
	address.insert(ignore_permissions=True)
	return address.name


def create_salary_component_if_not_exists(component_data):
	"""
	Helper function to create a salary component if it doesn't exist.

	Args:
		component_data (dict): Salary component configuration
	"""
	if not frappe.db.exists("Salary Component", component_data["name"]):
		doc = frappe.get_doc({"doctype": "Salary Component", **component_data})
		doc.insert(ignore_permissions=True)
		print(f"✓ Created Salary Component: {component_data['name']}")
	else:
		print(f"  Salary Component already exists: {component_data['name']}")


def setup_default_salary_components():
	"""
	Create default South African salary components.

	Creates components for:
	- PAYE
	- UIF Employee Contribution
	- UIF Employer Contribution
	- SDL Contribution
	- COIDA
	"""
	components = [
		{
			"name": "PAYE",
			"salary_component_abbr": "PAYE",
			"type": "Deduction",
			"description": "Pay As You Earn - Income Tax",
			"is_tax_applicable": 0,
			"variable_based_on_taxable_salary": 1,
		},
		{
			"name": "UIF Employee Contribution",
			"salary_component_abbr": "UIF_EE",
			"type": "Deduction",
			"description": "Unemployment Insurance Fund - Employee Contribution (1%)",
			"is_tax_applicable": 0,
			"formula": UIF_FORMULA,
			"amount_based_on_formula": 1,
		},
		{
			"name": "UIF Employer Contribution",
			"salary_component_abbr": "UIF_ER",
			"type": "Company Contribution",
			"description": "Unemployment Insurance Fund - Employer Contribution (1%)",
			"is_tax_applicable": 0,
			"formula": UIF_FORMULA,
			"amount_based_on_formula": 1,
		},
		{
			"name": "SDL Contribution",
			"salary_component_abbr": "SDL",
			"type": "Company Contribution",
			"description": "Skills Development Levy (1%)",
			"is_tax_applicable": 0,
			"formula": SDL_FORMULA,
			"amount_based_on_formula": 1,
		},
	]

	for component in components:
		create_salary_component_if_not_exists(component)


def make_property_setters():
	"""Compatibility wrapper for the centralized property-setter implementation."""
	apply_property_setters()


def apply_statutory_formulas():
	"""Ensure statutory Salary Components and Company Contribution rows carry correct formulas.
	- UIF Employee & Employer: 1% of gross pay capped at 177.12
	- SDL: 1% of gross pay
	Also enable Amount based on Formula on these components and child rows.
	"""
	print("Applying statutory formulas to salary components and company contribution rows...")

	if not frappe.db.table_exists("Salary Component"):
		print("  ⊙ Skipping statutory formula updates (Salary Component DocType not available)")
		return

	component_updates = {
		"UIF Employee Contribution": {
			"amount_based_on_formula": 1,
			"formula": UIF_FORMULA,
		},
		"UIF Employer Contribution": {
			"amount_based_on_formula": 1,
			"formula": UIF_FORMULA,
			"type": "Company Contribution",
		},
		"SDL Contribution": {
			"amount_based_on_formula": 1,
			"formula": SDL_FORMULA,
			"type": "Company Contribution",
		},
	}

	for canonical_name, fields in component_updates.items():
		if frappe.db.exists("Salary Component", canonical_name):
			try:
				frappe.db.set_value("Salary Component", canonical_name, fields)
			except Exception as e:
				print(f"  ! Could not update Salary Component {canonical_name}: {e}")

	# Update existing Salary Structure child rows and Salary Detail records
	_update_statutory_formulas_in_child_tables(component_updates)

	print("✓ Statutory formulas applied")


def _update_statutory_formulas_in_child_tables(component_updates: dict[str, dict]):
	if not frappe.db.table_exists("Company Contribution"):
		print("  ⊙ Skipping Company Contribution child row updates (DocType not available)")
	else:
		for name, fields in component_updates.items():
			if name not in ("UIF Employer Contribution", "SDL Contribution"):
				continue
			frappe.db.sql(
				"""
				UPDATE `tabCompany Contribution`
				SET amount_based_on_formula = 1, formula = %(formula)s
				WHERE salary_component = %(name)s
				""",
				{"name": name, "formula": fields["formula"]},
			)

	if frappe.db.table_exists("Salary Detail"):
		for name, fields in component_updates.items():
			frappe.db.sql(
				"""
				UPDATE `tabSalary Detail`
				SET amount_based_on_formula = 1, formula = %(formula)s
				WHERE salary_component = %(name)s
				""",
				{"name": name, "formula": fields["formula"]},
			)

	frappe.db.commit()


def import_master_data():
	"""
	Import master data from CSV files.

	Loads predefined data for:
	- Business Trip Regions (SA cities and international rates)
	- SETA list
	- Bargaining Councils
	"""
	print("Importing master data...")

	try:
		from za_local.utils.csv_importer import import_all_master_data

		import_all_master_data()
	except Exception as e:
		print(f"  Warning: Could not import master data: {e}")
		print("  Master data can be imported manually later.")


def setup_default_retirement_funds():
	"""Create default retirement fund types for South African retirement planning"""
	retirement_funds = [
		{"fund_name": "Company Pension Fund", "fund_type": "Pension"},
		{"fund_name": "Company Provident Fund", "fund_type": "Provident"},
		{"fund_name": "Retirement Annuity", "fund_type": "Retirement Annuity"},
	]

	for fund in retirement_funds:
		if not frappe.db.exists("Retirement Fund", {"fund_name": fund["fund_name"]}):
			try:
				doc = frappe.get_doc(
					{
						"doctype": "Retirement Fund",
						**fund,
						"employee_contribution_percentage": 7.5,
						"employer_contribution_percentage": 10.0,
						"tax_deductible_limit": 27.5,  # 27.5% of taxable income
						"company": frappe.defaults.get_defaults().get("company"),
					}
				)
				doc.insert(ignore_permissions=True)
			except Exception as e:
				print(f"! Could not create retirement fund {fund['fund_name']}: {e}")

	print("✓ Default retirement funds created")


def run_za_local_setup(setup_doc):
	"""
	Execute za_local setup based on user selections.
	Called from ZA Local Setup DocType when user completes the setup wizard.

	Args:
		setup_doc: ZA Local Setup document instance
	"""
	import json
	from pathlib import Path

	setup_doc.setup_status = "In Progress"
	setup_doc.save()
	frappe.db.commit()

	try:
		data_dir = Path(frappe.get_app_path("za_local", "sa_setup", "data"))

		# Load salary components
		if setup_doc.load_salary_components:
			load_data_from_json(data_dir / "salary_components.json")
			print("✓ Loaded statutory salary components")

		if setup_doc.load_earnings_components:
			load_data_from_json(data_dir / "earnings_components.json")
			print("✓ Loaded earnings components")

		# Load tax configuration
		if setup_doc.load_tax_slabs:
			load_data_from_json(data_dir / "tax_slabs_2025.json")  # 2024-2025 (2025 tax year)
			print("✓ Loaded 2024-2025 tax slabs")

		if setup_doc.load_tax_rebates or setup_doc.load_medical_credits:
			load_data_from_json(data_dir / "tax_rebates_2025.json")  # 2024-2025 (2025 tax year)
			print("✓ Loaded tax rebates and medical tax credits")

		# Load master data
		if setup_doc.load_business_trip_regions:
			from za_local.utils.csv_importer import import_csv_data

			import_csv_data("Business Trip Region", "business_trip_region.csv")
			print("✓ Loaded business trip regions")

		# Load Chart of Accounts
		if setup_doc.load_chart_of_accounts and setup_doc.company:
			print("Loading South African Chart of Accounts...")
			try:
				from za_local.accounts.setup_chart import load_sa_chart_of_accounts

				load_sa_chart_of_accounts(setup_doc.company)
				print("✓ Loaded Chart of Accounts")
			except Exception as e:
				print(f"  ! Warning: Could not load Chart of Accounts: {e}")
				print("  Note: Chart of Accounts can be loaded manually later")
				frappe.log_error(f"Chart of Accounts loading failed: {e!s}", "ZA Local Setup")

		# Mark as completed
		setup_doc.setup_status = "Completed"
		setup_doc.setup_completed_on = frappe.utils.now()
		setup_doc.save()
		frappe.db.commit()

		frappe.msgprint("✅ South African localization setup completed successfully!")

	except Exception as e:
		setup_doc.setup_status = "Pending"
		setup_doc.save()
		frappe.db.commit()
		frappe.log_error(f"Setup failed: {e!s}", "ZA Local Setup")
		frappe.throw(f"Setup failed: {e!s}")


@frappe.whitelist()
def refresh_sa_tax_tables():
	"""
	Idempotently reload South African payroll periods, tax slabs and rebates
	from fixtures for all configured tax years (2025, 2026, 2027) without
	recreating the site.
	Can be run via bench:
	  bench --site <site> execute za_local.sa_setup.install.refresh_sa_tax_tables
	"""
	import json
	from pathlib import Path

	data_dir = Path(frappe.get_app_path("za_local", "sa_setup", "data"))
	fixture_files = [
		# Payroll Periods
		"payroll_period_2025.json",  # 2024-2025 (2025 tax year)
		"payroll_period_2026.json",  # 2025-2026 (2026 tax year)
		"payroll_period_2027.json",  # 2026-2027 (2027 tax year)
		# Income Tax Slabs
		"tax_slabs_2025.json",  # 2024-2025 (2025 tax year)
		"tax_slabs_2026.json",  # 2025-2026 (2026 tax year)
		"tax_slabs_2027.json",  # 2026-2027 (2027 tax year)
		# Tax Rebates & Medical Credits
		"tax_rebates_2025.json",  # 2024-2025 (2025 tax year)
		"tax_rebates_2026.json",  # 2025-2026 (2026 tax year)
		"tax_rebates_2027.json",  # 2026-2027 (2027 tax year)
	]

	print("\nRefreshing South African payroll periods and tax tables from fixtures...")
	for filename in fixture_files:
		file_path = data_dir / filename
		if not file_path.exists():
			print(f"  ⊙ Skipping {filename} (file not found)")
			continue
		try:
			# Single DocType (Tax Rebates and Medical Tax Credit) needs merge behaviour, not delete/recreate
			if filename.startswith("tax_rebates_"):
				_merge_tax_rebates_from_file(file_path)
				print(f"  ✓ Merged rebates from {filename}")
			else:
				# Best-effort pre-delete so fixture values overwrite existing ones for non-Single doctypes
				try:
					with open(file_path) as f:
						raw = json.load(f)

					records: list[dict] = []
					if isinstance(raw, list):
						records = raw
					elif isinstance(raw, dict) and raw.get("doctype"):
						records = [raw]
					elif isinstance(raw, dict):
						for dt, rows in raw.items():
							for row in rows or []:
								row = dict(row)
								row.setdefault("doctype", dt)
								records.append(row)

					for record in records:
						doctype = record.get("doctype")
						name = record.get("name")
						if (
							doctype in ("Payroll Period", "Income Tax Slab")
							and name
							and frappe.db.exists(doctype, name)
						):
							frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
							print(f"  ⊙ Deleted existing {doctype}: {name}")
				except Exception:
					# Don't fail refresh if pre-delete inspection fails
					pass

				load_data_from_json(file_path)
				print(f"  ✓ Loaded {filename}")
		except Exception as e:
			print(f"  ! Error loading {filename}: {e}")

	print("✓ SA payroll periods and tax tables refresh complete\n")


def _merge_tax_rebates_from_file(file_path: Path) -> None:
	"""Merge a tax_rebates_*.json fixture into the Single DocType without discarding other years."""
	try:
		with open(file_path) as f:
			data = json.load(f)
	except Exception as e:
		print(f"  ! Could not read {file_path.name}: {e}")
		return

	if not isinstance(data, dict) or data.get("doctype") != "Tax Rebates and Medical Tax Credit":
		# Not in expected single-doc format
		return

	payroll_periods_rebates = data.get("tax_rebates_rate") or []
	payroll_periods_medical = data.get("medical_tax_credit") or []

	if not payroll_periods_rebates and not payroll_periods_medical:
		return

	doc = frappe.get_single("Tax Rebates and Medical Tax Credit")

	# Helper to upsert rows by payroll_period
	def upsert_child(child_table_name: str, new_rows: list[dict]):
		if not new_rows:
			return
		child_rows = list(doc.get(child_table_name) or [])
		index = {row.get("payroll_period"): row for row in child_rows}

		for nr in new_rows:
			pp = nr.get("payroll_period")
			if not pp:
				continue
			if pp in index:
				row = index[pp]
				for field, value in nr.items():
					if field != "name":
						row.set(field, value)
			else:
				child_rows.append(nr)

		doc.set(child_table_name, child_rows)

	upsert_child("tax_rebates_rate", payroll_periods_rebates)
	upsert_child("medical_tax_credit", payroll_periods_medical)

	doc.flags.ignore_permissions = True
	doc.save()


def load_data_from_json(file_path):
	"""
	Load data from JSON file and insert into database.

	Args:
		file_path: Path to JSON file
	"""
	import json

	with open(file_path) as f:
		data = json.load(f)

	# Handle different JSON formats
	if isinstance(data, dict):
		# Check if it's a single record (has "doctype" key)
		if "doctype" in data:
			# Single record
			insert_record(data)
		else:
			# Dict with DocType as key
			for doctype, records in data.items():
				for record in records:
					# Add doctype to record if not present
					if "doctype" not in record:
						record["doctype"] = doctype
					insert_record(record)
	elif isinstance(data, list):
		# List of records
		for record in data:
			insert_record(record)

	# Commit after loading all records from this file
	frappe.db.commit()


def insert_record(record):
	"""
	Insert a single record, skip if exists.
	Handles both regular DocTypes and Single DocTypes.
	Also handles child tables (like Holiday List with holidays).

	Args:
		record: Dict with doctype and field values
	"""
	doctype = record.get("doctype")

	# Determine the name field - different DocTypes use different name fields
	# Standard: "name"
	# Salary Component: "salary_component"
	# Holiday List: "holiday_list_name"
	name = record.get("name") or record.get("salary_component") or record.get("holiday_list_name")

	# Check if it's a Single DocType
	meta = frappe.get_meta(doctype)
	is_single = meta.issingle

	# Handle company field - set to first company if empty
	if "company" in record and not record.get("company"):
		companies = frappe.get_all("Company", limit=1)
		if companies:
			record["company"] = companies[0].name

	try:
		# Suppress validation warnings during setup (e.g., "Accounts not set")
		# These are expected and users will configure accounts later
		_message_log = frappe.local.message_log
		frappe.local.message_log = []

		if is_single:
			# For Single DocTypes, always update (don't check exists)
			doc = frappe.get_single(doctype)
			# Update fields from record
			for key, value in record.items():
				if key != "doctype":
					doc.set(key, value)
			doc.save(ignore_permissions=True)
			print(f"  ✓ Updated Single DocType: {doctype}")
		else:
			# For regular DocTypes, check if exists
			# Special handling for Holiday List - check by holiday_list_name
			if doctype == "Holiday List" and name:
				exists = frappe.db.exists("Holiday List", name)
			elif name:
				exists = frappe.db.exists(doctype, name)
			else:
				# If no name field, check if we should create anyway
				exists = False

			if not exists:
				# Create the document
				# frappe.get_doc() automatically handles child tables when you pass them in the record dict
				# For Holiday List, the "holidays" array will be automatically converted to child table rows
				# Each item in the "holidays" array becomes a row in the Holiday child table
				doc = frappe.get_doc(record)
				doc.insert(ignore_permissions=True, ignore_mandatory=True)

				created_name = name or doc.name
				print(f"  ✓ Created {doctype}: {created_name}")

				# Auto-submit submittable doctypes (e.g. Income Tax Slab) so they are ready to use
				try:
					if meta.is_submittable and hasattr(doc, "submit") and doc.docstatus == 0:
						doc.submit()
						print(f"    → Submitted {doctype}: {created_name}")
				except Exception as submit_err:
					print(f"    ! Warning: Could not submit {doctype} {created_name}: {submit_err}")

				# For Holiday List, verify holidays were saved
				if doctype == "Holiday List":
					# Reload document to get latest state from database
					doc.reload()
					holiday_count = len(doc.get("holidays", [])) if hasattr(doc, "get") else 0
					if holiday_count > 0:
						print(f"    → Added {holiday_count} holidays to '{created_name}'")
					else:
						# If no holidays in doc, check the original record
						holiday_count_from_record = len(record.get("holidays", []))
						if holiday_count_from_record > 0:
							print(
								f"    ! Warning: {holiday_count_from_record} holidays in record but not saved."
							)
							print(
								"    ! This may indicate a child table field name mismatch or HRMS not fully installed."
							)
						else:
							print("    ! Warning: No holidays found in record")
			else:
				print(f"  ⊙ Skipped {doctype}: {name} (already exists)")

		# Restore message log
		frappe.local.message_log = _message_log
	except Exception as e:
		# Restore message log even on error
		frappe.local.message_log = _message_log
		print(f"  ✗ Error with {doctype} {name or 'unknown'}: {e}")

		# For Holiday List, provide more specific error information
		if doctype == "Holiday List":
			print("    ! Holiday List creation failed. Check:")
			print("      - Is HRMS installed? (Holiday List is an HRMS DocType)")
			print("      - Does the record have 'holidays' child table array?")
			print("      - Are holiday items properly formatted with 'holiday_date' and 'description'?")

		import traceback

		traceback.print_exc()
