from types import SimpleNamespace
from unittest.mock import patch

import frappe

from za_local.tests.compat import UnitTestCase


class TestWhitelistedEndpointPermissions(UnitTestCase):
	def test_state_changing_endpoints_accept_post_only(self):
		from za_local.overrides.journal_entry import (
			force_delete_all_cancelled_payroll_journal_entries,
			force_delete_cancelled_payroll_journal_entry,
		)
		from za_local.overrides.payroll_entry import make_payment_entry_for_payroll
		from za_local.sa_vat.setup import bootstrap_company_vat_setup
		from za_local.utils.integrations.eft_file_generator import generate_eft_file

		for method in (
			bootstrap_company_vat_setup,
			make_payment_entry_for_payroll,
			generate_eft_file,
			force_delete_all_cancelled_payroll_journal_entries,
			force_delete_cancelled_payroll_journal_entry,
		):
			self.assertEqual(
				frappe.allowed_http_methods_for_whitelisted_func[method],
				["POST"],
			)

	def test_tax_invoice_readiness_loads_with_permission_check(self):
		from za_local.sa_vat.tax_invoice import check_tax_invoice_readiness

		invoice = SimpleNamespace(
			name="SINV-TEST",
			company="Test Company",
			base_grand_total=100,
			grand_total=100,
			is_pos=0,
			is_return=0,
			company_address_display="1 Test Street",
			company_tax_id="4123456789",
			customer_name="Test Customer",
			address_display="2 Test Street",
			posting_date="2026-04-10",
			items=[SimpleNamespace(description="Service", qty=1)],
			total_taxes_and_charges=15,
		)
		with (
			patch("za_local.sa_vat.tax_invoice.frappe.get_doc", return_value=invoice) as get_doc,
			patch("za_local.sa_vat.tax_invoice.get_company_vat_registration_number", return_value="4123456789"),
			patch("za_local.sa_vat.tax_invoice.get_company_currency", return_value="ZAR"),
			patch("za_local.sa_vat.tax_invoice.is_company_in_south_africa", return_value=True),
		):
			check_tax_invoice_readiness("SINV-TEST")

		get_doc.assert_called_once_with("Sales Invoice", "SINV-TEST", check_permission=True)

	def test_vat_bootstrap_stops_before_writes_without_system_manager_role(self):
		from za_local.sa_vat.setup import bootstrap_company_vat_setup

		with (
			patch(
				"za_local.sa_vat.setup.frappe.only_for",
				side_effect=frappe.PermissionError("Not permitted"),
			),
			patch("za_local.sa_vat.setup.get_vat_settings") as get_settings,
		):
			with self.assertRaises(frappe.PermissionError):
				bootstrap_company_vat_setup("Test Company")

		get_settings.assert_not_called()

	def test_payroll_payment_wrapper_denies_read_only_user_before_loading_document(self):
		from za_local.overrides.payroll_entry import make_payment_entry_for_payroll

		with (
			patch("za_local.overrides.payroll_entry.frappe.db.exists", return_value=True),
			patch("za_local.overrides.payroll_entry.frappe.has_permission", return_value=False),
			patch("za_local.overrides.payroll_entry.frappe.get_doc") as get_doc,
		):
			with self.assertRaises(frappe.PermissionError):
				make_payment_entry_for_payroll("Payroll Entry", "PAY-TEST")

		get_doc.assert_not_called()

	def test_eft_export_requires_payroll_role_before_reading_banking_data(self):
		from za_local.utils.integrations.eft_file_generator import generate_eft_file

		with (
			patch(
				"za_local.utils.integrations.eft_file_generator.frappe.only_for",
				side_effect=frappe.PermissionError("Not permitted"),
			),
			patch(
				"za_local.utils.integrations.eft_file_generator.frappe.has_permission"
			) as has_permission,
		):
			with self.assertRaises(frappe.PermissionError):
				generate_eft_file("PAY-TEST")

		has_permission.assert_not_called()
