from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from za_local.sa_payroll.doctype.emp201_submission.emp201_submission import calculate_eti_utilisation
from za_local.tests.compat import UnitTestCase
from za_local.utils import eti_utils, payroll_utils


class TestAdditionalSalarySelection(UnitTestCase):
	@patch.object(payroll_utils.frappe, "get_all")
	@patch.object(payroll_utils, "hrms_get_additional_salaries")
	def test_regular_additional_salary_preserves_hrms_aliases(self, get_hrms_salaries, get_all):
		selected = frappe._dict(
			name="AS-REC-1",
			component="Recurring Allowance",
			amount=1500,
			is_recurring=1,
			overwrite=1,
			ref_doctype="Employee Benefit Claim",
		)
		get_hrms_salaries.return_value = [selected]
		get_all.return_value = [
			frappe._dict(
				name=selected.name,
				za_is_company_contribution=0,
				ref_docname="EBC-0001",
			)
		]

		result = payroll_utils.get_additional_salaries("EMP-1", "2026-03-01", "2026-03-31", "earnings")

		self.assertEqual(result, [selected])
		self.assertEqual(result[0].component, "Recurring Allowance")
		self.assertEqual(result[0].overwrite, 1)
		self.assertEqual(result[0].ref_docname, "EBC-0001")
		get_hrms_salaries.assert_called_once_with("EMP-1", "2026-03-01", "2026-03-31", "earnings")

	@patch.object(payroll_utils.frappe, "get_all")
	@patch.object(payroll_utils, "hrms_get_additional_salaries")
	def test_company_contributions_are_partitioned_from_both_hrms_types(self, get_hrms_salaries, get_all):
		earning = frappe._dict(name="AS-EARN", component="UIF Employer")
		deduction = frappe._dict(name="AS-DED", component="SDL Employer")
		get_hrms_salaries.side_effect = [[earning], [deduction]]
		get_all.return_value = [
			frappe._dict(name="AS-EARN", za_is_company_contribution=1, ref_docname=None),
			frappe._dict(name="AS-DED", za_is_company_contribution=0, ref_docname=None),
		]

		result = payroll_utils.get_additional_salaries(
			"EMP-1", "2026-03-01", "2026-03-31", "company_contributions"
		)

		self.assertEqual(result, [earning])
		self.assertEqual(get_hrms_salaries.call_count, 2)


class TestEmployerEtiUtilisation(UnitTestCase):
	def test_eti_utilisation_is_capped_at_employer_paye_liability(self):
		result = calculate_eti_utilisation(10_000, 12_000, 2_000, "2026-07-01")

		self.assertEqual(result.eti_utilized_current_month, 10_000)
		self.assertEqual(result.net_paye_payable, 0)
		self.assertEqual(result.eti_to_be_carried_forward, 4_000)

	def test_september_opening_balance_is_always_zero(self):
		result = calculate_eti_utilisation(5_000, 2_000, 8_000, "2026-09-01")

		self.assertEqual(result.eti_carried_forward_from_previous, 0)
		self.assertEqual(result.total_eti_available, 2_000)
		self.assertEqual(result.eti_reconciliation_refund, 0)

	def test_august_unused_eti_is_ring_fenced_for_refund(self):
		result = calculate_eti_utilisation(5_000, 4_000, 3_000, "2026-08-01")

		self.assertEqual(result.eti_utilized_current_month, 5_000)
		self.assertEqual(result.eti_to_be_carried_forward, 0)
		self.assertEqual(result.eti_reconciliation_refund, 2_000)


