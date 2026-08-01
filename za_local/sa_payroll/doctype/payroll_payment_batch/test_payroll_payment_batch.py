import csv
import io
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from za_local.tests.compat import UnitTestCase
from za_local.utils.integrations.eft_file_generator import (
	FNB_COLUMNS,
	FNB_VERSION,
	PaymentBatchSnapshot,
	PaymentRecipient,
	build_payment_batch_snapshot,
	calculate_fnb_hash_total,
	generate_eft_file,
	normalize_bank_format,
	render_fnb_obe_csv,
)


def make_snapshot(source_hash="source-hash"):
	return PaymentBatchSnapshot(
		batch_name="PAY-BATCH-2026-00001",
		payroll_entry="PAY-2026-08",
		company="_Test Company",
		payment_date="2026-08-07",
		company_bank_account="_Test FNB Company",
		own_account_number="62000031451",
		recipients=(
			PaymentRecipient(
				salary_slip="SAL-00001",
				employee="EMP-00001",
				recipient_name="Test Employee",
				bank_account="_Test Employee Bank",
				account_number="12345678901",
				account_type_code="1",
				branch_code="250655",
				amount="12345.67",
				recipient_reference="Salary 202608 EMP-00001",
			),
			PaymentRecipient(
				salary_slip="SAL-00002",
				employee="EMP-00002",
				recipient_name="Second Employee",
				bank_account="_Test Employee Savings",
				account_number="98765432109",
				account_type_code="2",
				branch_code="051001",
				amount="20000.00",
				recipient_reference="Salary 202608 EMP-00002",
			),
		),
		source_hash=source_hash,
	)


class TestFNBPaymentCSV(UnitTestCase):
	def test_matches_official_36_column_control_and_header_rows(self):
		content, hash_total = render_fnb_obe_csv(make_snapshot())
		rows = list(csv.reader(io.StringIO(content)))

		self.assertTrue(content.endswith("\r\n"))
		self.assertTrue(all(len(row) == 36 for row in rows))
		self.assertEqual(rows[0], [FNB_VERSION, *([""] * 35)])
		self.assertEqual(rows[1], ["07-08-2026", *([""] * 35)])
		self.assertEqual(rows[2], ["62000031451", hash_total, *([""] * 34)])
		self.assertEqual(rows[3], list(FNB_COLUMNS))
		self.assertEqual(
			rows[4][:7],
			["Test Employee", "12345678901", "1", "250655", "12345.67", "PAY-BATCH-2026-00001", "Salary 202608 EMP-00"],
		)
		self.assertEqual(rows[4][7:], [""] * 29)

	def test_hash_is_numeric_account_sum_rightmost_12_digits(self):
		self.assertEqual(
			calculate_fnb_hash_total("62000031451", ["12345678901", "98765432109"]),
			"173111142461",
		)
		self.assertEqual(
			calculate_fnb_hash_total("99999999999", ["9999999999999"]),
			"099999999998",
		)

	def test_only_verified_fnb_format_is_enabled(self):
		self.assertEqual(normalize_bank_format("FNB"), "FNB OBE CSV")
		self.assertEqual(normalize_bank_format("FNB OBE CSV"), "FNB OBE CSV")
		for bank_format in ("ABSA", "Nedbank", "Standard Bank"):
			with self.subTest(bank_format=bank_format):
				with self.assertRaises(frappe.ValidationError):
					normalize_bank_format(bank_format)

	def test_total_uses_file_amounts(self):
		self.assertEqual(make_snapshot().total_amount, Decimal("32345.67"))


class TestPaymentBatchSnapshot(UnitTestCase):
	@patch("za_local.utils.integrations.eft_file_generator.validate_payment_batch_header")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.get_all")
	def test_uses_submitted_slips_and_linked_employee_bank_accounts(self, get_all, validate_header):
		company_account = frappe._dict(name="COMPANY-BANK", bank_account_no="62000031451")
		validate_header.return_value = (
			frappe._dict(name="PAY-ENTRY", end_date="2026-08-31"),
			company_account,
		)
		slip = frappe._dict(
			name="SAL-00001", employee="EMP-00001", employee_name="Test Employee",
			net_pay=1000, currency="ZAR", company="_Test Company", docstatus=1,
		)
		employee = frappe._dict(
			name="EMP-00001", employee_name="Test Employee",
			za_payroll_payable_bank_account="EMPLOYEE-BANK",
		)
		company_bank = frappe._dict(
			name="COMPANY-BANK", account_name="Company", bank="FNB", account_type="Current",
			bank_account_no="62000031451", branch_code="250655", disabled=0,
			is_company_account=1, company="_Test Company", party_type=None, party=None,
		)
		employee_bank = frappe._dict(
			name="EMPLOYEE-BANK", account_name="Employee", bank="FNB", account_type="Savings",
			bank_account_no="12345678901", branch_code="250655", disabled=0,
			is_company_account=0, company=None, party_type="Employee", party="EMP-00001",
		)

		def get_rows(doctype, **kwargs):
			return {
				"Salary Slip": [slip],
				"Employee": [employee],
				"Bank Account": [company_bank, employee_bank],
			}[doctype]

		get_all.side_effect = get_rows
		batch = SimpleNamespace(
			name="PAY-BATCH-2026-00001", payroll_entry="PAY-ENTRY", company="_Test Company",
			payment_date="2026-08-07", bank_account="COMPANY-BANK",
		)
		snapshot = build_payment_batch_snapshot(batch)

		self.assertEqual(snapshot.recipients[0].salary_slip, "SAL-00001")
		self.assertEqual(snapshot.recipients[0].bank_account, "EMPLOYEE-BANK")
		self.assertEqual(snapshot.recipients[0].account_number, "12345678901")
		self.assertEqual(snapshot.recipients[0].account_type_code, "2")
		self.assertEqual(len(snapshot.source_hash), 64)


