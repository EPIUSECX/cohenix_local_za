"""Statutory fringe-benefit calculations.

Sources:
- SARS PAYE-GEN-01-G02, Guide for Employers in respect of Fringe Benefits.
- SARS Guide for Employers in respect of Employees' Tax (2027).

All percentages are expressed as percentages, not decimal fractions.
"""

from __future__ import annotations

import calendar
from collections.abc import Iterator
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate

from za_local.utils.statutory_rates import get_rate_pack


def calculate_company_car_values(
	determined_value,
	*,
	has_maintenance_plan=False,
	employee_consideration=0,
	business_use_at_least_80_percent=False,
) -> dict:
	"""Return the monthly cash equivalent and PAYE withholding value.

	The monthly cash equivalent is 3.5% of determined value, or 3.25% when
	the vehicle had a qualifying maintenance plan when acquired. PAYE is
	withheld on 80%, reduced to 20% only where the employer is satisfied that
	at least 80% of the vehicle's use will be for business purposes.
	"""
	determined_value = _non_negative(determined_value, _("Determined Value"))
	employee_consideration = _non_negative(employee_consideration, _("Employee Consideration"))
	monthly_rate = 3.25 if has_maintenance_plan else 3.5
	monthly_cash_equivalent = max(
		0,
		determined_value * monthly_rate / 100 - employee_consideration,
	)
	paye_inclusion_percentage = 20 if business_use_at_least_80_percent else 80
	monthly_paye_value = monthly_cash_equivalent * paye_inclusion_percentage / 100

	return {
		"monthly_rate": monthly_rate,
		"monthly_cash_equivalent": flt(monthly_cash_equivalent, 2),
		"paye_inclusion_percentage": paye_inclusion_percentage,
		"monthly_paye_value": flt(monthly_paye_value, 2),
	}


def calculate_housing_values(
	remuneration_proxy,
	*,
	date_value,
	room_count=0,
	furnished=False,
	power_or_fuel_provided=False,
	abatement_reduced_to_zero=False,
	provided_by="Employer",
	employer_monthly_expenditure=0,
	employee_consideration=0,
) -> dict:
	"""Calculate the paragraph 9 residential-accommodation cash equivalent."""
	remuneration_proxy = _non_negative(remuneration_proxy, _("Remuneration Proxy"))
	employer_monthly_expenditure = _non_negative(
		employer_monthly_expenditure,
		_("Employer Monthly Expenditure"),
	)
	employee_consideration = _non_negative(employee_consideration, _("Employee Consideration"))
	room_count = int(room_count or 0)
	if room_count < 0:
		frappe.throw(_("Number of Rooms cannot be negative."), title=_("Invalid Housing Benefit"))

	abatement = 0 if abatement_reduced_to_zero else get_housing_abatement(date_value)
	formula_percentage = get_housing_formula_percentage(
		room_count,
		furnished=furnished,
		power_or_fuel_provided=power_or_fuel_provided,
	)
	formula_value = max(0, remuneration_proxy - abatement) * formula_percentage / 100 / 12

	if provided_by == "Third Party":
		if employer_monthly_expenditure <= 0:
			frappe.throw(
				_("Employer Monthly Expenditure is required for third-party accommodation."),
				title=_("Missing Housing Benefit Value"),
			)
		base_value = min(formula_value, employer_monthly_expenditure)
	elif provided_by == "Employer":
		base_value = formula_value
	else:
		frappe.throw(
			_("Accommodation Provided By must be Employer or Third Party."),
			title=_("Invalid Housing Benefit"),
		)

	return {
		"statutory_abatement": flt(abatement, 2),
		"formula_percentage": formula_percentage,
		"monthly_formula_value": flt(formula_value, 2),
		"monthly_taxable_value": flt(max(0, base_value - employee_consideration), 2),
	}


def get_housing_formula_percentage(room_count, *, furnished=False, power_or_fuel_provided=False) -> int:
	"""Return paragraph 9 factor C (17%, 18%, or 19%)."""
	if int(room_count or 0) < 4:
		return 17
	services = int(bool(furnished)) + int(bool(power_or_fuel_provided))
	return 17 + services