class TestEtiCalculationQueries(UnitTestCase):
	@patch.object(eti_utils, "check_eti_eligibility")
	def test_calculation_passes_remuneration_into_eligibility(self, check_eligibility):
		check_eligibility.return_value = {"eligible": False}
		slip = SimpleNamespace(end_date="2026-03-31")

		amount = eti_utils.calculate_eti_amount("EMP-1", slip, 4_000)

		self.assertEqual(amount, 0)
		check_eligibility.assert_called_once_with("EMP-1", slip, 4_000)

	@patch.object(eti_utils.frappe, "new_doc")
	@patch.object(eti_utils.frappe.db, "exists", return_value=None)
	def test_eti_log_records_qualifying_month_evidence(self, _exists, new_doc):
		log = frappe._dict(docstatus=0, save=Mock())
		new_doc.return_value = log
		eligibility = frappe._dict(
			eligible=True,
			reason="Employee qualifies for ETI",
			months_employed=6,
			hours_per_month=160,
			monthly_remuneration=5_000,
			wage_paid=4_900,
			minimum_wage=4_800,
		)
		slip = SimpleNamespace(name="SS-1", employee_name="Test Employee", end_date="2026-08-31")

		eti_utils.log_eti_calculation("EMP-1", slip, 1_500, eligibility)

		self.assertEqual(log.is_qualifying_month, 1)
		self.assertEqual(log.qualifying_month_number, 6)
		self.assertEqual(log.minimum_wage, 4_800)
		log.save.assert_called_once_with(ignore_permissions=True)

	@patch.object(eti_utils.frappe, "get_doc")
	@patch.object(eti_utils.frappe.db, "exists", return_value="ETI-LOG-1")
	def test_eti_log_submits_with_salary_slip(self, _exists, get_doc):
		log = frappe._dict(docstatus=0, submit=Mock())
		get_doc.return_value = log

		eti_utils.submit_eti_log("EMP-1", SimpleNamespace(name="SS-1"))

		log.submit.assert_called_once_with()

	@patch.object(eti_utils, "calculate_months_employed")
	@patch.object(eti_utils.frappe, "get_all")
	def test_qualifying_month_uses_distinct_submitted_log_months(self, get_all, calculate_calendar_months):
		get_all.return_value = [
			frappe._dict(date="2026-03-31", is_qualifying_month=1, eti_amount=1_500),
			frappe._dict(date="2026-03-15", is_qualifying_month=1, eti_amount=500),
			frappe._dict(date="2026-04-30", is_qualifying_month=0, eti_amount=0),
			frappe._dict(date="2026-05-31", is_qualifying_month=0, eti_amount=750),
		]

		month_number = eti_utils.get_eti_qualifying_month_number(
			"EMP-1",
			SimpleNamespace(name="SS-JUNE", end_date="2026-06-30"),
			"2025-01-01",
		)

		self.assertEqual(month_number, 3)
		calculate_calendar_months.assert_not_called()
		self.assertEqual(get_all.call_args.kwargs["filters"]["docstatus"], 1)

	@patch.object(eti_utils, "calculate_months_employed", return_value=7)
	@patch.object(eti_utils.frappe, "get_all", return_value=[])
	def test_qualifying_month_uses_calendar_fallback_only_without_history(
		self, _get_all, calculate_calendar_months
	):
		month_number = eti_utils.get_eti_qualifying_month_number(
			"EMP-1",
			SimpleNamespace(name="SS-1", end_date="2026-06-30"),
			"2025-12-01",
		)

		self.assertEqual(month_number, 7)
		calculate_calendar_months.assert_called_once()

	@patch.object(eti_utils.frappe, "get_cached_value", return_value=1)
	def test_unregulated_minimum_wage_is_prorated_to_ordinary_hours(self, _get_component_flag):
		employee = frappe._dict(za_eti_minimum_wage_basis=eti_utils.WAGE_BASIS_UNREGULATED)
		settings = frappe._dict(za_eti_unregulated_minimum_monthly_wage=2_500)
		slip = frappe._dict(
			earnings=[frappe._dict(salary_component="Basic Salary", amount=1_250)]
		)

		result = eti_utils.check_eti_minimum_wage(employee, slip, settings, 2_000, 80)

		self.assertTrue(result.eligible)
		self.assertEqual(result.minimum_wage, 1_250)

	@patch.object(eti_utils.frappe, "get_cached_value", return_value=1)
	def test_regulated_minimum_wage_rejects_underpayment(self, _get_component_flag):
		employee = frappe._dict(
			za_eti_minimum_wage_basis=eti_utils.WAGE_BASIS_REGULATED,
			za_eti_minimum_wage_rate=30,
		)
		slip = frappe._dict(
			earnings=[frappe._dict(salary_component="Basic Salary", amount=4_700)]
		)

		result = eti_utils.check_eti_minimum_wage(employee, slip, frappe._dict(), 5_000, 160)

		self.assertFalse(result.eligible)
		self.assertEqual(result.minimum_wage, 4_800)

	@patch.object(eti_utils.frappe, "get_cached_doc")
	def test_domestic_worker_is_excluded_before_eti_calculation(self, get_cached_doc):
		get_cached_doc.side_effect = [
			frappe._dict(za_is_domestic_worker=1, za_hours_per_month=160),
			frappe._dict(za_disable_eti_calculation=0),
		]

		result = eti_utils.check_eti_eligibility(
			"EMP-1", frappe._dict(end_date="2026-06-30"), 5_000
		)

		self.assertFalse(result.eligible)
		self.assertIn("Domestic", result.reason)

	@patch.object(eti_utils.frappe, "get_cached_doc")
	def test_connected_person_is_excluded_before_eti_calculation(self, get_cached_doc):
		get_cached_doc.side_effect = [
			frappe._dict(za_is_connected_person_to_employer=1, za_hours_per_month=160),
			frappe._dict(za_disable_eti_calculation=0),
		]

		result = eti_utils.check_eti_eligibility(
			"EMP-1", frappe._dict(end_date="2026-06-30"), 5_000
		)

		self.assertFalse(result.eligible)
		self.assertIn("Connected", result.reason)

	@patch.object(eti_utils, "find_rate_pack", return_value={"tax_year": "2026-2027"})
	@patch.object(eti_utils, "calculate_eti_from_pack", return_value=1_500)
	@patch.object(eti_utils, "check_eti_eligibility")
	def test_calculate_eti_accepts_precomputed_eligibility(
		self, check_eligibility, calculate_pack, _find_rate_pack
	):
		eligibility = {
			"eligible": True,
			"months_employed": 4,
			"hours_per_month": 80,
		}
		slip = SimpleNamespace(end_date="2026-03-31")

		amount = eti_utils.calculate_eti_amount("EMP-1", slip, 4_000, eligibility=eligibility)

		self.assertEqual(amount, 1_500)
		check_eligibility.assert_not_called()
		calculate_pack.assert_called_once_with(4_000, 4, "2026-03-31", hours_per_month=80)

	@patch.object(eti_utils, "find_rate_pack", return_value={"tax_year": "2026-2027"})
	@patch.object(eti_utils, "calculate_eti_from_pack", side_effect=ValueError("malformed pack"))
	def test_malformed_rate_pack_error_is_not_swallowed(self, _calculate_pack, _find_rate_pack):
		eligibility = {
			"eligible": True,
			"months_employed": 4,
			"hours_per_month": 160,
		}

		with self.assertRaisesRegex(ValueError, "malformed pack"):
			eti_utils.calculate_eti_amount(
				"EMP-1",
				SimpleNamespace(end_date="2026-03-31"),
				4_000,
				eligibility=eligibility,
			)

	@patch.object(eti_utils, "find_rate_pack", return_value=None)
	@patch.object(eti_utils, "get_eti_slab")
	def test_missing_pack_uses_date_effective_legacy_slab(self, get_slab, _find_rate_pack):
		get_slab.return_value = frappe._dict(
			hours_in_a_month=160,
			eti_slab_details=[
				frappe._dict(
					from_amount=2_000,
					to_amount=4_499.99,
					percentage=0,
					eti_amount=1_500,
					first_qualifying_12_months=1,
					second_qualifying_12_months=0,
				)
			],
		)
		eligibility = {
			"eligible": True,
			"months_employed": 4,
			"hours_per_month": 160,
		}

		amount = eti_utils.calculate_eti_amount(
			"EMP-1",
			SimpleNamespace(end_date="2021-03-31"),
			3_000,
			eligibility=eligibility,
		)

		self.assertEqual(amount, 1_500)
		get_slab.assert_called_once_with(4, "2021-03-31")

	@patch.object(eti_utils, "find_rate_pack", return_value=None)
	@patch.object(eti_utils, "get_eti_slab", return_value=None)
	def test_missing_pack_and_legacy_slab_fails_loudly(self, _get_slab, _find_rate_pack):
		eligibility = {
			"eligible": True,
			"months_employed": 4,
			"hours_per_month": 160,
		}

		with self.assertRaises(frappe.ValidationError):
			eti_utils.calculate_eti_amount(
				"EMP-1",
				SimpleNamespace(end_date="2021-03-31"),
				3_000,
				eligibility=eligibility,
			)

	@patch.object(eti_utils, "find_rate_pack", return_value=None)
	@patch.object(eti_utils, "get_eti_slab")
	def test_legacy_fallback_grosses_up_remuneration_before_bracket_selection(
		self, get_slab, _find_rate_pack
	):
		get_slab.return_value = frappe._dict(
			hours_in_a_month=160,
			eti_slab_details=[
				frappe._dict(
					from_amount=0,
					to_amount=6_499.99,
					percentage=0,
					eti_amount=1_500,
					first_qualifying_12_months=1,
					second_qualifying_12_months=0,
				)
			],
		)
		eligibility = {
			"eligible": True,
			"months_employed": 4,
			"hours_per_month": 80,
		}

		amount = eti_utils.calculate_eti_amount(
			"EMP-1",
			SimpleNamespace(end_date="2021-03-31"),
			4_000,
			eligibility=eligibility,
		)

		self.assertEqual(amount, 0)

	@patch.object(eti_utils.frappe, "get_doc", return_value="selected-slab")
	@patch.object(eti_utils.frappe, "get_all")
	def test_legacy_slab_lookup_is_bounded_by_payroll_date(self, get_all, _get_doc):
		get_all.return_value = [frappe._dict(name="ETI-2024-FIRST")]

		result = eti_utils.get_eti_slab(1, "2024-03-31")

		self.assertEqual(result, "selected-slab")
		self.assertEqual(
			get_all.call_args.kwargs["filters"]["start_date"],
			["<=", frappe.utils.getdate("2024-03-31")],
		)
