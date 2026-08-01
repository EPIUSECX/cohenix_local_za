from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_years, flt, getdate

from za_local.utils.coida_utils import get_coida_earnings_by_employee, get_company_industry_rate
from za_local.utils.statutory_rates import get_coida_annual_earnings_cap

DIRECTOR_DESIGNATIONS = {"Director", "Executive Director", "Managing Director"}


class COIDAAnnualReturn(Document):
	def validate(self):
		self.set_and_validate_assessment_period()
		self.calculate_assessment_fee()

	def set_and_validate_assessment_period(self):
		"""Require a 1 March to end-February assessment year."""
		if not self.fiscal_year:
			return

		fiscal_year = frappe.get_cached_doc("Fiscal Year", self.fiscal_year)
		expected_from = getdate(f"{getdate(fiscal_year.year_start_date).year}-03-01")
		expected_to = add_days(add_years(expected_from, 1), -1)
		if (
			getdate(fiscal_year.year_start_date) != expected_from
			or getdate(fiscal_year.year_end_date) != expected_to
		):
			frappe.throw(
				_(
					"Fiscal Year {0} is not a valid COIDA assessment year. Configure a Fiscal Year from "
					"1 March to the last day of February."
				).format(frappe.bold(self.fiscal_year)),
				title=_("Invalid COIDA Assessment Year"),
			)

		self.from_date = expected_from
		self.to_date = expected_to

	def calculate_assessment_fee(self):
		"""Resolve the configured rate server-side and calculate the fee."""
		if not self.company or not self.industry_class:
			self.assessment_rate = 0
			self.assessment_fee = 0
			return

		self.assessment_rate = get_company_industry_rate(self.company, self.industry_class)
		self.assessment_fee = flt(
			flt(self.total_annual_earnings) * flt(self.assessment_rate) / 100,
			2,
		)

	def on_submit(self):
		self.db_set(
			{"status": "Submitted", "submission_date": frappe.utils.today()},
			update_modified=False,
		)

	def on_cancel(self):
		self.db_set(
			{"status": "Cancelled", "submission_date": None},
			update_modified=False,
		)

	@frappe.whitelist()
	def fetch_employee_data(self):
		"""Fetch submitted payroll earnings using COIDA component applicability."""
		self.check_permission("write")
		if not self.company or not self.from_date or not self.to_date:
			frappe.throw(_("Company and assessment period are required to fetch employee data."))
		if not self.industry_class:
			frappe.throw(_("Select the company's COIDA Industry Class before fetching employee data."))

		if not frappe.db.table_exists("Salary Slip"):
			frappe.throw(
				_("Salary Slip data is unavailable. Install and configure HRMS before fetching payroll earnings.")
			)

		earnings = get_coida_earnings_by_employee(self.company, self.from_date, self.to_date)
		cap = get_coida_annual_earnings_cap(self.from_date)
		gross_total = sum(row.gross_total for row in earnings.values())
		assessable_total = sum(min(row.assessable_total, cap) for row in earnings.values())

		self.total_employees = len(earnings)
		self.uncapped_annual_earnings = flt(gross_total, 2)
		self.coida_annual_earnings_cap = cap
		self.total_annual_earnings = flt(assessable_total, 2)
		self.excluded_annual_earnings = flt(max(0, gross_total - assessable_total), 2)
		self.director_earnings = self._get_director_earnings(earnings, cap)
		self.calculate_assessment_fee()
		return self

	def _get_director_earnings(self, earnings, cap):
		if not earnings:
			return 0

		designations = frappe.get_all(
			"Employee",
			filters={"name": ["in", list(earnings)]},
			fields=["name", "designation"],
		)
		return flt(
			sum(
				min(earnings[row.name].assessable_total, cap)
				for row in designations
				if row.designation in DIRECTOR_DESIGNATIONS
			),
			2,
		)
