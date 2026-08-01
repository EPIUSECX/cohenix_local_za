from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import add_days, today

from za_local.sa_coida.doctype.coida_annual_return.coida_annual_return import COIDAAnnualReturn
from za_local.sa_coida.doctype.oid_claim.oid_claim import OIDClaim
from za_local.sa_coida.doctype.workplace_injury.workplace_injury import WorkplaceInjury
from za_local.sa_labour.doctype.business_trip.business_trip import (
	BusinessTrip,
	generate_allowances_for_date_range,
	get_business_trip_mileage_rate,
)
from za_local.sa_labour.doctype.business_trip_region.business_trip_region import get_active_regions
from za_local.sa_labour.report.eea2_income_differentials.eea2_income_differentials import (
	get_data as get_eea2_data,
)
from za_local.sa_labour.report_utils import get_permitted_company
from za_local.tests.compat import UnitTestCase
from za_local.utils.coida_utils import (
	get_coida_earnings_by_employee,
	get_company_industry_rate,
	get_oid_claims_for_period,
	get_workplace_injuries_for_period,
)


class TestCOIDARemediation(UnitTestCase):
	def test_persisted_salary_slip_basis_is_preferred(self):
		salary_slip_meta = MagicMock()
		salary_slip_meta.has_field.side_effect = lambda fieldname: fieldname == "za_coida_basis"
		with (
			patch("frappe.has_permission", return_value=True),
			patch("frappe.get_meta", return_value=salary_slip_meta),
			patch(
				"frappe.db.sql",
				side_effect=[
					[frappe._dict(employee="EMP-001", assessable_total=500000)],
					[frappe._dict(employee="EMP-001", gross_total=550000)],
				],
			) as sql,
		):
			result = get_coida_earnings_by_employee("Test Company", "2026-03-01", "2027-02-28")

		self.assertIn("za_coida_basis", sql.call_args_list[0].args[0])
		self.assertEqual(500000, result["EMP-001"].assessable_total)
		self.assertEqual(550000, result["EMP-001"].gross_total)

	def test_component_applicability_is_used_without_persisted_basis(self):
		salary_slip_meta = MagicMock()
		salary_slip_meta.has_field.return_value = False
		component_meta = MagicMock()
		component_meta.has_field.return_value = True
		detail_meta = MagicMock()
		detail_meta.has_field.return_value = True

		with (
			patch("frappe.has_permission", return_value=True),
			patch("frappe.get_meta", side_effect=[salary_slip_meta, component_meta, detail_meta]),
			patch(
				"frappe.db.sql",
				side_effect=[
					[frappe._dict(employee="EMP-001", assessable_total=400000)],
					[frappe._dict(employee="EMP-001", gross_total=425000)],
				],
			) as sql,
		):
			result = get_coida_earnings_by_employee("Test Company", "2026-03-01", "2027-02-28")

		basis_query = sql.call_args_list[0].args[0]
		self.assertIn("sc.za_coida_applicable", basis_query)
		self.assertIn("sd.parentfield = 'earnings'", basis_query)
		self.assertEqual(400000, result["EMP-001"].assessable_total)

	def test_company_scoped_industry_rate_wins_over_legacy_row(self):
		settings = frappe._dict(
			industry_rates=[
				frappe._dict(company=None, industry_class="Class 1", assessment_rate=1.1),
				frappe._dict(company="Test Company", industry_class="Class 1", assessment_rate=1.25),
			]
		)
		with patch("frappe.get_single", return_value=settings):
			self.assertEqual(1.25, get_company_industry_rate("Test Company", "Class 1"))

	def test_period_helpers_use_correct_fields_and_permission_filtered_lists(self):
		with patch("frappe.get_list", return_value=[]) as get_list:
			get_workplace_injuries_for_period("Test Company", "2026-03-01", "2027-02-28")
			injury_call = get_list.call_args
			self.assertIn("injury_date", injury_call.kwargs["filters"])
			self.assertNotIn("injury_description", injury_call.kwargs["fields"])

		with patch("frappe.get_list", return_value=[]) as get_list:
			get_oid_claims_for_period(
				"Test Company", "2026-03-01", "2027-02-28", status="Under Review"
			)
			claim_call = get_list.call_args
			self.assertEqual("Under Review", claim_call.kwargs["filters"]["claim_status"])
			self.assertNotIn("medical_reports", claim_call.kwargs["fields"])

	def test_oid_claim_state_machine_rejects_reverse_transition(self):
		doc = frappe.new_doc("OID Claim")
		with self.assertRaises(frappe.ValidationError):
			OIDClaim._validate_transition(doc, "Approved", "Under Review")

	def test_oid_claim_parent_rejects_future_medical_report(self):
		doc = frappe.new_doc("OID Claim")
		doc.claim_status = "Submitted"
		doc.medical_reports = [
			frappe._dict(idx=1, report_date=add_days(today(), 1), report_type="Progress Report")
		]
		with self.assertRaises(frappe.ValidationError):
			OIDClaim.validate_medical_reports(doc)

	def test_workplace_injury_claim_creation_failure_propagates(self):
		doc = frappe.new_doc("Workplace Injury")
		doc.name = "INJ-TEST"
		doc.employee = "EMP-001"
		doc.company = "Test Company"
		doc.injury_date = "2026-04-01"
		doc.injury_type = "Moderate"
		doc.injury_location = "Warehouse"
		doc.injury_description = "Test injury"
		claim = MagicMock()
		claim.insert.side_effect = frappe.ValidationError("claim insert failed")
		with patch("frappe.new_doc", return_value=claim):
			with self.assertRaises(frappe.ValidationError):
				WorkplaceInjury.create_oid_claim(doc)

	def test_health_doctypes_do_not_grant_employee_role_access(self):
		app_path = Path(frappe.get_app_path("za_local"))
		for relative_path in (
			"sa_coida/doctype/workplace_injury/workplace_injury.json",
			"sa_coida/doctype/oid_claim/oid_claim.json",
		):
			payload = json.loads((app_path / relative_path).read_text())
			self.assertNotIn("Employee", {row["role"] for row in payload["permissions"]})

	def test_non_march_fiscal_year_is_rejected_for_coida_return(self):
		doc = frappe.new_doc("COIDA Annual Return")
		doc.fiscal_year = "Calendar 2026"
		calendar_year = frappe._dict(year_start_date="2026-01-01", year_end_date="2026-12-31")
		with (
			patch("frappe.get_cached_doc", return_value=calendar_year),
			self.assertRaises(frappe.ValidationError),
		):
			COIDAAnnualReturn.set_and_validate_assessment_period(doc)


