# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, get_last_day, getdate, today

from za_local.sa_payroll.fringe_benefits.calculations import (
	calculate_low_interest_loan_period,
	get_official_interest_rate,
)


class LowInterestLoanBenefit(Document):
	def autoname(self):
		if self.employee and self.loan_start_date:
			self.name = f"{self.employee}-{self.loan_start_date}"

	def validate(self):
		self.calculation_date = self.calculation_date or today()
		if not self.loan_start_date:
			frappe.throw(_("Loan Start Date is required."))
		if getdate(self.calculation_date) < getdate(self.loan_start_date):
			frappe.throw(_("Calculation Date cannot be before Loan Start Date."))
		if flt(self.loan_amount) < 0 or flt(self.current_balance) < 0:
			frappe.throw(_("Loan Amount and Current Balance cannot be negative."))
		if flt(self.current_balance) > flt(self.loan_amount) and flt(self.loan_amount):
			frappe.throw(_("Current Balance cannot exceed the original Loan Amount."))
		if self.interest_rate in (None, ""):
			frappe.throw(_("Actual Interest Rate is required. Enter zero for an interest-free loan."))
		if flt(self.interest_rate) < 0:
			frappe.throw(_("Actual Interest Rate cannot be negative."))
		self.calculate_interest_benefit()

	@frappe.whitelist()
	def calculate_interest_benefit(self):
		"""Calculate the benefit for the calendar month of Calculation Date."""
		calculation_date = getdate(self.calculation_date or today())
		period_start = max(get_first_day(calculation_date), getdate(self.loan_start_date))
		period_end = get_last_day(calculation_date)
		result = calculate_low_interest_loan_period(
			self.current_balance,
			self.interest_rate,
			period_start,
			period_end,
		)
		rate = get_official_interest_rate(calculation_date)
		self.official_interest_rate = rate["rate"]
		self.official_rate_effective_from = rate["effective_from"]
		self.monthly_interest_benefit = result["taxable_value"]
		return result

	@frappe.whitelist()
	def get_official_rate(self):
		rate = get_official_interest_rate(self.calculation_date or today())
		self.official_interest_rate = rate["rate"]
		self.official_rate_effective_from = rate["effective_from"]
		return rate


@frappe.whitelist()
def get_current_official_rate(date_value=None):
	return get_official_interest_rate(date_value or today())
