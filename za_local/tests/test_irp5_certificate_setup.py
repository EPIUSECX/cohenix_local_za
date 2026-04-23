from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from za_local.sa_payroll.doctype.emp501_reconciliation.emp501_reconciliation import EMP501Reconciliation
from za_local.sa_payroll.doctype.irp5_certificate.irp5_certificate import IRP5Certificate


class TestIRP5CertificateSetup(UnitTestCase):
	def test_irp5_source_custom_fields_exist(self):
		checks = {
			"Employee": {
				"za_income_tax_reference_number",
				"za_residential_address",
				"za_postal_address",
				"za_business_address_override",
				"za_bank_account_type",
			},
			"Company": {
				"za_paye_reference_number",
				"za_trading_name",
				"za_business_address",
			},
			"Address": {
				"za_south_african_address_section",
				"za_unit_no",
				"za_postal_address_type",
				"za_address_line_4",
			},
			"Salary Component": {
				"za_sars_payroll_code",
			},
		}

		for doctype, expected_fields in checks.items():
			meta = frappe.get_meta(doctype)
			fieldnames = {field.fieldname for field in meta.fields if field.fieldname}
			self.assertTrue(
				expected_fields.issubset(fieldnames),
				msg=f"Missing IRP5 source fields on {doctype}: {sorted(expected_fields - fieldnames)}",
			)

	def test_sars_payroll_codes_are_seeded(self):
		expected_codes = {"3601", "4102", "4116", "4118", "4142"}
		found_codes = set(
			frappe.get_all(
				"SARS Payroll Code",
				filters={"name": ["in", list(expected_codes)]},
				pluck="name",
			)
		)
		self.assertEqual(expected_codes, found_codes)

	def test_statutory_readiness_reports_missing_fields(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.certificate_type = "IRP5"
		doc.company = "Test Company"
		doc.employee = "EMP-0001"
		doc.tax_year = "2026-2027"
		doc.from_date = "2026-03-01"
		doc.to_date = "2026-08-31"
		doc.reconciliation_period = "Interim"
		doc.gross_taxable_income = 1000

		missing = IRP5Certificate.validate_statutory_readiness(doc, throw=False)

		self.assertIn("Employer PAYE Reference Number", missing)
		self.assertIn("Employee income tax reference number", missing)
		self.assertIn("Residential address", missing)
		self.assertIn("Income line items", missing)

	def test_tax_certificate_select_fields_have_real_options(self):
		checks = {
			("Employee", "za_identity_type"): ["South African ID", "Passport", "Asylum Seeker"],
			("Employee", "za_nature_of_person"): ["Individual", "Director", "Foreign Employee"],
			("Employee", "za_bank_account_type"): ["Cheque", "Savings", "Other"],
			("Employee", "za_bank_account_holder_relationship"): ["Employee", "Spouse", "Other"],
			("Address", "za_postal_address_type"): ["Street", "PO Box", "Other"],
		}

		for (doctype, fieldname), expected_options in checks.items():
			field = frappe.get_meta(doctype).get_field(fieldname)
			self.assertIsNotNone(field, msg=f"Missing field {doctype}.{fieldname}")
			self.assertFalse(
				"\\n" in (field.options or ""),
				msg=f"{doctype}.{fieldname} still has escaped option separators",
			)
			options = [value for value in (field.options or "").split("\n") if value]
			for expected in expected_options:
				self.assertIn(expected, options, msg=f"{doctype}.{fieldname} missing option {expected}")

	def test_emp501_requires_complete_emp201_coverage(self):
		doc = frappe.new_doc("EMP501 Reconciliation")
		doc.company = "Test Company"
		doc.tax_year = "2026-2027"
		doc.reconciliation_period = "Interim"
		doc.from_date = "2026-03-01"
		doc.to_date = "2026-08-31"

		with patch(
			"frappe.get_all",
			return_value=[
				frappe._dict(name="EMP201-03", submission_period_start_date="2026-03-01"),
				frappe._dict(name="EMP201-04", submission_period_start_date="2026-04-01"),
			],
		):
			result = EMP501Reconciliation.validate_emp201_period_coverage(doc, throw=False)

		self.assertEqual(
			["2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01"],
			[str(value) for value in result["missing_periods"]],
		)
