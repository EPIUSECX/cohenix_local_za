# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, get_first_day, get_last_day, getdate, today

from za_local.sa_payroll.fringe_benefits.calculations import (
	calculate_company_car_values,
	calculate_housing_values,
	calculate_low_interest_loan_period,
	iter_month_breakdown,
)

DETAIL_FIELDS = {
	"Company Car": ("Company Car Benefit", "company_car_details"),
	"Housing": ("Housing Benefit", "housing_details"),
	"Low Interest Loan": ("Low Interest Loan Benefit", "loan_details"),
}


class FringeBenefit(Document):
	def validate(self):
		self.validate_dates()
		self.validate_detail_link()
		self.calculate_taxable_value()
		self.status = self.get_status()

	def before_submit(self):
		self.generate_monthly_breakdown()

	def on_submit(self):
		self.db_set("status", self.get_status(), update_modified=False)

	def on_cancel(self):
		self.db_set("status", "Inactive", update_modified=False)

	def validate_dates(self):
		if not self.from_date:
			frappe.throw(_("From Date is required."))
		if self.to_date and getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))

	def validate_detail_link(self):
		config = DETAIL_FIELDS.get(self.benefit_type)
		if not config:
			return
		doctype, link_field = config
		name = self.get(link_field)
		if not name:
			frappe.throw(
				_("{0} is required for a {1} fringe benefit.").format(doctype, self.benefit_type),
				title=_("Missing Fringe Benefit Detail"),
			)
		detail = frappe.get_doc(doctype, name)
		if detail.docstatus != 1:
			frappe.throw(
				_("{0} {1} must be submitted before it can be used.").format(doctype, name),
				title=_("Unsubmitted Fringe Benefit Detail"),
			)
		if detail.employee != self.employee:
			frappe.throw(_("The linked {0} belongs to a different employee.").format(doctype))
		if detail.get("company") and detail.company != self.company:
			frappe.throw(_("The linked {0} belongs to a different company.").format(doctype))
		if self.benefit_type == "Low Interest Loan" and getdate(self.from_date) < getdate(
			detail.loan_start_date
		):
			frappe.throw(_("Fringe Benefit From Date cannot be before the Loan Start Date."))

	def get_status(self, date_value=None):
		if self.docstatus == 2:
			return "Inactive"
		date_value = getdate(date_value or today())
		if getdate(self.from_date) > date_value:
			return "Pending"
		if self.to_date and getdate(self.to_date) < date_value:
			return "Expired"
		return "Active" if self.docstatus == 1 else "Inactive"

	@frappe.whitelist()
	def calculate_taxable_value(self, date_value=None):
		"""Set the full monthly cash equivalent used for IRP5 reporting."""
		date_value = getdate(date_value or max(getdate(self.from_date), getdate(today())))
		if self.benefit_type == "Company Car":
			detail = frappe.get_doc("Company Car Benefit", self.company_car_details)
			self.taxable_value = calculate_company_car_values(
				detail.purchase_price,
				has_maintenance_plan=detail.has_maintenance_plan,
				employee_consideration=detail.employee_consideration,
				business_use_at_least_80_percent=detail.business_use_at_least_80_percent,
			)["monthly_cash_equivalent"]
		elif self.benefit_type == "Housing":
			detail = frappe.get_doc("Housing Benefit", self.housing_details)
			self.taxable_value = _housing_monthly_value(detail, date_value)
		elif self.benefit_type == "Low Interest Loan":
			detail = frappe.get_doc("Low Interest Loan Benefit", self.loan_details)
			month_start = max(get_first_day(date_value), getdate(detail.loan_start_date))
			self.taxable_value = calculate_low_interest_loan_period(
				detail.current_balance,
				detail.interest_rate,
				month_start,
				get_last_day(date_value),
			)["taxable_value"]
		else:
			self.taxable_value = flt(self.benefit_value)
		return self.taxable_value

	@frappe.whitelist()
	def generate_monthly_breakdown(self):
		"""Regenerate monthly values, extending open benefits to tax-year end."""
		self.set("monthly_breakdown", [])
		period_start = getdate(self.from_date)
		period_end = (
			getdate(self.to_date)
			if self.to_date
			else _assessment_year_end(max(period_start, getdate(today())))
		)
		month = get_first_day(period_start)
		while month <= period_end:
			month_start = max(month, period_start)
			month_end = min(get_last_day(month), period_end)
			monthly_value = self._get_month_value(month_start, month_end)
			for row in iter_month_breakdown(monthly_value, month_start, month_end):
				self.append("monthly_breakdown", row)
			month = add_months(month, 1)

	def _get_month_value(self, month_start, month_end):
		if self.benefit_type == "Housing":
			return _housing_monthly_value(
				frappe.get_doc("Housing Benefit", self.housing_details), month_start
			)
		if self.benefit_type == "Low Interest Loan":
			detail = frappe.get_doc("Low Interest Loan Benefit", self.loan_details)
			loan_start = max(month_start, getdate(detail.loan_start_date))
			if loan_start > month_end:
				return 0
			# Return a full-month equivalent so the common proration below remains correct.
			active_value = calculate_low_interest_loan_period(
				detail.current_balance,
				detail.interest_rate,
				loan_start,
				month_end,
			)["taxable_value"]
			active_days = (month_end - loan_start).days + 1
			month_days = (get_last_day(month_start) - get_first_day(month_start)).days + 1
			return active_value * month_days / active_days
		return flt(self.taxable_value)

	def get_monthly_tax_impact(self, month):
		month_start = get_first_day(month)
		for row in self.monthly_breakdown:
			if getdate(row.month) == month_start:
				return flt(row.taxable_value)
		return 0.0


def _housing_monthly_value(detail, date_value):
	return calculate_housing_values(
		detail.remuneration_proxy,
		date_value=date_value,
		room_count=detail.room_count,
		furnished=detail.furnished,
		power_or_fuel_provided=detail.power_or_fuel_provided,
		abatement_reduced_to_zero=detail.abatement_reduced_to_zero,
		provided_by=detail.owned_by,
		employer_monthly_expenditure=detail.monthly_rental_value,
		employee_consideration=detail.employee_rental_contribution,
	)["monthly_taxable_value"]


def _assessment_year_end(date_value) -> date:
	date_value = getdate(date_value)
	end_year = date_value.year + 1 if date_value.month >= 3 else date_value.year
	return date(end_year, 2, 29 if _is_leap_year(end_year) else 28)


def _is_leap_year(year):
	return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


@frappe.whitelist()
def get_active_fringe_benefits(employee, date=None):
	"""Return submitted benefits active on a date, subject to read permission."""
	if not frappe.has_permission("Fringe Benefit", "read"):
		frappe.throw(
			_("You are not permitted to read Fringe Benefits."),
			frappe.PermissionError,
			title=_("Insufficient Permission"),
		)
	date = getdate(date or today())
	return frappe.get_list(
		"Fringe Benefit",
		filters={"employee": employee, "docstatus": 1, "from_date": ["<=", date]},
		or_filters=[
			["Fringe Benefit", "to_date", ">=", date],
			["Fringe Benefit", "to_date", "is", "not set"],
		],
		fields=["name", "benefit_type", "taxable_value"],
	)
