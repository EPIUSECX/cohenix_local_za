import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, today

from za_local.sa_coida.doctype.coida_annual_return.coida_annual_return import COIDAAnnualReturn
from za_local.sa_coida.doctype.oid_claim.oid_claim import OIDClaim
from za_local.sa_coida.doctype.workplace_injury.workplace_injury import WorkplaceInjury
from za_local.sa_labour.doctype.business_trip.business_trip import BusinessTrip
from za_local.sa_payroll.doctype.emp201_submission.emp201_submission import EMP201Submission
from za_local.sa_payroll.doctype.emp501_reconciliation.emp501_reconciliation import EMP501Reconciliation
from za_local.sa_payroll.report.retirement_fund_deductions.retirement_fund_deductions import (
	get_data as get_retirement_fund_deductions,
)
from za_local.sa_setup.install import (
	_desktop_icon_supports_app_tiles,
	ensure_sa_vat_print_format_field_templates,
	sync_za_local_desktop_icons,
)
from za_local.tests.compat import UnitTestCase

EXPECTED_SA_PRINT_FORMATS = {
	"SA Sales Invoice": "Sales Invoice",
	"SA Full Tax Invoice": "Sales Invoice",
	"SA Abridged Tax Invoice": "Sales Invoice",
	"SA Credit Note": "Sales Invoice",
	"SA Purchase Invoice": "Purchase Invoice",
	"SA Debit Note": "Purchase Invoice",
	"SA Quotation": "Quotation",
	"SA Sales Order": "Sales Order",
	"SA Delivery Note": "Delivery Note",
	"SA Purchase Order": "Purchase Order",
	"SA Payment Entry": "Payment Entry",
	"SA Salary Slip": "Salary Slip",
	"IRP5 Employee Certificate": "IRP5 Certificate",
	"IRP5-it3 Certificate": "IRP5 Certificate",
}


