"""Regression tests for the backfilled prior-year statutory rate packs.

These packs (2024-2025 and 2025-2026) exist so that date-effective payroll
calculations for prior tax years resolve through the statutory rate engine
instead of raising "No statutory rate pack configured". The high-confidence
values (PAYE brackets, rebates, thresholds, medical tax credits) are asserted
here. Annually-gazetted figures that were carried forward (travel per-km,
subsistence, COIDA cap, and the ETI band amounts around the 2025 increase) are
flagged in each pack's ``verification_notes`` block and are intentionally not
asserted as authoritative here.
"""

import json
from pathlib import Path

import frappe

from za_local.tests.compat import UnitTestCase
from za_local.utils.eti_utils import calculate_months_employed
from za_local.utils.statutory_rates import (
	calculate_eti_from_pack,
	calculate_tax_from_brackets,
	get_rate_pack,
	get_uif_monthly_cap,
)

PRIOR_YEAR_PACKS = {
	"2024-2025": {"date": "2024-03-31", "file": "statutory_rates_2025.json"},
	"2025-2026": {"date": "2025-03-31", "file": "statutory_rates_2026.json"},
}


class TestSAPayrollCompliancePriorYears(UnitTestCase):
	def test_all_tax_years_resolve_without_throwing(self):
		# The original gap: get_rate_pack threw for any date before 2026-03-01.
		for date_value in ("2024-03-31", "2025-03-31", "2026-03-31"):
			pack = get_rate_pack(date_value)
			self.assertIn("paye", pack)

	def test_prior_year_packs_have_expected_metadata_and_paye(self):
		for tax_year, meta in PRIOR_YEAR_PACKS.items():
			pack = get_rate_pack(meta["date"])
			self.assertEqual(tax_year, pack["tax_year"])
			# Brackets were frozen at 2024-2025 levels across both years.
			self.assertEqual(17235, pack["paye"]["rebates"]["primary"])
			self.assertEqual(9444, pack["paye"]["rebates"]["secondary"])
			self.assertEqual(3145, pack["paye"]["rebates"]["tertiary"])
			self.assertEqual(95750, pack["paye"]["thresholds"]["under_65"])
			self.assertEqual(7, len(pack["paye"]["brackets"]))
			self.assertEqual(17712, get_uif_monthly_cap(meta["date"]))
			self.assertEqual(364, pack["medical_tax_credit"]["main_member"])
			self.assertEqual(246, pack["medical_tax_credit"]["additional_dependant"])

	def test_prior_year_paye_brackets_compute_correctly(self):
		for meta in PRIOR_YEAR_PACKS.values():
			brackets = get_rate_pack(meta["date"])["paye"]["brackets"]
			self.assertEqual(18000, calculate_tax_from_brackets(100000, brackets))
			self.assertEqual(59032, calculate_tax_from_brackets(300000, brackets))
			self.assertEqual(189677, calculate_tax_from_brackets(700000, brackets))

	def test_prior_year_eti_uses_legacy_band_structure(self):
		# Prior years use the legacy R1000 / R500 ETI structure (max R1000 in the
		# first 12 months), matching the repo's eti_slabs_2025.json.
		for meta in PRIOR_YEAR_PACKS.values():
			d = meta["date"]
			self.assertEqual(750, calculate_eti_from_pack(1500, 1, d))   # 50% band
			self.assertEqual(1000, calculate_eti_from_pack(3000, 1, d))  # fixed band
			self.assertEqual(500, calculate_eti_from_pack(5500, 1, d))   # declining band
			self.assertEqual(0, calculate_eti_from_pack(6500, 1, d))     # above ceiling
			self.assertEqual(500, calculate_eti_from_pack(3000, 13, d))  # second period

	def test_prior_year_pack_json_is_valid_and_flags_verification(self):
		for tax_year, meta in PRIOR_YEAR_PACKS.items():
			path = Path(frappe.get_app_path("za_local", "sa_setup", "data", meta["file"]))
			data = json.loads(path.read_text())
			self.assertEqual(tax_year, data["tax_year"])
			self.assertEqual(7, len(data["paye"]["brackets"]))
			self.assertEqual(4, len(data["eti"]["first_12_months"]))
			# Carried-forward annual figures must remain flagged for verification.
			self.assertIn("verification_notes", data)
			self.assertIn("coida.annual_earnings_cap", data["verification_notes"]["verify_before_use"])


class TestETIMonthsEmployed(UnitTestCase):
	"""Lock in the calendar-month ETI count (joining month is month 1)."""

	def test_joining_month_counts_as_month_one(self):
		self.assertEqual(1, calculate_months_employed("2024-01-15", "2024-01-31"))

	def test_subsequent_calendar_month_increments(self):
		self.assertEqual(2, calculate_months_employed("2024-01-15", "2024-02-10"))

	def test_month_end_joiner_is_not_undercounted(self):
		# Previously a 31st-of-month joiner was undercounted the following month
		# because the day-of-month comparison failed.
		self.assertEqual(2, calculate_months_employed("2024-01-31", "2024-02-01"))

	def test_twelfth_and_thirteenth_month_boundary(self):
		self.assertEqual(12, calculate_months_employed("2024-01-01", "2024-12-01"))
		self.assertEqual(13, calculate_months_employed("2023-01-01", "2024-01-01"))

	def test_current_date_before_joining_returns_zero(self):
		self.assertEqual(0, calculate_months_employed("2024-02-01", "2024-01-01"))