def get_housing_abatement(date_value) -> float:
	pack = get_rate_pack(date_value)
	value = (pack.get("fringe_benefits") or {}).get("residential_accommodation_abatement")
	if value is None:
		frappe.throw(
			_("No residential-accommodation abatement is configured for {0}.").format(pack.get("tax_year")),
			title=_("Missing Fringe Benefit Statutory Rate"),
		)
	return flt(value)


def get_official_interest_rate(date_value) -> dict:
	"""Return the date-effective official interest rate (SARB policy rate + 1%)."""
	date_value = getdate(date_value)
	pack = get_rate_pack(date_value)
	rows = (pack.get("fringe_benefits") or {}).get("official_interest_rates") or []
	for row in rows:
		start = getdate(row.get("effective_from"))
		end = getdate(row.get("effective_to") or pack.get("effective_to"))
		if start <= date_value <= end and row.get("rate") is not None:
			return {
				"rate": flt(row.get("rate")),
				"effective_from": start,
				"effective_to": end,
				"source_reference": row.get("source_reference"),
			}

	frappe.throw(
		_("No official fringe-benefit interest rate is configured for {0}.").format(date_value),
		title=_("Missing Fringe Benefit Statutory Rate"),
	)


def calculate_low_interest_loan_period(
	current_balance,
	actual_interest_rate,
	period_start,
	period_end,
) -> dict:
	"""Calculate the benefit on the outstanding balance for an exact date period."""
	current_balance = _non_negative(current_balance, _("Current Balance"))
	actual_interest_rate = _non_negative(actual_interest_rate, _("Actual Interest Rate"))
	period_start = getdate(period_start)
	period_end = getdate(period_end)
	if period_end < period_start:
		frappe.throw(_("Loan benefit period end cannot be before its start."))

	benefit = 0.0
	rates_used = []
	for segment_start, segment_end, rate_row in _official_rate_segments(period_start, period_end):
		rate = flt(rate_row["rate"])
		rate_difference = max(0, rate - actual_interest_rate)
		segment_benefit = 0.0
		current = segment_start
		while current <= segment_end:
			segment_benefit += (
				current_balance * rate_difference / 100 / (366 if calendar.isleap(current.year) else 365)
			)
			current += timedelta(days=1)
		benefit += segment_benefit
		rates_used.append(
			{
				"effective_from": segment_start,
				"effective_to": segment_end,
				"official_rate": rate,
			}
		)

	return {"taxable_value": flt(benefit, 2), "rates_used": rates_used}


def prorate_monthly_value(monthly_value, period_start, period_end) -> float:
	"""Prorate a monthly cash equivalent over an inclusive date range."""
	period_start = getdate(period_start)
	period_end = getdate(period_end)
	if period_end < period_start:
		return 0.0

	total = 0.0
	month = get_first_day(period_start)
	while month <= period_end:
		month_end = get_last_day(month)
		active_start = max(period_start, month)
		active_end = min(period_end, month_end)
		days = (active_end - active_start).days + 1
		days_in_month = (month_end - month).days + 1
		total += flt(monthly_value) * days / days_in_month
		month = get_first_day(month_end + timedelta(days=1))
	return flt(total, 2)


def iter_month_breakdown(monthly_value, period_start, period_end) -> Iterator[dict]:
	"""Yield monthly proration rows for a Fringe Benefit breakdown table."""
	period_start = getdate(period_start)
	period_end = getdate(period_end)
	month = get_first_day(period_start)
	while month <= period_end:
		month_end = get_last_day(month)
		active_start = max(period_start, month)
		active_end = min(period_end, month_end)
		days = (active_end - active_start).days + 1
		yield {
			"month": month,
			"days_applicable": days,
			"taxable_value": prorate_monthly_value(monthly_value, active_start, active_end),
		}
		month = get_first_day(month_end + timedelta(days=1))


def _official_rate_segments(period_start: date, period_end: date) -> Iterator[tuple[date, date, dict]]:
	cursor = period_start
	while cursor <= period_end:
		rate_row = get_official_interest_rate(cursor)
		segment_end = min(period_end, getdate(rate_row["effective_to"]))
		yield cursor, segment_end, rate_row
		cursor = segment_end + timedelta(days=1)


def _non_negative(value, label) -> float:
	value = flt(value)
	if value < 0:
		frappe.throw(_("{0} cannot be negative.").format(label), title=_("Invalid Fringe Benefit"))
	return value
