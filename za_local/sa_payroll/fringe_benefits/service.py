"""Translate active Fringe Benefit records into non-cash Salary Slip earnings."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate

from za_local.sa_payroll.fringe_benefits.calculations import (
	calculate_company_car_values,
	calculate_housing_values,
	calculate_low_interest_loan_period,
	prorate_monthly_value,
)

COMPANY_CAR_COMPONENT = "Company Car Benefit"
COMPANY_CAR_PAYE_ADJUSTMENT_COMPONENT = "Company Car PAYE Adjustment"
HOUSING_COMPONENT = "Housing Fringe Benefit"
LOW_INTEREST_LOAN_COMPONENT = "Low Interest Loan Fringe Benefit"
OTHER_COMPONENT = "Other Fringe Benefit"

SERVICE_COMPONENTS = {
	COMPANY_CAR_COMPONENT,
	COMPANY_CAR_PAYE_ADJUSTMENT_COMPONENT,
	HOUSING_COMPONENT,
	LOW_INTEREST_LOAN_COMPONENT,
	OTHER_COMPONENT,
}

DETAIL_CONFIG = {
	"Company Car": (
		"Company Car Benefit",
		"company_car_details",
		[
			"employee",
			"company",
			"purchase_price",
			"has_maintenance_plan",
			"employee_consideration",
			"business_use_at_least_80_percent",
		],
	),
	"Housing": (
		"Housing Benefit",
		"housing_details",
		[
			"employee",
			"remuneration_proxy",
			"room_count",
			"furnished",
			"power_or_fuel_provided",
			"abatement_reduced_to_zero",
			"owned_by",
			"monthly_rental_value",
			"employee_rental_contribution",
		],
	),
	"Low Interest Loan": (
		"Low Interest Loan Benefit",
		"loan_details",
		["employee", "loan_start_date", "current_balance", "interest_rate"],
	),
}


def get_active_fringe_benefit_rows(employee, company, period_start, period_end) -> list:
	"""Return submitted benefits overlapping a payroll period.

	Status is deliberately not used as a filter. It is a display snapshot; dates
	and docstatus are the authoritative eligibility controls.
	"""
	return frappe.get_all(
		"Fringe Benefit",
		filters={
			"employee": employee,
			"company": company,
			"docstatus": 1,
			"from_date": ["<=", period_end],
		},
		or_filters=[
			["Fringe Benefit", "to_date", ">=", period_start],
			["Fringe Benefit", "to_date", "is", "not set"],
		],
		fields=[
			"name",
			"employee",
			"company",
			"benefit_type",
			"from_date",
			"to_date",
			"benefit_value",
			"taxable_value",
			"company_car_details",
			"housing_details",
			"loan_details",
		],
		order_by="from_date, name",
	)


def build_payroll_lines(employee, company, period_start, period_end) -> list[dict]:
	"""Build aggregated non-cash earning lines for a Salary Slip period."""
	period_start = getdate(period_start)
	period_end = getdate(period_end)
	benefits = get_active_fringe_benefit_rows(employee, company, period_start, period_end)
	if not benefits:
		return []

	details = _load_details(benefits)
	amounts = defaultdict(float)
	for benefit in benefits:
		active_start = max(period_start, getdate(benefit.from_date))
		active_end = min(period_end, getdate(benefit.to_date) if benefit.to_date else period_end)
		if active_end < active_start:
			continue

		if benefit.benefit_type == "Company Car":
			detail = _required_detail(benefit, details)
			values = calculate_company_car_values(
				detail.purchase_price,
				has_maintenance_plan=detail.has_maintenance_plan,
				employee_consideration=detail.employee_consideration,
				business_use_at_least_80_percent=detail.business_use_at_least_80_percent,
			)
			cash_equivalent = prorate_monthly_value(
				values["monthly_cash_equivalent"], active_start, active_end
			)
			paye_value = cash_equivalent * values["paye_inclusion_percentage"] / 100
			amounts[COMPANY_CAR_COMPONENT] += cash_equivalent
			amounts[COMPANY_CAR_PAYE_ADJUSTMENT_COMPONENT] += paye_value - cash_equivalent
		elif benefit.benefit_type == "Housing":
			detail = _required_detail(benefit, details)
			amounts[HOUSING_COMPONENT] += _calculate_housing_period(detail, active_start, active_end)
		elif benefit.benefit_type == "Low Interest Loan":
			detail = _required_detail(benefit, details)
			loan_start = max(active_start, getdate(detail.loan_start_date))
			if loan_start <= active_end:
				amounts[LOW_INTEREST_LOAN_COMPONENT] += calculate_low_interest_loan_period(
					detail.current_balance,
					detail.interest_rate,
					loan_start,
					active_end,
				)["taxable_value"]
		else:
			monthly_value = flt(benefit.taxable_value or benefit.benefit_value)
			amounts[OTHER_COMPONENT] += prorate_monthly_value(monthly_value, active_start, active_end)

	return [
		{"salary_component": component, "amount": flt(amount, 2)}
		for component, amount in amounts.items()
		if flt(amount, 2)
	]


def apply_fringe_benefits_to_salary_slip(salary_slip) -> None:
	"""Replace service-owned rows with current, non-cash fringe-benefit values."""
	lines = build_payroll_lines(
		salary_slip.employee,
		salary_slip.company,
		salary_slip.start_date,
		salary_slip.end_date,
	)
	salary_slip.set(
		"earnings",
		[
			row
			for row in (salary_slip.get("earnings") or [])
			if row.salary_component not in SERVICE_COMPONENTS
		],
	)
	if not lines:
		return

	components = _get_salary_components({row["salary_component"] for row in lines})
	for line in lines:
		component = components[line["salary_component"]]
		salary_slip.update_component_row(
			component,
			line["amount"],
			"earnings",
			remove_if_zero_valued=1,
		)


def _load_details(benefits) -> dict[tuple[str, str], frappe._dict]:
	details = {}
	for benefit_type, (doctype, link_field, fields) in DETAIL_CONFIG.items():
		names = sorted(
			{
				benefit.get(link_field)
				for benefit in benefits
				if benefit.benefit_type == benefit_type and benefit.get(link_field)
			}
		)
		if not names:
			continue
		for row in frappe.get_all(
			doctype,
			filters={"name": ["in", names], "docstatus": 1},
			fields=["name", "docstatus", *fields],
		):
			details[(doctype, row.name)] = row
	return details


def _required_detail(benefit, details):
	doctype, link_field, _fields = DETAIL_CONFIG[benefit.benefit_type]
	name = benefit.get(link_field)
	if not name:
		frappe.throw(
			_("Fringe Benefit {0} requires a submitted {1} record.").format(benefit.name, doctype),
			title=_("Missing Fringe Benefit Detail"),
		)
	detail = details.get((doctype, name))
	if not detail:
		frappe.throw(
			_("{0} {1} linked to Fringe Benefit {2} must be submitted.").format(doctype, name, benefit.name),
			title=_("Invalid Fringe Benefit Detail"),
		)
	if detail.employee != benefit.employee:
		frappe.throw(
			_("{0} {1} belongs to a different employee than Fringe Benefit {2}.").format(
				doctype, name, benefit.name
			),
			title=_("Invalid Fringe Benefit Detail"),
		)
	if detail.get("company") and detail.company != benefit.company:
		frappe.throw(
			_("{0} {1} belongs to a different company than Fringe Benefit {2}.").format(
				doctype, name, benefit.name
			),
			title=_("Invalid Fringe Benefit Detail"),
		)
	return detail


def _calculate_housing_period(detail, period_start, period_end) -> float:
	total = 0.0
	month = get_first_day(period_start)
	while month <= period_end:
		month_end = get_last_day(month)
		active_start = max(period_start, month)
		active_end = min(period_end, month_end)
		values = calculate_housing_values(
			detail.remuneration_proxy,
			date_value=active_start,
			room_count=detail.room_count,
			furnished=detail.furnished,
			power_or_fuel_provided=detail.power_or_fuel_provided,
			abatement_reduced_to_zero=detail.abatement_reduced_to_zero,
			provided_by=detail.owned_by,
			employer_monthly_expenditure=detail.monthly_rental_value,
			employee_consideration=detail.employee_rental_contribution,
		)
		total += prorate_monthly_value(values["monthly_taxable_value"], active_start, active_end)
		month = get_first_day(month_end + timedelta(days=1))
	return flt(total, 2)


def _get_salary_components(names: set[str]) -> dict[str, frappe._dict]:
	rows = frappe.get_all(
		"Salary Component",
		filters={"name": ["in", sorted(names)]},
		fields=[
			"name",
			"salary_component",
			"abbr",
			"type",
			"disabled",
			"depends_on_payment_days",
			"do_not_include_in_total",
			"do_not_include_in_accounts",
			"is_tax_applicable",
			"is_flexible_benefit",
			"variable_based_on_taxable_salary",
			"exempted_from_income_tax",
			"accrual_component",
		],
	)
	components = {row.name: row for row in rows}
	missing = sorted(names - components.keys())
	if missing:
		frappe.throw(
			_("Required fringe-benefit Salary Components are missing: {0}.").format(", ".join(missing)),
			title=_("Incomplete Fringe Benefit Setup"),
		)

	for name, row in components.items():
		if row.disabled or row.type != "Earning":
			frappe.throw(
				_("Fringe-benefit Salary Component {0} must be an enabled Earning.").format(name),
				title=_("Invalid Fringe Benefit Setup"),
			)
		if not row.is_tax_applicable or not row.do_not_include_in_total or not row.do_not_include_in_accounts:
			frappe.throw(
				_(
					"Fringe-benefit Salary Component {0} must be taxable, excluded from totals, "
					"and excluded from accounts."
				).format(name),
				title=_("Invalid Fringe Benefit Setup"),
			)
	return components
