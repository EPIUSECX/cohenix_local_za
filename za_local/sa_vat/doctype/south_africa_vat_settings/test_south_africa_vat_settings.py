from unittest.mock import patch

import frappe

from za_local.sa_vat.doctype.vat201_return.vat201_return import VAT201Return
from za_local.sa_vat.item_sync import sync_item_zero_rated_flag
from za_local.sa_vat.setup import (
	CLASSIFICATION_OPTIONS,
	DEFAULT_VAT_VENDOR_TYPES,
	ITEM_VAT_CATEGORY_OPTIONS,
	ensure_vat_custom_fields,
	get_default_vat_vendor_type,
	get_vat_settings,
	is_valid_item_tax_account,
	migrate_legacy_vat_account_rows,
	seed_vat_vendor_types,
	sync_vat_accounts,
)
from za_local.sa_vat.tax_invoice import (
	FULL_TAX_INVOICE_THRESHOLD,
	NO_TAX_INVOICE_THRESHOLD,
	build_sales_invoice_print_profile,
	get_invoice_type,
)
from za_local.tests.compat import UnitTestCase


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

	def test_sync_vat_accounts_only_tracks_erpnext_vat_accounts(self):
		settings = frappe._dict(
			{
				"company": "Test Company",
				"output_vat_account": "VAT Output - TC",
				"input_vat_account": "VAT Input - TC",
				"vat_accounts": [],
				"append": lambda fieldname, value: settings.vat_accounts.append(frappe._dict(value)),
			}
		)
		tracked = sync_vat_accounts(settings)
		self.assertEqual(
			["VAT Output - TC", "VAT Input - TC"],
			tracked,
		)
		self.assertEqual("South Africa VAT Account", settings.vat_accounts[0].doctype)

	def test_item_zero_rated_flag_syncs_from_sa_vat_category(self):
		item = frappe._dict(custom_sa_vat_category="Zero Rated", is_zero_rated=0)
		sync_item_zero_rated_flag(item)
		self.assertEqual(1, item.is_zero_rated)

		item.custom_sa_vat_category = "Exempt"
		sync_item_zero_rated_flag(item)
		self.assertEqual(0, item.is_zero_rated)

	def test_ensure_vat_custom_fields_includes_erpnext_zero_rated_fields(self):
		with patch("za_local.sa_vat.setup.create_custom_fields") as create_custom_fields:
			ensure_vat_custom_fields()

		custom_fields = create_custom_fields.call_args.args[0]
		self.assertEqual("is_zero_rated", custom_fields["Item"][0]["fieldname"])
		self.assertEqual("is_zero_rated", custom_fields["Sales Invoice Item"][0]["fieldname"])
		self.assertEqual("is_zero_rated", custom_fields["Purchase Invoice Item"][0]["fieldname"])

	def test_legacy_vat_account_rows_migrate_to_erpnext_child_doctype(self):
		row = frappe._dict(parent="Test VAT Settings", parenttype="South Africa VAT Settings", account="VAT Output - TC", idx=1)
		inserted = []

		with (
			patch("frappe.db.table_exists", return_value=True),
			patch("frappe.get_all", return_value=[row]),
			patch("frappe.db.exists", return_value=False),
			patch("frappe.get_doc") as get_doc,
		):
			doc = frappe._dict(insert=lambda ignore_permissions=False: inserted.append(ignore_permissions))
			get_doc.return_value = doc
			migrated = migrate_legacy_vat_account_rows()

		self.assertEqual(1, migrated)
		self.assertEqual([True], inserted)

	def test_vat201_return_aggregates_from_transaction_rows(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.transactions = [
			frappe._dict(
				{
					"classification": "Output - A Standard rate (excl capital goods)",
					"classification_status": "Classified",
					"incl_tax_amount": 100,
					"tax_amount": 15,
					"is_cancelled": 0,
				}
			),
			frappe._dict(
				{
					"classification": "Output - C Zero Rated (excl goods exported)",
					"classification_status": "Classified",
					"incl_tax_amount": 40,
					"tax_amount": 0,
					"is_cancelled": 0,
				}
			),
			frappe._dict(
				{
					"classification": "Input - C Other goods supplied to you (excl capital goods)",
					"classification_status": "Classified",
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

	def test_company_scope_defaults_follow_company(self):
		doc = frappe.new_doc("South Africa VAT Settings")
		doc.company = "Test Company"
		doc.default_vat_report_company = "Another Company"

		with patch("za_local.sa_vat.doctype.south_africa_vat_settings.south_africa_vat_settings.get_default_vat_vendor_type", return_value="Standard"):
			doc.ensure_company_default()

		self.assertEqual("Test Company", doc.default_vat_report_company)

	def test_vat_filing_day_must_be_between_1_and_31(self):
		doc = frappe.new_doc("South Africa VAT Settings")
		doc.vat_filing_day = 0

		with self.assertRaises(frappe.ValidationError):
			doc.validate_vat_filing_day()

		doc.vat_filing_day = 32
		with self.assertRaises(frappe.ValidationError):
			doc.validate_vat_filing_day()

	def test_item_tax_account_validation_helper_accepts_valid_types(self):
		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", return_value=("Tax", "Test Company")),
		):
			self.assertTrue(is_valid_item_tax_account("VAT Tax - TC", "Test Company"))

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", return_value=("Bank", "Test Company")),
		):
			self.assertFalse(is_valid_item_tax_account("Bank - TC", "Test Company"))

	def test_validate_item_tax_template_account_requires_same_company(self):
		doc = frappe.new_doc("South Africa VAT Settings")
		doc.company = "Test Company"
		doc.item_tax_template_account = "Tax - OTH"

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.get_value", return_value="Other Company"),
		):
			with self.assertRaises(frappe.ValidationError):
				doc.validate_item_tax_template_account()

	def test_get_vat_settings_uses_company_scoped_lookup(self):
		expected = frappe._dict(name="Test Settings")
		with (
			patch("za_local.sa_vat.setup.get_default_company", return_value="Test Company"),
			patch("frappe.db.get_value", return_value="Test Settings"),
			patch("frappe.get_doc", return_value=expected),
		):
			result = get_vat_settings()

		self.assertEqual(expected, result)

	def test_sales_invoice_rows_use_posted_tax_evidence(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.company = "Test Company"
		doc.from_date = "2026-04-01"
		doc.to_date = "2026-04-30"
		settings = frappe._dict(output_vat_account="VAT Output - TC")

		with patch("frappe.get_all") as get_all:
			get_all.side_effect = [
				[
					frappe._dict(
						{
							"name": "SINV-0001",
							"posting_date": "2026-04-10",
							"taxes_and_charges": "SA Standard Rated Sales 15% - Test Company",
							"base_net_total": 100,
							"is_return": 0,
						}
					)
				],
				[
					frappe._dict({"base_net_amount": 100, "custom_sa_vat_category": "Standard Rated"}),
				],
				[
					frappe._dict({"name": "TAX-1", "rate": 15, "tax_amount": 15, "total": 115}),
				],
			]
			rows = VAT201Return.get_sales_invoice_rows(doc, settings)

		self.assertEqual(1, len(rows))
		self.assertEqual(15, rows[0]["tax_amount"])
		self.assertEqual("Classified", rows[0]["classification_status"])

	def test_purchase_zero_rated_rows_do_not_create_input_vat(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.company = "Test Company"
		doc.from_date = "2026-04-01"
		doc.to_date = "2026-04-30"
		settings = frappe._dict(input_vat_account="VAT Input - TC")

		with patch("frappe.get_all") as get_all:
			get_all.side_effect = [
				[
					frappe._dict(
						{
							"name": "PINV-0001",
							"posting_date": "2026-04-10",
							"taxes_and_charges": "",
							"base_net_total": 200,
							"is_return": 0,
						}
					)
				],
				[
					frappe._dict({"base_net_amount": 200, "custom_sa_vat_category": "Zero Rated"}),
				],
				[],
			]
			rows = VAT201Return.get_purchase_invoice_rows(doc, settings)

		self.assertEqual([], rows)

	def test_taxable_template_without_posted_vat_is_reviewed(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.company = "Test Company"
		doc.from_date = "2026-04-01"
		doc.to_date = "2026-04-30"
		settings = frappe._dict(input_vat_account="VAT Input - TC", input_goods_local="SA Standard Rated Purchases 15% - Test Company")

		with patch("frappe.get_all") as get_all:
			get_all.side_effect = [
				[
					frappe._dict(
						{
							"name": "PINV-0002",
							"posting_date": "2026-04-11",
							"taxes_and_charges": "SA Standard Rated Purchases 15% - Test Company",
							"base_net_total": 200,
							"is_return": 0,
						}
					)
				],
				[],
				[],
			]
			rows = VAT201Return.get_purchase_invoice_rows(doc, settings)

		self.assertEqual(1, len(rows))
		self.assertEqual("Needs Review", rows[0]["classification_status"])

	def test_review_rows_do_not_count_in_totals(self):
		doc = frappe.new_doc("VAT201 Return")
		doc.transactions = [
			frappe._dict(
				{
					"classification": "Output - A Standard rate (excl capital goods)",
					"classification_status": "Needs Review",
					"incl_tax_amount": 100,
					"tax_amount": 15,
					"is_cancelled": 0,
				}
			)
		]
		doc.change_in_use_output = 0
		doc.bad_debts_output = 0
		doc.other_output = 0
		doc.change_in_use_input = 0
		doc.bad_debts_input = 0
		doc.diesel_refund = 0

		VAT201Return.calculate_totals(doc)

		self.assertEqual(0, doc.total_output_tax)
		self.assertEqual(0, doc.vat_payable)