class TestStatutoryWorkflowRegressions(UnitTestCase):
	def test_sa_print_formats_are_registered_for_expected_doctypes(self):
		for print_format, doc_type in EXPECTED_SA_PRINT_FORMATS.items():
			record = frappe.db.get_value(
				"Print Format",
				print_format,
				["doc_type", "standard", "disabled"],
				as_dict=True,
			)
			self.assertIsNotNone(record, msg=f"Missing Print Format: {print_format}")
			self.assertEqual(doc_type, record.doc_type)
			self.assertEqual("Yes", record.standard)
			self.assertEqual(0, record.disabled)

	def test_sa_print_format_json_has_inline_html_and_no_legacy_app_references(self):
		app_root = Path(frappe.get_app_path("za_local"))
		json_files = list(app_root.glob("sa_vat/print_format/*/*.json")) + list(
			app_root.glob("sa_payroll/print_format/*/*.json")
		)
		self.assertTrue(json_files, msg="No standard print format JSON files found")

		for path in json_files:
			payload = json.loads(path.read_text())
			html = payload.get("html") or ""
			self.assertTrue(html.strip(), msg=f"{path} must store inline Jinja HTML")
			self.assertNotIn("erpnext_south_africa", html)
			self.assertNotIn("kartoza", html.lower())

	def test_sa_vat_field_template_sync_does_not_require_document_insert(self):
		columns = [
			"name",
			"creation",
			"modified",
			"modified_by",
			"owner",
			"docstatus",
			"idx",
			"module",
			"document_type",
			"field",
			"standard",
			"template",
			"template_file",
		]

		with (
			patch("frappe.db.table_exists", return_value=True),
			patch("frappe.db.exists", return_value=False),
			patch("frappe.db.get_table_columns", return_value=columns),
			patch("frappe.db.sql") as sql,
			patch("frappe.get_doc") as get_doc,
		):
			ensure_sa_vat_print_format_field_templates()

		self.assertEqual(5, sql.call_count)
		get_doc.assert_not_called()

	def test_desktop_icon_sync_skips_legacy_schema_without_icon_type(self):
		with (
			patch("frappe.db.table_exists", return_value=True),
			patch(
				"frappe.db.get_table_columns",
				return_value=["name", "label", "link", "link_to", "hidden", "standard"],
			),
			patch("frappe.get_meta", side_effect=Exception("legacy metadata")),
			patch("frappe.get_all") as get_all,
		):
			self.assertFalse(_desktop_icon_supports_app_tiles())
			sync_za_local_desktop_icons()

		get_all.assert_not_called()

	def test_emp201_fetch_data_aggregates_sars_mapped_components(self):
		doc = frappe.new_doc("EMP201 Submission")
		doc.company = "Test Company"
		doc.submission_period_start_date = "2026-04-01"
		doc.submission_period_end_date = "2026-04-30"

		salary_slip = frappe._dict(
			{
				"za_monthly_eti": 200,
				"deductions": [
					frappe._dict(salary_component="PAYE", amount=1_500),
					frappe._dict(salary_component="UIF Employee", amount=177.12),
				],
				"company_contribution": [
					frappe._dict(salary_component="SDL Contribution", amount=250),
				],
				"earnings": [],
			}
		)

		def bucket(component_name):
			return {
				"PAYE": ("paye", frappe._dict()),
				"UIF Employee": ("uif", frappe._dict()),
				"SDL Contribution": ("sdl", frappe._dict()),
			}.get(component_name, (None, frappe._dict()))

		with (
			patch("frappe.get_all", return_value=[frappe._dict(name="SAL-SLIP-0001")]),
			patch("frappe.get_doc", return_value=salary_slip),
			patch("frappe.db.get_value", return_value=0),
			patch("za_local.sa_payroll.doctype.emp201_submission.emp201_submission._get_emp201_bucket", side_effect=bucket),
		):
			result = EMP201Submission.fetch_emp201_data(doc)

		self.assertEqual(1_500, result["gross_paye_before_eti"])
		self.assertEqual(200, result["eti_generated_current_month"])
		self.assertEqual(200, result["eti_utilized_current_month"])
		self.assertEqual(1_300, result["net_paye_payable"])
		self.assertEqual(177.12, result["uif_payable"])
		self.assertEqual(250, result["sdl_payable"])

	def test_emp501_submission_readiness_requires_sars_references(self):
		doc = frappe.new_doc("EMP501 Reconciliation")
		doc.paye_reference_number = ""
		doc.sdl_reference_number = "L123456789"
		doc.uif_reference_number = ""

		with self.assertRaises(frappe.ValidationError):
			EMP501Reconciliation.validate_submission_readiness(doc)

	def test_business_trip_totals_use_settings_mileage_rate(self):
		doc = frappe.new_doc("Business Trip")
		doc.from_date = "2026-04-10"
		doc.to_date = "2026-04-11"
		doc.allowances = [
			frappe._dict(daily_rate=522, incidental_rate=169),
			frappe._dict(daily_rate=522, incidental_rate=169),
		]
		doc.journeys = [
			frappe._dict(transport_mode="Car (Private)", distance_km=120, mileage_claim=0),
			frappe._dict(transport_mode="Flight", receipt_amount=1_800),
		]
		doc.accommodations = [frappe._dict(amount=1_250)]
		doc.other_expenses = [frappe._dict(amount=300)]

		with patch("frappe.get_cached_doc", return_value=frappe._dict(mileage_allowance_rate=4.84)):
			BusinessTrip.validate(doc)

		self.assertEqual(1_044, doc.total_allowance)
		self.assertEqual(338, doc.total_incidental)
		self.assertEqual(580.8, flt(doc.total_mileage_claim, 2))
		self.assertEqual(1_800, doc.total_receipt_claims)
		self.assertEqual(1_250, doc.total_accommodation)
		self.assertEqual(300, doc.total_other_expenses)
		self.assertEqual(5_312.8, flt(doc.grand_total, 2))

	def test_coida_annual_return_calculates_assessment_fee_and_aligns_fiscal_dates(self):
		doc = frappe.new_doc("COIDA Annual Return")
		doc.fiscal_year = "2026-2027"
		doc.from_date = "2026-01-01"
		doc.to_date = "2026-12-31"
		doc.total_annual_earnings = 1_250_000
		doc.assessment_rate = 1.35

		fiscal_year = frappe._dict(year_start_date="2026-03-01", year_end_date="2027-02-28")
		with patch("frappe.get_doc", return_value=fiscal_year):
			COIDAAnnualReturn.validate(doc)

		self.assertEqual(fiscal_year.year_start_date, doc.from_date)
		self.assertEqual(fiscal_year.year_end_date, doc.to_date)
		self.assertEqual(16_875, doc.assessment_fee)

	def test_workplace_injury_rejects_future_dates_and_calculates_leave_days(self):
		doc = frappe.new_doc("Workplace Injury")
		doc.injury_date = add_days(today(), 1)

		with self.assertRaises(frappe.ValidationError):
			WorkplaceInjury.validate_dates(doc)

		doc.injury_date = "2026-04-01"
		doc.expected_recovery_date = "2026-04-05"
		WorkplaceInjury.calculate_leave_days(doc)
		self.assertEqual(5, doc.leave_days)

	def test_oid_claim_rejects_dates_before_injury(self):
		doc = frappe.new_doc("OID Claim")
		doc.injury_date = "2026-04-10"
		doc.claim_date = "2026-04-09"

		with self.assertRaises(frappe.ValidationError):
			OIDClaim.validate_dates(doc)

	def test_retirement_fund_report_returns_empty_without_company_filter(self):
		self.assertEqual([], get_retirement_fund_deductions(frappe._dict()))