class TestPaymentBatchExportEndpoint(UnitTestCase):
	@patch("za_local.utils.integrations.eft_file_generator.frappe.get_doc")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.has_permission")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.only_for")
	def test_requires_write_permission_before_loading_batch(self, only_for, has_permission, get_doc):
		has_permission.side_effect = frappe.PermissionError("Not permitted")
		with self.assertRaises(frappe.PermissionError):
			generate_eft_file("PAY-BATCH-TEST")

		only_for.assert_called_once()
		has_permission.assert_called_once_with(
			"Payroll Payment Batch", "write", doc="PAY-BATCH-TEST", throw=True
		)
		get_doc.assert_not_called()

	@patch("za_local.utils.integrations.eft_file_generator.now_datetime", return_value="2026-08-01 10:00:00")
	@patch("za_local.utils.integrations.eft_file_generator.save_file")
	@patch("za_local.utils.integrations.eft_file_generator.render_fnb_obe_csv")
	@patch("za_local.utils.integrations.eft_file_generator.build_payment_batch_snapshot")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.get_doc")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.db.get_value")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.has_permission")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.only_for")
	def test_generates_and_attaches_privately_without_returning_content(
		self, only_for, has_permission, get_value, get_doc, build_snapshot,
		render_csv, save_file_mock, now_datetime,
	):
		batch = frappe._dict(
			name="PAY-BATCH-2026-00001", doctype="Payroll Payment Batch", docstatus=1,
			eft_source_hash="", eft_file_generated=0, eft_file_path=None,
		)
		batch.db_set = Mock()
		get_doc.return_value = batch
		build_snapshot.return_value = make_snapshot()
		render_csv.return_value = ("sensitive,csv\r\n", "173111142461")
		file_doc = frappe._dict(
			file_name="FNB_OBE.csv", file_url="/private/files/FNB_OBE.csv", is_private=1,
			attached_to_doctype="Payroll Payment Batch", attached_to_name=batch.name,
		)
		save_file_mock.return_value = file_doc

		result = generate_eft_file(batch.name)

		self.assertNotIn("file_content", result)
		self.assertEqual(result["file_url"], "/private/files/FNB_OBE.csv")
		self.assertFalse(result["reused"])
		save_file_mock.assert_called_once()
		self.assertEqual(save_file_mock.call_args.kwargs["is_private"], 1)
		self.assertEqual(save_file_mock.call_args.kwargs["df"], "eft_file_path")
		batch.db_set.assert_called_once()

	@patch("za_local.utils.integrations.eft_file_generator._get_existing_private_file")
	@patch("za_local.utils.integrations.eft_file_generator.build_payment_batch_snapshot")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.get_doc")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.db.get_value")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.has_permission")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.only_for")
	def test_reuses_existing_private_attachment_idempotently(
		self, only_for, has_permission, get_value, get_doc, build_snapshot, get_existing,
	):
		batch = frappe._dict(
			name="PAY-BATCH-2026-00001", doctype="Payroll Payment Batch", docstatus=1,
			eft_source_hash="source-hash", eft_file_generated=1,
			eft_file_path="/private/files/FNB_OBE.csv",
		)
		get_doc.return_value = batch
		build_snapshot.return_value = make_snapshot()
		get_existing.return_value = frappe._dict(
			file_name="FNB_OBE.csv", file_url="/private/files/FNB_OBE.csv"
		)

		with patch("za_local.utils.integrations.eft_file_generator.save_file") as save_file_mock:
			result = generate_eft_file(batch.name)

		self.assertTrue(result["reused"])
		save_file_mock.assert_not_called()

	@patch("za_local.utils.integrations.eft_file_generator.build_payment_batch_snapshot")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.get_doc")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.db.get_value")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.has_permission")
	@patch("za_local.utils.integrations.eft_file_generator.frappe.only_for")
	def test_rejects_changed_source_after_submission(
		self, only_for, has_permission, get_value, get_doc, build_snapshot,
	):
		get_doc.return_value = frappe._dict(
			name="PAY-BATCH-2026-00001", doctype="Payroll Payment Batch", docstatus=1,
			eft_source_hash="original-hash", eft_file_generated=0, eft_file_path=None,
		)
		build_snapshot.return_value = make_snapshot(source_hash="changed-hash")

		with self.assertRaises(frappe.ValidationError):
			generate_eft_file("PAY-BATCH-2026-00001")
