import json
from pathlib import Path

from za_local.sa_setup.custom_fields import get_custom_field_fixtures
from za_local.tests.compat import UnitTestCase
from za_local.utils.statutory_rates import find_rate_pack, get_rate_pack


class TestStatutorySetup(UnitTestCase):
	def test_public_holiday_fixtures_match_official_2025_to_2027_dates(self):
		data_dir = Path(__file__).resolve().parents[1] / "sa_setup" / "data"
		expected = {
			2025: {"2025-04-18", "2025-04-21", "2025-04-27", "2025-04-28"},
			2026: {"2026-04-03", "2026-04-06", "2026-08-09", "2026-08-10", "2026-12-26"},
			2027: {"2027-03-21", "2027-03-22", "2027-03-26", "2027-03-29", "2027-12-27"},
		}
		actual_dates = {}
		for year, required_dates in expected.items():
			data = json.loads((data_dir / f"holiday_list_{year}.json").read_text())[0]
			dates = {row["holiday_date"] for row in data["holidays"]}
			actual_dates[year] = dates
			self.assertEqual(data["total_holidays"], len(data["holidays"]))
			self.assertTrue(required_dates.issubset(dates), required_dates - dates)
		self.assertNotIn("2026-12-28", actual_dates[2026])

	def test_all_custom_field_fixture_names_are_unique(self):
		names = [row["name"] for row in get_custom_field_fixtures()]
		self.assertEqual(len(names), len(set(names)))

	def test_controller_consumed_compliance_fields_are_owned_by_app(self):
		fixtures = {(row["dt"], row["fieldname"]) for row in get_custom_field_fixtures()}
		required = {
			("Salary Component", "za_is_annual_bonus"),
			("Salary Slip", "za_paye_inclusion_adjustment"),
			("Payroll Settings", "za_official_interest_rate"),
			("Leave Type", "za_bcea_compliant"),
			("Leave Type", "za_applicable_gender"),
			("Leave Type", "za_medical_certificate_required_after"),
			("Employee Separation", "za_termination_type"),
			("Employee Separation", "za_notice_period_days"),
			("Employee Separation", "za_severance_pay"),
			("Employee Separation", "za_leave_payout"),
		}
		self.assertTrue(required.issubset(fixtures), required - fixtures)

	def test_future_rate_pack_probe_is_non_throwing(self):
		self.assertIsNone(find_rate_pack("2027-03-01"))

	def test_future_statutory_calculation_still_fails_loudly(self):
		with self.assertRaises(Exception):
			get_rate_pack("2027-03-01")

	def test_company_contribution_is_a_standard_app_doctype(self):
		path = (
			Path(__file__).resolve().parents[1]
			/ "sa_payroll"
			/ "doctype"
			/ "company_contribution"
			/ "company_contribution.json"
		)
		data = json.loads(path.read_text())
		self.assertEqual("SA Payroll", data["module"])
		self.assertEqual(1, data["istable"])
		self.assertFalse(data.get("custom", 0))
