import json
import subprocess
from pathlib import Path

from frappe.tests.utils import FrappeTestCase

APP_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = APP_ROOT / "za_local"


class TestRepositoryHygiene(FrappeTestCase):
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
			PACKAGE_ROOT / "sa_payroll" / "workspace",
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
