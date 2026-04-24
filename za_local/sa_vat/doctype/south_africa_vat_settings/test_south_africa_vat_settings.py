from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from za_local.sa_vat.doctype.vat201_return.vat201_return import VAT201Return
from za_local.sa_vat.setup import (
	CLASSIFICATION_OPTIONS,
	DEFAULT_VAT_VENDOR_TYPES,
	ITEM_VAT_CATEGORY_OPTIONS,
	get_default_vat_vendor_type,
	seed_vat_vendor_types,
	sync_vat_accounts,
)
from za_local.sa_vat.tax_invoice import (
	FULL_TAX_INVOICE_THRESHOLD,
	NO_TAX_INVOICE_THRESHOLD,
	build_sales_invoice_print_profile,
	get_invoice_type,
)


class TestSouthAfricaVATSettings(UnitTestCase):
	def test_vat_custom_field_options_exist(self):
		self.assertIn("Output - A Standard rate (excl capital goods)", CLASSIFICATION_OPTIONS.split("\n"))
		self.assertIn("Export Zero Rated", ITEM_VAT_CATEGORY_OPTIONS.split("\n"))

	def test_seed_vat_vendor_types_returns_expected_defaults(self):
		with (
			patch("frappe.db.get_value", side_effect=[None, None, None, None, None]),
			patch("frappe.get_doc") as get_doc,
		):
			inserted = []
			for spec in DEFAULT_VAT_VENDOR_TYPES:
				doc = frappe._dict(spec)
				doc.flags = frappe._dict()
				doc.insert = lambda spec=spec: inserted.append(spec["vendor_type"])
				get_doc.side_effect = lambda payload, _doc=doc: _doc
			result = seed_vat_vendor_types()
		self.assertEqual(len(DEFAULT_VAT_VENDOR_TYPES), result["created"])

	def test_default_vat_vendor_type_prefers_standard(self):
		with patch("frappe.db.get_value", side_effect=["Standard"]):
			self.assertEqual("Standard", get_default_vat_vendor_type())

	def test_tax_invoice_threshold_profiles(self):
		self.assertEqual("no_tax_invoice_required", get_invoice_type(NO_TAX_INVOICE_THRESHOLD))
		self.assertEqual("abridged_tax_invoice", get_invoice_type(NO_TAX_INVOICE_THRESHOLD + 1))
		self.assertEqual("full_tax_invoice", get_invoice_type(FULL_TAX_INVOICE_THRESHOLD + 1))

	def test_sales_invoice_profile_only_overrides_for_sa_company(self):
		with patch("za_local.sa_vat.tax_invoice.is_company_in_south_africa", return_value=True):
			profile = build_sales_invoice_print_profile(company="Test Company", grand_total=6000)
		self.assertTrue(profile["override_default"])
		self.assertEqual("SA Full Tax Invoice", profile["print_format"])

		with patch("za_local.sa_vat.tax_invoice.is_company_in_south_africa", return_value=True):
			profile = build_sales_invoice_print_profile(company="Test Company", grand_total=500)
		self.assertEqual("SA Abridged Tax Invoice", profile["print_format"])

		with patch("za_local.sa_vat.tax_invoice.is_company_in_south_africa", return_value=False):
			profile = build_sales_invoice_print_profile(company="Test Company", grand_total=6000)
		self.assertFalse(profile["override_default"])
		self.assertIsNone(profile["print_format"])

	def test_sync_vat_accounts_only_tracks_vat_tax_accounts(self):
		settings = frappe._dict(
			{
				"company": "Test Company",
				"output_vat_account": "VAT Output - TC",
				"input_vat_account": "VAT Input - TC",
				"tax_accounts": [],
				"append": lambda fieldname, value: settings.tax_accounts.append(frappe._dict(value)),
			}
		)
		tracked = sync_vat_accounts(settings)
		self.assertEqual(
			["VAT Output - TC", "VAT Input - TC"],
			tracked,
		)

	def test_vat201_return_aggregates_from_transaction_rows(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.transactions = [
			frappe._dict(
				{
					"classification": "Output - A Standard rate (excl capital goods)",
					"incl_tax_amount": 100,
					"tax_amount": 15,
					"is_cancelled": 0,
				}
			),
			frappe._dict(
				{
					"classification": "Output - C Zero Rated (excl goods exported)",
					"incl_tax_amount": 40,
					"tax_amount": 0,
					"is_cancelled": 0,
				}
			),
			frappe._dict(
				{
					"classification": "Input - C Other goods supplied to you (excl capital goods)",
					"incl_tax_amount": 60,
					"tax_amount": 9,
					"is_cancelled": 0,
				}
			),
		]
		doc.change_in_use_output = 0
		doc.bad_debts_output = 0
		doc.other_output = 0
		doc.change_in_use_input = 0
		doc.bad_debts_input = 0
		doc.diesel_refund = 0

		VAT201Return.calculate_totals(doc)

		self.assertEqual(100, doc.standard_rated_supplies)
		self.assertEqual(40, doc.zero_rated_supplies)
		self.assertEqual(15, doc.standard_rated_output)
		self.assertEqual(9, doc.other_goods_services_input)
		self.assertEqual(6, doc.vat_payable)

	def test_blank_vat_rate_rows_are_replaced_with_defaults(self):
		doc = frappe.new_doc("South Africa VAT Settings")
		doc.standard_vat_rate = 15
		doc.enable_zero_rated_items = 1
		doc.enable_exempt_items = 1
		doc.append("vat_rates", {"rate_name": "", "rate": 0})

		doc.validate_vat_rates()

		rate_names = [row.rate_name for row in doc.vat_rates]
		self.assertIn("Standard Rate", rate_names)
		self.assertIn("Zero Rate", rate_names)
		self.assertIn("Exempt", rate_names)