class TestSALabourRemediation(UnitTestCase):
	def test_active_region_query_requires_read_permission(self):
		with (
			patch("frappe.has_permission") as has_permission,
			patch("frappe.db.sql", return_value=[]),
		):
			get_active_regions(None, "", "name", 0, 20, {})

		has_permission.assert_called_once_with("Business Trip Region", "read", throw=True)

	def test_manager_employee_is_mapped_to_manager_user(self):
		doc = frappe.new_doc("Business Trip")
		doc.employee = "EMP-001"
		with patch(
			"frappe.get_cached_value",
			side_effect=[
				frappe._dict(expense_approver=None, reports_to="EMP-MANAGER"),
				"manager@example.com",
			],
		):
			self.assertEqual("manager@example.com", BusinessTrip._get_expense_approver(doc))

	def test_mileage_rate_falls_back_to_date_effective_pack(self):
		with (
			patch("frappe.get_cached_doc", return_value=frappe._dict(mileage_allowance_rate=0)),
			patch(
				"za_local.sa_labour.doctype.business_trip.business_trip.get_reimbursive_travel_rate",
				return_value=4.95,
			) as statutory_rate,
		):
			self.assertEqual(4.95, get_business_trip_mileage_rate("2026-04-01"))
		statutory_rate.assert_called_once_with("2026-04-01")

	def test_allowance_generation_requires_region_and_write_permission(self):
		trip = MagicMock()
		trip.docstatus = 0
		trip.from_date = "2026-04-01"
		trip.to_date = "2026-04-03"
		with (
			patch("frappe.get_doc", return_value=trip),
			self.assertRaises(frappe.ValidationError),
		):
			generate_allowances_for_date_range("TRIP-001", None)
		trip.check_permission.assert_called_once_with("write")

	def test_report_requires_a_permitted_company(self):
		with self.assertRaises(frappe.ValidationError):
			get_permitted_company({})

		with patch("frappe.has_permission", return_value=True) as has_permission:
			self.assertEqual("Test Company", get_permitted_company({"company": "Test Company"}))
		has_permission.assert_called_once_with("Company", "read", "Test Company", throw=True)

	def test_eea2_query_joins_only_latest_salary_assignment(self):
		with (
			patch(
				"za_local.sa_labour.report.eea2_income_differentials.eea2_income_differentials.get_permitted_company",
				return_value="Test Company",
			),
			patch(
				"za_local.sa_labour.report.eea2_income_differentials.eea2_income_differentials.validate_employee_fields"
			),
			patch("frappe.db.sql", return_value=[]) as sql,
		):
			get_eea2_data({"company": "Test Company"})

		query = sql.call_args.args[0]
		self.assertIn("SELECT latest.name", query)
		self.assertIn("ORDER BY latest.from_date DESC", query)
		self.assertIn("LIMIT 1", query)
