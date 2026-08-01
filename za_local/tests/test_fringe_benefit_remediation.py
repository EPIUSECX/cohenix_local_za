import ast
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import frappe

from za_local.sa_payroll.doctype.fringe_benefit.fringe_benefit import _assessment_year_end
from za_local.sa_payroll.fringe_benefits.calculations import (
	calculate_company_car_values,
	calculate_housing_values,
	calculate_low_interest_loan_period,
	get_housing_abatement,
	get_housing_formula_percentage,
	get_official_interest_rate,
)
from za_local.sa_payroll.fringe_benefits.salary_slip import FringeBenefitSalarySlipMixin
from za_local.sa_payroll.fringe_benefits.service import (
	COMPANY_CAR_COMPONENT,
	COMPANY_CAR_PAYE_ADJUSTMENT_COMPONENT,
	build_payroll_lines,
	get_active_fringe_benefit_rows,
)
from za_local.sa_payroll.fringe_benefits.tasks import _status_for_dates
from za_local.tests.compat import UnitTestCase


class TestFringeBenefitCalculations(UnitTestCase):
	def test_company_car_without_maintenance_uses_3_5_percent_and_80_percent_paye(self):
		values = calculate_company_car_values(600000)

		self.assertEqual(3.5, values["monthly_rate"])
		self.assertEqual(21000, values["monthly_cash_equivalent"])
		self.assertEqual(80, values["paye_inclusion_percentage"])
		self.assertEqual(16800, values["monthly_paye_value"])

	def test_company_car_maintenance_and_business_use_apply_3_25_and_20_percent(self):
		values = calculate_company_car_values(
			600000,
			has_maintenance_plan=True,
			business_use_at_least_80_percent=True,
		)

		self.assertEqual(3.25, values["monthly_rate"])
		self.assertEqual(19500, values["monthly_cash_equivalent"])
		self.assertEqual(20, values["paye_inclusion_percentage"])
		self.assertEqual(3900, values["monthly_paye_value"])

	def test_company_car_employee_consideration_reduces_cash_equivalent(self):
		values = calculate_company_car_values(600000, employee_consideration=1000)
		self.assertEqual(20000, values["monthly_cash_equivalent"])
		self.assertEqual(16000, values["monthly_paye_value"])

	def test_housing_formula_uses_2027_abatement_and_17_18_19_percent_factors(self):
		self.assertEqual(99000, get_housing_abatement("2026-08-31"))
		self.assertEqual(17, get_housing_formula_percentage(3, furnished=True, power_or_fuel_provided=True))
		self.assertEqual(17, get_housing_formula_percentage(4))
		self.assertEqual(18, get_housing_formula_percentage(4, furnished=True))
		self.assertEqual(
			19,
			get_housing_formula_percentage(4, furnished=True, power_or_fuel_provided=True),
		)

		values = calculate_housing_values(
			400000,
			date_value="2026-08-31",
			room_count=4,
			furnished=True,
			power_or_fuel_provided=True,
		)
		self.assertEqual(4765.83, values["monthly_taxable_value"])

	def test_third_party_housing_uses_lower_expenditure_then_employee_consideration(self):
		values = calculate_housing_values(
			400000,
			date_value="2026-08-31",
			room_count=4,
			provided_by="Third Party",
			employer_monthly_expenditure=3000,
			employee_consideration=500,
		)
		self.assertEqual(2500, values["monthly_taxable_value"])

	def test_missing_housing_abatement_fails_loudly(self):
		with (
			patch(
				"za_local.sa_payroll.fringe_benefits.calculations.get_rate_pack",
				return_value={"tax_year": "2099-2100"},
			),
			self.assertRaises(frappe.ValidationError),
		):
			get_housing_abatement("2099-03-01")

	def test_low_interest_loan_uses_current_balance_and_date_effective_rate(self):
		march = calculate_low_interest_loan_period(500000, 3, "2026-03-01", "2026-03-31")
		june = calculate_low_interest_loan_period(500000, 3, "2026-06-01", "2026-06-30")

		self.assertEqual(7.75, march["rates_used"][0]["official_rate"])
		self.assertEqual(2017.12, march["taxable_value"])
		self.assertEqual(8.0, june["rates_used"][0]["official_rate"])
		self.assertEqual(2054.79, june["taxable_value"])
		self.assertEqual(
			1027.4,
			calculate_low_interest_loan_period(250000, 3, "2026-06-01", "2026-06-30")["taxable_value"],
		)
		self.assertEqual(
			0, calculate_low_interest_loan_period(0, 3, "2026-06-01", "2026-06-30")["taxable_value"]
		)

	def test_official_rate_change_is_effective_from_first_day_of_next_month(self):
		self.assertEqual(7.75, get_official_interest_rate("2026-05-31")["rate"])
		self.assertEqual(8.0, get_official_interest_rate("2026-06-01")["rate"])

	def test_missing_official_interest_rate_fails_loudly(self):
		with (
			patch(
				"za_local.sa_payroll.fringe_benefits.calculations.get_rate_pack",
				return_value={"tax_year": "2099-2100", "effective_to": "2100-02-28"},
			),
			self.assertRaises(frappe.ValidationError),
		):
			get_official_interest_rate("2099-03-01")


