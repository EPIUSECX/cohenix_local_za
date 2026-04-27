import json
import subprocess
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = APP_ROOT / "za_local"


class TestRepositoryHygiene(unittest.TestCase):
	def test_no_active_duplicate_print_format_jsons(self):
		seen = {}

		for path in PACKAGE_ROOT.rglob("*.json"):
			path_str = path.as_posix()
			if "/print_format/" not in path_str or "/legacy_standard_docs/" in path_str:
				continue
			seen.setdefault(path.stem, []).append(path_str)

		duplicates = {
			name: paths
			for name, paths in seen.items()
			if len(paths) > 1
		}
		self.assertFalse(duplicates, msg=f"Duplicate active print formats found: {duplicates}")

	def test_no_tracked_cache_or_backup_artifacts(self):
		result = subprocess.run(
			[
				"git",
				"-C",
				str(APP_ROOT),
				"ls-files",
				"*.pyc",
				"*.backup",
			],
			check=True,
			capture_output=True,
			text=True,
		)
		artifacts = sorted(
			line for line in result.stdout.splitlines() if line and (APP_ROOT / line).exists()
		)
		self.assertFalse(artifacts, msg=f"Repository artifacts should not be tracked: {artifacts}")

	def test_standard_json_docs_parse(self):
		json_dirs = (
			PACKAGE_ROOT / "sa_setup" / "workspace",
			PACKAGE_ROOT / "sa_setup" / "onboarding_step",
			PACKAGE_ROOT / "sa_setup" / "module_onboarding",
			PACKAGE_ROOT / "sa_setup" / "form_tour",
			PACKAGE_ROOT / "workspace_sidebar",
			PACKAGE_ROOT / "sa_vat" / "workspace",
			PACKAGE_ROOT / "sa_vat" / "report",
			PACKAGE_ROOT / "sa_vat" / "print_format",
			PACKAGE_ROOT / "sa_vat" / "print_format_field_template",
			PACKAGE_ROOT / "sa_payroll" / "workspace",
			PACKAGE_ROOT / "sa_payroll" / "print_format",
		)

		for json_dir in json_dirs:
			if not json_dir.exists():
				continue

			for path in json_dir.rglob("*.json"):
				with path.open() as handle:
					json.load(handle)

	def test_expected_sa_workspace_sidebars_exist(self):
		expected = {
			"sa_localisation.json",
			"sa_overview.json",
			"sa_vat.json",
			"sa_payroll.json",
			"sa_labour.json",
			"sa_coida.json",
		}
		found = {path.name for path in (PACKAGE_ROOT / "workspace_sidebar").glob("*.json")}
		self.assertTrue(
			expected.issubset(found),
			msg=f"Missing expected workspace sidebar standard docs: {sorted(expected - found)}",
		)

	def test_expected_sa_module_onboarding_exists(self):
		expected = {
			"sa_localisation_onboarding.json",
			"sa_overview_onboarding.json",
			"sa_vat_onboarding.json",
			"sa_payroll_onboarding.json",
			"sa_labour_onboarding.json",
			"sa_coida_onboarding.json",
		}
		found = {
			path.name
			for path in (PACKAGE_ROOT / "sa_setup" / "module_onboarding").rglob("*.json")
		}
		self.assertTrue(
			expected.issubset(found),
			msg=f"Missing expected module onboarding standard docs: {sorted(expected - found)}",
		)

	def test_module_sidebars_reference_module_onboarding(self):
		expected = {
			"sa_overview.json": "SA Overview Onboarding",
			"sa_vat.json": "SA VAT Onboarding",
			"sa_payroll.json": "SA Payroll Onboarding",
			"sa_labour.json": "SA Labour Onboarding",
			"sa_coida.json": "SA COIDA Onboarding",
		}

		for filename, onboarding in expected.items():
			path = PACKAGE_ROOT / "workspace_sidebar" / filename
			with path.open() as handle:
				data = json.load(handle)
			self.assertEqual(
				data.get("module_onboarding"),
				onboarding,
				msg=f"{filename} should attach {onboarding}",
			)

	def test_sa_print_formats_are_module_scoped_and_inline(self):
		expected = {
			"sa_vat/print_format/sa_sales_invoice/sa_sales_invoice.json": "SA Sales Invoice",
			"sa_vat/print_format/sa_full_tax_invoice/sa_full_tax_invoice.json": "SA Full Tax Invoice",
			"sa_vat/print_format/sa_abridged_tax_invoice/sa_abridged_tax_invoice.json": "SA Abridged Tax Invoice",
			"sa_vat/print_format/sa_sales_order/sa_sales_order.json": "SA Sales Order",
			"sa_vat/print_format/sa_quotation/sa_quotation.json": "SA Quotation",
			"sa_vat/print_format/sa_delivery_note/sa_delivery_note.json": "SA Delivery Note",
			"sa_vat/print_format/sa_purchase_invoice/sa_purchase_invoice.json": "SA Purchase Invoice",
			"sa_vat/print_format/sa_purchase_order/sa_purchase_order.json": "SA Purchase Order",
			"sa_vat/print_format/sa_credit_note/sa_credit_note.json": "SA Credit Note",
			"sa_vat/print_format/sa_debit_note/sa_debit_note.json": "SA Debit Note",
			"sa_vat/print_format/sa_payment_entry/sa_payment_entry.json": "SA Payment Entry",
			"sa_payroll/print_format/irp5_employee_certificate/irp5_employee_certificate.json": "IRP5 Employee Certificate",
			"sa_payroll/print_format/irp5_it3_certificate/irp5_it3_certificate.json": "IRP5-it3 Certificate",
			"sa_payroll/print_format/sa_salary_slip/sa_salary_slip.json": "SA Salary Slip",
		}

		for relative_path, name in expected.items():
			path = PACKAGE_ROOT / relative_path
			self.assertTrue(path.exists(), msg=f"Missing print format JSON: {relative_path}")
			with path.open() as handle:
				data = json.load(handle)

			self.assertEqual(data.get("name"), name)
			self.assertEqual(data.get("doctype"), "Print Format")
			self.assertEqual(data.get("print_format_for"), "DocType")
			self.assertEqual(data.get("print_format_type"), "Jinja")
			self.assertEqual(data.get("standard"), "Yes")
			self.assertNotIn(
				"{% include",
				data.get("html") or "",
				msg=f"{name} should keep its HTML inline like ERPNext standard print formats",
			)
