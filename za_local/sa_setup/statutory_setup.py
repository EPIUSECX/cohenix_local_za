"""Deterministic setup for company-scoped South African payroll tax masters."""

from copy import deepcopy

import frappe
from frappe import _
from frappe.utils import getdate

from za_local.utils.file_utils import read_app_json, resolve_app_path
from za_local.utils.hrms_detection import is_hrms_installed
from za_local.utils.statutory_rates import get_tax_year_for_date

PAYROLL_PERIOD_FILES = (
	"payroll_period_2025.json",
	"payroll_period_2026.json",
	"payroll_period_2027.json",
)
INCOME_TAX_SLAB_FILES = (
	"tax_slabs_2025.json",
	"tax_slabs_2026.json",
	"tax_slabs_2027.json",
)
TAX_REBATE_FILES = (
	"tax_rebates_2025.json",
	"tax_rebates_2026.json",
	"tax_rebates_2027.json",
)
PUBLIC_HOLIDAY_FILES = (
	"holiday_list_2025.json",
	"holiday_list_2026.json",
	"holiday_list_2027.json",
)


def ensure_all_company_tax_configuration():
	"""Create missing statutory tax masters for every South African company."""
	if not is_hrms_installed():
		return {}
	ensure_sa_public_holiday_lists()

	companies = frappe.get_all(
		"Company",
		filters={"country": "South Africa"},
		pluck="name",
		order_by="creation asc",
	)
	results = {}
	for company in companies:
		results[company] = ensure_company_tax_configuration(company)
	return results


def ensure_sa_public_holiday_lists():
	"""Synchronize the app-owned official public-holiday reference lists.

	These lists intentionally contain public holidays only. They are not forced
	as Company defaults because weekly-off rules differ by employer; implementers
	must copy/extend the reference list with the applicable weekly-off pattern.
	"""
	if not frappe.db.exists("DocType", "Holiday List"):
		return []

	data_dir = resolve_app_path("sa_setup", "data")
	synchronized = []
	for filename in PUBLIC_HOLIDAY_FILES:
		for source in _read_records(data_dir / filename):
			name = source["holiday_list_name"]
			doc = frappe.get_doc("Holiday List", name) if frappe.db.exists("Holiday List", name) else frappe.new_doc(
				"Holiday List"
			)
			desired_holidays = [
				(str(row["holiday_date"]), row.get("description") or "", int(row.get("weekly_off") or 0))
				for row in source.get("holidays") or []
			]
			current_holidays = [
				(str(row.holiday_date), row.description or "", int(row.weekly_off or 0))
				for row in doc.get("holidays") or []
			]
			is_current = (
				not doc.is_new()
				and str(doc.from_date) == str(source["from_date"])
				and str(doc.to_date) == str(source["to_date"])
				and current_holidays == desired_holidays
			)
			if is_current:
				synchronized.append(name)
				continue

			doc.holiday_list_name = name
			doc.from_date = source["from_date"]
			doc.to_date = source["to_date"]
			doc.set("holidays", [])
			for row in source.get("holidays") or []:
				doc.append("holidays", row)
			doc.flags.ignore_permissions = True
			if doc.is_new():
				doc.insert(ignore_permissions=True)
			else:
				doc.save(ignore_permissions=True)
			synchronized.append(doc.name)
	return synchronized


def configure_new_south_african_company(doc, method=None):
	"""Create required payroll masters after ERPNext creates an SA company."""
	if doc.country != "South Africa" or not is_hrms_installed():
		return

	ensure_company_tax_configuration(doc.name)

	# Import at runtime to avoid an install-module cycle.
	from za_local.sa_setup.install import seed_statutory_rate_packs

	seed_statutory_rate_packs()


