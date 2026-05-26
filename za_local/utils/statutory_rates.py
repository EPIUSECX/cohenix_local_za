"""Date-effective South African payroll statutory rates.

The JSON files in ``sa_setup/data/statutory_rates_*.json`` are the annual
statutory packs. Calculation code should resolve values through this module
instead of hardcoding amounts in formulas or controller methods.
"""

import json
from functools import lru_cache

import frappe
from frappe.utils import flt, getdate

from za_local.utils.file_utils import resolve_app_path


@lru_cache(maxsize=1)
def _load_rate_packs():
	packs = []
	data_dir = resolve_app_path("sa_setup", "data")
	for path in sorted(data_dir.glob("statutory_rates_*.json")):
		with path.open() as handle:
			pack = json.load(handle)
		if pack.get("is_active", 1):
			packs.append(pack)
	return tuple(packs)


def clear_rate_pack_cache():
	_load_rate_packs.cache_clear()


def get_tax_year_for_date(date_value) -> str:
	date_value = getdate(date_value or frappe.utils.today())
	start_year = date_value.year if date_value.month >= 3 else date_value.year - 1
	return f"{start_year}-{start_year + 1}"


def get_rate_pack(date_value=None, tax_year: str | None = None) -> dict:
	"""Return the active statutory pack for a date or tax year."""
	if tax_year is None:
		tax_year = get_tax_year_for_date(date_value)
	date_value = getdate(date_value or f"{tax_year.split('-')[0]}-03-01")

	for pack in _load_rate_packs():
		if pack.get("tax_year") != tax_year:
			continue
		start = getdate(pack.get("effective_from"))
		end = getdate(pack.get("effective_to"))
		if start <= date_value <= end:
			return pack

	frappe.throw(
		frappe._("No South African statutory rate pack is configured for {0}.").format(tax_year),
		title=frappe._("Missing Statutory Rates"),
	)


def get_nested_rate(path: str, date_value=None, default=None):
	value = get_rate_pack(date_value)
	for part in path.split("."):
		if not isinstance(value, dict) or part not in value:
			if default is not None:
				return default
			frappe.throw(
				frappe._("South African statutory rate '{0}' is not configured.").format(path),
				title=frappe._("Missing Statutory Rate"),
			)
		value = value[part]
	return value


def calculate_tax_from_brackets(annual_taxable_income, brackets):
	annual_taxable_income = flt(annual_taxable_income)
	if annual_taxable_income <= 0:
		return 0

	for bracket in brackets:
		to_amount = bracket.get("to_amount")
		if to_amount is None or annual_taxable_income <= flt(to_amount):
			return flt(bracket.get("base_tax")) + (
				annual_taxable_income - flt(bracket.get("amount_over"))
			) * flt(bracket.get("rate")) / 100
	return 0


def calculate_lump_sum_benefit_tax(amount, date_value=None, previous_lump_sums=0):
	"""Calculate retirement/severance benefit tax on an aggregate basis."""
	pack = get_rate_pack(date_value)
	brackets = pack.get("lump_sum_benefits", {}).get("brackets") or []
	current_aggregate = flt(previous_lump_sums) + flt(amount)
	previous_tax = calculate_tax_from_brackets(previous_lump_sums, brackets)
	current_tax = calculate_tax_from_brackets(current_aggregate, brackets)
	return flt(max(0, current_tax - previous_tax), 2)


def calculate_eti_from_pack(monthly_remuneration, months_employed, date_value=None, hours_per_month=None):
	eti = get_rate_pack(date_value).get("eti") or {}
	if months_employed <= 0 or months_employed > 24:
		return 0

	rows = eti.get("first_12_months" if months_employed <= 12 else "second_12_months") or []
	remuneration = flt(monthly_remuneration)
	amount = 0
	for row in rows:
		from_amount = flt(row.get("from_amount"))
		to_amount = row.get("to_amount")
		if remuneration < from_amount:
			continue
		if to_amount is not None and remuneration > flt(to_amount):
			continue

		formula_type = row.get("formula_type")
		if formula_type == "percentage":
			amount = remuneration * flt(row.get("percentage")) / 100
		elif formula_type == "declining":
			amount = flt(row.get("amount")) - (
				(remuneration - from_amount) * flt(row.get("percentage")) / 100
			)
		else:
			amount = flt(row.get("amount"))
		break

	standard_hours = flt(eti.get("hours_in_a_month")) or 160
	if hours_per_month and flt(hours_per_month) > 0 and flt(hours_per_month) < standard_hours:
		amount *= flt(hours_per_month) / standard_hours

	return flt(max(0, amount), 2)


def get_uif_monthly_cap(date_value=None):
	return flt(get_nested_rate("uif.monthly_remuneration_cap", date_value))


def get_uif_employee_rate(date_value=None):
	return flt(get_nested_rate("uif.employee_rate", date_value)) / 100


def get_uif_employer_rate(date_value=None):
	return flt(get_nested_rate("uif.employer_rate", date_value)) / 100


def get_sdl_rate(date_value=None):
	return flt(get_nested_rate("sdl.rate", date_value)) / 100


def get_reimbursive_travel_rate(date_value=None):
	return flt(get_nested_rate("travel.reimbursive_rate_per_km", date_value))


def get_default_travel_paye_inclusion_percentage(date_value=None):
	return flt(get_nested_rate("travel.fixed_allowance_default_paye_inclusion_percentage", date_value))


def get_retirement_annual_cap(date_value=None):
	return flt(get_nested_rate("retirement.annual_deduction_cap", date_value))


def get_retirement_deduction_percentage(date_value=None):
	return flt(get_nested_rate("retirement.deduction_percentage", date_value)) / 100


def get_coida_annual_earnings_cap(date_value=None):
	return flt(get_nested_rate("coida.annual_earnings_cap", date_value))
