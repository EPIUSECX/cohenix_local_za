import frappe
from frappe.tests import UnitTestCase

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
		expected_codes = {"3601", "4102", "4142", "4116"}
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