def ensure_company_tax_configuration(company: str):
	"""Create missing payroll periods, slabs, rebates and credits for one company.

	Existing statutory documents are never overwritten. Annual changes must be
	shipped as a new rate pack/fixture and applied through a versioned patch.
	"""
	_validate_company(company)
	data_dir = resolve_app_path("sa_setup", "data")
	period_names = {}
	created = []

	for filename in PAYROLL_PERIOD_FILES:
		for record in _read_records(data_dir / filename):
			original_name = record["name"]
			actual_name, was_created = _ensure_company_record(record, company)
			period_names[original_name] = actual_name
			if was_created:
				created.append(actual_name)

	for filename in INCOME_TAX_SLAB_FILES:
		for record in _read_records(data_dir / filename):
			actual_name, was_created = _ensure_company_record(record, company)
			if was_created:
				created.append(actual_name)

	settings = frappe.get_single("Tax Rebates and Medical Tax Credit")
	for filename in TAX_REBATE_FILES:
		data = read_app_json(data_dir / filename)
		_upsert_missing_child_rows(settings, "tax_rebates_rate", data, period_names)
		_upsert_missing_child_rows(settings, "medical_tax_credit", data, period_names)
	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)

	return {"created": created, "payroll_periods": period_names}


def get_missing_current_tax_configuration(company: str, date_value=None) -> list[str]:
	"""Return actionable missing-master messages for the supplied tax year."""
	date_value = getdate(date_value or frappe.utils.today())
	tax_year = get_tax_year_for_date(date_value)
	missing = []

	period = frappe.db.get_value(
		"Payroll Period",
		{
			"company": company,
			"start_date": ["<=", date_value],
			"end_date": [">=", date_value],
		},
		"name",
	)
	if not period:
		missing.append(_("Payroll Period for {0} ({1})").format(company, tax_year))

	slab = frappe.db.get_value(
		"Income Tax Slab",
		{
			"company": company,
			"effective_from": ["<=", date_value],
			"disabled": 0,
			"docstatus": 1,
		},
		"name",
		order_by="effective_from desc",
	)
	if not slab:
		missing.append(_("submitted Income Tax Slab for {0} ({1})").format(company, tax_year))

	if period:
		settings = frappe.get_single("Tax Rebates and Medical Tax Credit")
		if not any(row.payroll_period == period for row in settings.tax_rebates_rate or []):
			missing.append(_("Tax Rebate row for Payroll Period {0}").format(period))
		if not any(row.payroll_period == period for row in settings.medical_tax_credit or []):
			missing.append(_("Medical Tax Credit row for Payroll Period {0}").format(period))

	return missing


def validate_current_tax_configuration(company: str, date_value=None):
	"""Fail payroll setup loudly when statutory masters are incomplete."""
	missing = get_missing_current_tax_configuration(company, date_value)
	if missing:
		frappe.throw(
			_("South African payroll setup is incomplete:<br>{0}").format(
				"<br>".join(f"• {frappe.utils.escape_html(item)}" for item in missing)
			),
			title=_("Incomplete South African Payroll Setup"),
		)


def _validate_company(company: str):
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid Company is required to configure South African payroll."))
	if frappe.db.get_value("Company", company, "country") != "South Africa":
		frappe.throw(_("Company {0} is not configured for South Africa.").format(company))


def _read_records(path):
	data = read_app_json(path)
	return data if isinstance(data, list) else [data]


def _ensure_company_record(source: dict, company: str) -> tuple[str, bool]:
	record = deepcopy(source)
	doctype = record["doctype"]
	base_name = record["name"]
	name = _get_company_scoped_name(doctype, base_name, company)
	record["name"] = name
	record["company"] = company

	if frappe.db.exists(doctype, name):
		return name, False

	doc = frappe.get_doc(record)
	doc.insert(ignore_permissions=True)
	if doc.meta.is_submittable and doc.docstatus == 0:
		doc.submit()
	return doc.name, True


def _get_company_scoped_name(doctype: str, base_name: str, company: str) -> str:
	if frappe.db.exists(doctype, base_name):
		existing_company = frappe.db.get_value(doctype, base_name, "company")
		if existing_company in (None, "", company):
			return base_name

	company_count = frappe.db.count("Company", {"country": "South Africa"})
	if company_count <= 1 and not frappe.db.exists(doctype, base_name):
		return base_name

	abbr = frappe.db.get_value("Company", company, "abbr") or company
	return f"{base_name} - {abbr}"


def _upsert_missing_child_rows(settings, child_field: str, data: dict, period_names: dict):
	existing = {row.payroll_period for row in settings.get(child_field) or []}
	for source in data.get(child_field) or []:
		row = deepcopy(source)
		row["payroll_period"] = period_names.get(row["payroll_period"], row["payroll_period"])
		if row["payroll_period"] in existing:
			continue
		settings.append(child_field, row)
		existing.add(row["payroll_period"])
