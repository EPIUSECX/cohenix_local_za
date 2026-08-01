from unittest.mock import Mock, patch

import frappe

from za_local.tests.compat import UnitTestCase
from za_local.utils.tax_utils import (
	calculate_south_african_tax,
	get_medical_aid_credit,
	get_tax_rebate,
	get_tax_year_dates,
)


class TestTaxUtils(UnitTestCase):
	def setUp(self):
		self.salary_slip = frappe._dict(
			company="Test Company",
			end_date="2026-09-30",
		)

	@patch("za_local.utils.tax_utils.frappe.db.get_value", return_value="2026-2027 - TC")
	@patch("za_local.utils.tax_utils.frappe.get_single")
	def test_rebate_uses_exact_company_payroll_period(self, get_single, _get_value):
		get_single.return_value = frappe._dict(
			tax_rebates_rate=[
				frappe._dict(payroll_period="Other Period", primary=1, secondary=2, tertiary=3),
				frappe._dict(payroll_period="2026-2027 - TC", primary=17820, secondary=9765, tertiary=3249),
			]
		)

		self.assertEqual(27585, get_tax_rebate(self.salary_slip, "1961-10-01"))

	@patch("za_local.utils.tax_utils.frappe.db.get_value", return_value="2026-2027 - TC")
	@patch("za_local.utils.tax_utils.frappe.get_single")
	def test_medical_credit_is_prorated_to_membership_months(self, get_single, _get_value):
		get_single.return_value = frappe._dict(
			medical_tax_credit=[
				frappe._dict(
					payroll_period="2026-2027 - TC",
					one_dependant=376,
					two_dependant=376,
					additional_dependant=254,
				)
			]
		)

		credit = get_medical_aid_credit(
			self.salary_slip,
			1,
			membership_start_date="2026-09-01",
		)
		self.assertEqual(4512, credit)

	@patch("za_local.utils.tax_utils.frappe.db.get_value", return_value="2026-2027 - TC")
	@patch("za_local.utils.tax_utils.frappe.get_single")
	def test_missing_period_specific_rate_fails_loudly(self, get_single, _get_value):
		get_single.return_value = frappe._dict(
			tax_rebates_rate=[frappe._dict(payroll_period="Wrong Period", primary=1)]
		)

		with self.assertRaises(frappe.ValidationError):
			get_tax_rebate(self.salary_slip, "1990-01-01")

	@patch("za_local.utils.hrms_detection.safe_import_hrms")
	def test_tax_calculation_passes_a_slab_document_to_hrms(self, safe_import_hrms):
		tax_calculator = Mock(return_value=(12345, 0))
		safe_import_hrms.return_value = (tax_calculator,)
		tax_slab = frappe._dict(name="2026-2027 - TC", tax_relief_limit=0)

		self.assertEqual(12345, calculate_south_african_tax(300000, tax_slab=tax_slab))
		self.assertIs(tax_slab, tax_calculator.call_args.args[1])

	def test_century_year_is_not_treated_as_a_leap_year(self):
		self.assertEqual("2100-02-28", str(get_tax_year_dates("2099-03-01")[1]))
