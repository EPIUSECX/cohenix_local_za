import json
from pathlib import Path
from unittest.mock import patch

import frappe

from za_local.sa_payroll.doctype.emp201_submission.emp201_submission import (
	EMP201Submission,
	calculate_eti_utilisation,
)
from za_local.sa_payroll.doctype.emp501_reconciliation.emp501_reconciliation import (
	EMP501Reconciliation,
)
from za_local.sa_payroll.doctype.irp5_certificate.irp5_certificate import (
	IRP5Certificate,
	build_certificate_key,
	require_certificate_generation_permissions,
)
from za_local.sa_payroll.report.emp201_report.emp201_report import get_data as get_emp201_report
from za_local.sa_payroll.report.retirement_fund_deductions.retirement_fund_deductions import (
	RETIREMENT_FUND_CODES,
)
from za_local.sa_payroll.report.retirement_fund_deductions.retirement_fund_deductions import (
	get_data as get_retirement_report,
)
from za_local.sa_payroll.report.statutory_submissions_summary.statutory_submissions_summary import (
	get_data as get_statutory_summary,
)
from za_local.tests.compat import UnitTestCase
from za_local.utils.emp501_utils import generate_emp501_csv


class TestSARSReportingRegressions(UnitTestCase):
	def test_emp201_submission_key_is_deterministic_for_company_period(self):
		first = frappe.new_doc("EMP201 Submission")
		first.update({"company": "Test Company", "fiscal_year": "2026-2027", "month": "March"})
		second = frappe.new_doc("EMP201 Submission")
		second.update({"company": "Test Company", "fiscal_year": "2026-2027", "month": "March"})

		EMP201Submission.set_submission_key(first)
		EMP201Submission.set_submission_key(second)

		self.assertEqual(first.submission_key, second.submission_key)
		self.assertEqual(64, len(first.submission_key))

	def test_irp5_totals_follow_sars_4141_4149_and_4497_rules(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.gross_taxable_income = 500_000
		doc.eti = 5_000
		for code, amount in (
			("4001", 60_000),
			("4102", 120_000),
			("4115", 1_000),
			("4116", 4_368),
			("4120", 500),
			("4141", 2_125),
		):
			doc.append("deduction_details", {"deduction_code": code, "amount": amount})
		for code, amount in (("4141", 2_125), ("4142", 6_000), ("4472", 10_000)):
			doc.append(
				"company_contribution_details",
				{"contribution_code": code, "amount": amount},
			)

		IRP5Certificate.calculate_totals(doc)

		self.assertEqual(121_000, doc.paye)
		self.assertEqual(4_250, doc.uif)
		self.assertEqual(6_000, doc.sdl)
		self.assertEqual(131_250, doc.total_tax_payable)
		self.assertEqual(70_000, doc.total_deductions_contributions)
		self.assertEqual(4_368, doc.medical_scheme_fees_tax_credit)
		self.assertEqual(500, doc.additional_medical_expenses_tax_credit)
		self.assertEqual("IRP5", doc.certificate_type)

	def test_zero_taxable_income_is_not_replaced_with_all_income(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.gross_taxable_income = 0
		doc.non_taxable_income = 5_000
		doc.append("income_details", {"income_code": "3704", "amount": 5_000})

		IRP5Certificate.calculate_totals(doc)

		self.assertEqual(0, doc.gross_taxable_income)
		self.assertEqual("IT3(a)", doc.certificate_type)
		self.assertEqual("04", doc.reason_for_non_deduction)

	def test_reference_income_does_not_inflate_gross_taxable_income(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.employee = "_Test Employee"
		doc.tax_year = "2026-2027"
		doc.reconciliation_period = "Final"
		doc.from_date = "2026-03-01"
		doc.to_date = "2027-02-28"
		salary_slip = frappe._dict(
			earnings=[
				frappe._dict(salary_component="Severance", amount=500_000),
				frappe._dict(salary_component="Basic", amount=300_000),
				frappe._dict(salary_component="Subsistence", amount=5_000),
			],
			deductions=[],
			company_contribution=[],
		)
		codes = {
			"Severance": frappe._dict(
				code="3901", description="Severance", category="Income", tax_treatment="Reference"
			),
			"Basic": frappe._dict(
				code="3601", description="Basic", category="Income", tax_treatment="Taxable"
			),
			"Subsistence": frappe._dict(
				code="3704", description="Subsistence", category="Income", tax_treatment="Non-Taxable"
			),
		}

		with (
			patch.object(IRP5Certificate, "_get_salary_slips", return_value=[frappe._dict(name="SS-1")]),
			patch("frappe.get_doc", return_value=salary_slip),
			patch.object(
				IRP5Certificate,
				"_get_sars_payroll_code",
				side_effect=lambda component: codes[component],
			),
		):
			IRP5Certificate._generate_certificate_lines(doc)

		self.assertEqual(300_000, doc.gross_taxable_income)
		self.assertEqual(5_000, doc.non_taxable_income)
		self.assertEqual({"3601", "3704", "3901"}, {row.income_code for row in doc.income_details})

	def test_taxable_it3a_requires_explicit_valid_reason_code(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.gross_taxable_income = 50_000
		doc.certificate_type = "IRP5"
		IRP5Certificate.calculate_totals(doc)

		self.assertEqual("IT3(a)", doc.certificate_type)
		self.assertFalse(doc.reason_for_non_deduction)
		missing = IRP5Certificate.validate_statutory_readiness(doc, throw=False)
		self.assertIn("Valid SARS reason code 4150 (02-10)", missing)

		doc.reason_for_non_deduction = "02"
		missing = IRP5Certificate.validate_statutory_readiness(doc, throw=False)
		self.assertNotIn("Valid SARS reason code 4150 (02-10)", missing)

		doc.reason_for_non_deduction = "08"
		missing = IRP5Certificate.validate_statutory_readiness(doc, throw=False)
		self.assertIn("Reason code 08 requires medical tax credit code 4116 or 4120", missing)

	def test_taxable_it3a_below_threshold_gets_reason_code_02(self):
		doc = frappe.new_doc("IRP5 Certificate")
		doc.tax_year = "2026-2027"
		doc.date_of_birth = "1990-01-01"
		doc.gross_taxable_income = 36_000
		doc.periods_worked = 6
		doc.periods_in_year = 12

		IRP5Certificate.calculate_totals(doc)

		self.assertEqual("IT3(a)", doc.certificate_type)
		self.assertEqual("02", doc.reason_for_non_deduction)

	def test_certificate_key_is_canonical_across_certificate_type(self):
		irp5_key = build_certificate_key("_Test Company", "_Test Employee", "2026-2027", "Final")
		it3a_key = build_certificate_key("_Test Company", "_Test Employee", "2026-2027", "Final")
		self.assertEqual(irp5_key, it3a_key)

	def test_certificate_generation_requires_create_and_write_permissions(self):
		with (
			patch("frappe.has_permission", side_effect=[True, False]),
			self.assertRaises(frappe.PermissionError),
		):
			require_certificate_generation_permissions()

	def test_pay_period_snapshot_uses_frequency_and_deduplicates_off_cycle_slips(self):
		doc = frappe.new_doc("IRP5 Certificate")
		slips = [
			frappe._dict(
				name="SS-MAIN",
				end_date="2026-03-31",
				payroll_frequency="Monthly",
				total_working_days=22,
				payment_days=22,
			),
			frappe._dict(
				name="SS-OFFCYCLE",
				end_date="2026-03-20",
				payroll_frequency="Monthly",
				total_working_days=22,
				payment_days=5,
			),
		]

		IRP5Certificate._set_pay_period_snapshot(doc, slips)

		self.assertEqual(12, doc.periods_in_year)
		self.assertEqual(1, doc.periods_worked)

	def test_emp201_month_is_resolved_from_fiscal_year_dates_not_name(self):
		doc = frappe.new_doc("EMP201 Submission")
		doc.month = "January"
		doc.fiscal_year = "SA Tax Year FY26"
		fiscal_year = frappe._dict(year_start_date="2025-03-01", year_end_date="2026-02-28")

		with patch("frappe.get_doc", return_value=fiscal_year):
			result = EMP201Submission.set_submission_period_dates(doc)

		self.assertEqual("2026-01-01", str(result["submission_period_start_date"]))
		self.assertEqual("2026-01-31", str(result["submission_period_end_date"]))

	def test_emp201_eti_refund_closes_each_six_month_reconciliation_cycle(self):
		august = calculate_eti_utilisation(1_000, 300, 900, "2026-08-01")
		self.assertEqual(1_000, august.eti_utilized_current_month)
		self.assertEqual(200, august.eti_reconciliation_refund)
		self.assertEqual(0, august.eti_to_be_carried_forward)

		september = calculate_eti_utilisation(1_000, 300, 900, "2026-09-01")
		self.assertEqual(0, september.eti_carried_forward_from_previous)
		self.assertEqual(300, september.eti_utilized_current_month)

	def test_emp501_reconciles_certificates_to_generated_not_utilized_eti(self):
		doc = frappe.new_doc("EMP501 Reconciliation")
		rows = [
			frappe._dict(
				name="EMP201-MAR",
				submission_period_start_date="2026-03-01",
				gross_paye_before_eti=1_000,
				uif_payable=100,
				sdl_payable=50,
				eti_carried_forward_from_previous=100,
				eti_generated_current_month=300,
				eti_utilized_current_month=250,
				eti_to_be_carried_forward=150,
			),
			frappe._dict(
				name="EMP201-APR",
				submission_period_start_date="2026-04-01",
				gross_paye_before_eti=1_200,
				uif_payable=120,
				sdl_payable=60,
				eti_carried_forward_from_previous=150,
				eti_generated_current_month=200,
				eti_utilized_current_month=250,
				eti_to_be_carried_forward=100,
			),
		]
		certificate_totals = frappe._dict(paye=2_200, uif=220, sdl=110, eti=500)

		with patch.object(EMP501Reconciliation, "_get_linked_emp201_rows", return_value=rows):
			result = EMP501Reconciliation.validate_certificate_reconciliation(
				doc,
				certificate_totals,
			)

		self.assertEqual(500, result.eti_generated)
		self.assertEqual(500, result.eti_utilized)

		certificate_totals.eti = 400
		with (
			patch.object(EMP501Reconciliation, "_get_linked_emp201_rows", return_value=rows),
			self.assertRaises(frappe.ValidationError),
		):
			EMP501Reconciliation.validate_certificate_reconciliation(doc, certificate_totals)

	def test_emp501_coverage_rejects_draft_certificate(self):
		doc = frappe.new_doc("EMP501 Reconciliation")
		doc.append(
			"irp5_certificates",
			{
				"employee": "_Test Employee",
				"employee_name": "_Test Employee",
				"irp5_certificate": "IRP5-DRAFT",
			},
		)
		with (
			patch.object(
				EMP501Reconciliation,
				"_get_salary_slip_employees",
				return_value={"_Test Employee": "_Test Employee"},
			),
			patch(
				"frappe.get_all",
				return_value=[
					frappe._dict(
						name="IRP5-DRAFT",
						employee="_Test Employee",
						company=None,
						tax_year=None,
						reconciliation_period=None,
						from_date=None,
						to_date=None,
						docstatus=0,
						status="Prepared",
					)
				],
			),
			self.assertRaises(frappe.ValidationError),
		):
			EMP501Reconciliation.validate_irp5_coverage(doc)

	def test_emp501_linked_emp201_rows_must_match_period_coverage(self):
		doc = frappe.new_doc("EMP501 Reconciliation")
		doc.append("emp201_submissions", {"emp201_submission": "EMP201-MAR"})
		coverage = {
			"missing_periods": [],
			"duplicate_periods": [],
			"linked_submissions": [frappe._dict(name="EMP201-MAR"), frappe._dict(name="EMP201-APR")],
		}
		with (
			patch.object(EMP501Reconciliation, "validate_emp201_period_coverage", return_value=coverage),
			patch.object(
				EMP501Reconciliation,
				"_get_linked_emp201_rows",
				return_value=[frappe._dict(name="EMP201-MAR")],
			),
			self.assertRaises(frappe.ValidationError),
		):
			EMP501Reconciliation.validate_linked_emp201_references(doc)

	def test_reports_filter_submitted_rows_and_deduplicate_eti(self):
		filters = {"company": "_Test Company", "from_date": "2026-03-01", "to_date": "2026-03-31"}
		with patch("frappe.db.sql", return_value=[]) as sql:
			get_emp201_report(filters)
		self.assertIn("docstatus = 1", sql.call_args.args[0])

		with patch("frappe.db.sql", return_value=[]) as sql:
			get_statutory_summary(filters)
		query = sql.call_args.args[0]
		self.assertIn("IFNULL(ss.za_monthly_eti, 0) = 0", query)
		self.assertIn("cc.parenttype = 'Salary Slip'", query)

	def test_retirement_report_uses_only_retirement_sars_codes(self):
		self.assertEqual({"4001", "4003", "4006"}, RETIREMENT_FUND_CODES)
		rows = [
			frappe._dict(salary_slip="SS-1", retirement_taxable_excess=1_000),
			frappe._dict(salary_slip="SS-1", retirement_taxable_excess=1_000),
		]
		with patch("frappe.db.sql", return_value=rows) as sql:
			result = get_retirement_report(frappe._dict(company="_Test Company"))
		query = sql.call_args.args[0]
		self.assertNotIn("LIKE '%%pension%%'", query)
		self.assertIn("parenttype = 'Salary Slip'", query)
		self.assertEqual([1_000, 0], [row.retirement_taxable_excess for row in result])

	def test_active_print_template_escapes_values_and_renders_required_fields(self):
		template = (
			Path(frappe.get_app_path("za_local"))
			/ "templates"
			/ "print_format"
			/ "irp5_employee_certificate.html"
		).read_text()
		self.assertIn('value if value is not none else "") | e', template)
		self.assertIn("Additional Medical Expenses Tax Credit", template)
		self.assertIn("Directive Number(s)", template)
		self.assertIn("Reason Code for IT3(a) (4150)", template)
		self.assertNotIn('field("ETI", money(doc.eti))', template)

		doc = frappe.new_doc("IRP5 Certificate")
		doc.employee_name = '<img src=x onerror="alert(1)">'
		doc.certificate_type = "IRP5"
		doc.set("income_details", [])
		doc.append(
			"income_details",
			{"income_code": "3601", "description": "<script>alert(1)</script>", "amount": 1},
		)
		rendered = frappe.render_template(template, {"doc": doc})
		self.assertIn("&lt;img", rendered)
		self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)
		self.assertNotIn("<script>alert(1)</script>", rendered)

		app_path = Path(frappe.get_app_path("za_local"))
		for relative_path in (
			"sa_payroll/print_format/irp5_employee_certificate/irp5_employee_certificate.json",
			"sa_payroll/print_format/irp5_it3_certificate/irp5_it3_certificate.json",
		):
			print_format = json.loads((app_path / relative_path).read_text())
			self.assertEqual(template, print_format["html"])

		meta = json.loads(
			(app_path / "sa_payroll" / "doctype" / "irp5_certificate" / "irp5_certificate.json").read_text()
		)
		fields = {field["fieldname"]: field for field in meta["fields"]}
		self.assertEqual(1, fields["certificate_key"]["unique"])
		self.assertEqual("Float", fields["periods_in_year"]["fieldtype"])
		self.assertEqual("Float", fields["periods_worked"]["fieldtype"])
		self.assertEqual("IRP5 Certificate", fields["amended_from"]["options"])

		emp501_meta = json.loads(
			(
				app_path / "sa_payroll" / "doctype" / "emp501_reconciliation" / "emp501_reconciliation.json"
			).read_text()
		)
		emp501_fields = {field["fieldname"]: field for field in emp501_meta["fields"]}
		self.assertEqual("EMP501 Reconciliation", emp501_fields["amended_from"]["options"])
		self.assertNotIn("e_filing_csv", emp501_fields)

	def test_invalid_mixed_record_csv_is_retired(self):
		with (
			patch("frappe.get_doc"),
			patch("frappe.has_permission", return_value=True),
			self.assertRaisesRegex(frappe.ValidationError, "legacy mixed-record CSV was removed"),
		):
			generate_emp501_csv("_Test EMP501")