class TestFringeBenefitPayrollIntegration(UnitTestCase):
	def test_company_car_builds_full_irp5_value_and_negative_paye_adjustment(self):
		benefit = frappe._dict(
			name="FB-1",
			employee="EMP-1",
			company="Test Company",
			benefit_type="Company Car",
			from_date="2026-08-01",
			to_date=None,
			company_car_details="CAR-1",
		)
		detail = frappe._dict(
			name="CAR-1",
			employee="EMP-1",
			company="Test Company",
			purchase_price=600000,
			has_maintenance_plan=0,
			employee_consideration=0,
			business_use_at_least_80_percent=0,
		)
		with (
			patch(
				"za_local.sa_payroll.fringe_benefits.service.get_active_fringe_benefit_rows",
				return_value=[benefit],
			),
			patch(
				"za_local.sa_payroll.fringe_benefits.service._load_details",
				return_value={("Company Car Benefit", "CAR-1"): detail},
			),
		):
			lines = build_payroll_lines("EMP-1", "Test Company", "2026-08-01", "2026-08-31")

		amounts = {row["salary_component"]: row["amount"] for row in lines}
		self.assertEqual(21000, amounts[COMPANY_CAR_COMPONENT])
		self.assertEqual(-4200, amounts[COMPANY_CAR_PAYE_ADJUSTMENT_COMPONENT])
		self.assertEqual(16800, sum(amounts.values()))

	def test_active_benefit_query_uses_dates_and_docstatus_not_stale_status(self):
		with patch("frappe.get_all", return_value=[]) as get_all:
			get_active_fringe_benefit_rows("EMP-1", "Test Company", "2026-08-01", "2026-08-31")

		filters = get_all.call_args.kwargs["filters"]
		self.assertEqual(1, filters["docstatus"])
		self.assertNotIn("status", filters)
		self.assertEqual(["<=", "2026-08-31"], filters["from_date"])

	def test_salary_component_fixtures_are_non_cash_taxable_and_correctly_mapped(self):
		path = Path(frappe.get_app_path("za_local", "sa_setup", "data", "salary_components.json"))
		components = {row["salary_component"]: row for row in json.loads(path.read_text())}
		for name in (
			"Company Car Benefit",
			"Company Car PAYE Adjustment",
			"Housing Fringe Benefit",
			"Low Interest Loan Fringe Benefit",
			"Other Fringe Benefit",
		):
			self.assertEqual(1, components[name]["is_tax_applicable"])
			self.assertEqual(1, components[name]["do_not_include_in_total"])
			self.assertEqual(1, components[name]["do_not_include_in_accounts"])

		install_path = Path(frappe.get_app_path("za_local", "sa_setup", "install.py"))
		mappings = _literal_assignment(install_path, "DEFAULT_SALARY_COMPONENT_SARS_CODES")
		excluded = _literal_assignment(install_path, "DEFAULT_IRP5_EXCLUDED_SALARY_COMPONENTS")
		self.assertEqual("3802", mappings["Company Car Benefit"])
		self.assertEqual("3805", mappings["Housing Fringe Benefit"])
		self.assertEqual("3801", mappings["Low Interest Loan Fringe Benefit"])
		self.assertIn("Company Car PAYE Adjustment", excluded)

	def test_status_and_open_ended_assessment_year_are_date_derived(self):
		current = date(2026, 8, 1)
		self.assertEqual("Pending", _status_for_dates("2026-09-01", None, current))
		self.assertEqual("Active", _status_for_dates("2026-03-01", None, current))
		self.assertEqual("Expired", _status_for_dates("2026-03-01", "2026-07-31", current))
		self.assertEqual(date(2027, 2, 28), _assessment_year_end(current))

	def test_salary_slip_extension_runs_after_standard_earning_calculation(self):
		calls = []

		class BaseSalarySlip:
			def calculate_component_amounts(self, component_type):
				calls.append(("standard", component_type))

		class ExtendedSalarySlip(FringeBenefitSalarySlipMixin, BaseSalarySlip):
			pass

		with patch(
			"za_local.sa_payroll.fringe_benefits.salary_slip.apply_fringe_benefits_to_salary_slip",
			side_effect=lambda _slip: calls.append(("fringe", "earnings")),
		):
			doc = ExtendedSalarySlip()
			doc.calculate_component_amounts("earnings")
			doc.calculate_component_amounts("deductions")

		self.assertEqual(
			[("standard", "earnings"), ("fringe", "earnings"), ("standard", "deductions")],
			calls,
		)


def _literal_assignment(path, variable_name):
	for node in ast.parse(path.read_text()).body:
		if isinstance(node, ast.Assign) and any(
			isinstance(target, ast.Name) and target.id == variable_name for target in node.targets
		):
			return ast.literal_eval(node.value)
	raise AssertionError(f"Missing assignment: {variable_name}")
