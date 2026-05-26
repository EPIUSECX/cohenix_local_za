import json
from unittest.mock import patch

import frappe

from za_local.tests.compat import UnitTestCase


class TestHRMSDetection(UnitTestCase):
	def test_hrms_detection_is_site_scoped_when_app_code_exists_elsewhere(self):
		from za_local.utils.hrms_detection import is_hrms_installed

		with (
			patch("za_local.utils.hrms_detection.frappe.get_installed_apps", return_value=["frappe", "erpnext"]),
			patch("za_local.utils.hrms_detection.frappe.db.table_exists", return_value=False),
		):
			self.assertFalse(is_hrms_installed())

	def test_hrms_detection_accepts_only_installed_site_app(self):
		from za_local.utils.hrms_detection import is_hrms_installed

		with patch(
			"za_local.utils.hrms_detection.frappe.get_installed_apps",
			return_value=["frappe", "erpnext", "hrms"],
		):
			self.assertTrue(is_hrms_installed())


class TestSetupWizardStabilisation(UnitTestCase):
	def test_setup_stage_is_only_registered_for_south_africa(self):
		from za_local.sa_setup.setup_wizard import get_sa_localization_stages

		with patch("za_local.sa_setup.install.start_setup_warning_suppression") as suppress:
			self.assertEqual(get_sa_localization_stages(frappe._dict(country="United States")), [])
			suppress.assert_not_called()

		with patch("za_local.sa_setup.install.start_setup_warning_suppression") as suppress:
			self.assertEqual(len(get_sa_localization_stages(frappe._dict(country="South Africa"))), 1)
			suppress.assert_called_once()

	def test_known_setup_warning_filter_is_flag_gated(self):
		from za_local.sa_setup.install import (
			enable_known_setup_warning_filter,
			stop_setup_warning_suppression,
			suppress_known_setup_warnings,
		)

		delivered = []

		def collect_msgprint(msg=None, *args, **kwargs):
			delivered.append(msg)

		stop_setup_warning_suppression()
		with patch.object(frappe, "msgprint", new=collect_msgprint):
			enable_known_setup_warning_filter()

			frappe.msgprint("Accounts not set for Salary Component Basic")
			with suppress_known_setup_warnings():
				frappe.msgprint("Accounts not set for Salary Component Income Tax")
				frappe.msgprint(
					"Rule for this doctype, role, permlevel and if-owner combination already exists."
				)
				frappe.msgprint(
					"User user@example.com: Removed Employee Self Service role as there is no mapped employee."
				)
				frappe.msgprint("Keep this warning")
			frappe.msgprint("Rule for this doctype, role, permlevel and if-owner combination already exists.")

		self.assertEqual(
			delivered,
			[
				"Accounts not set for Salary Component Basic",
				"Keep this warning",
				"Rule for this doctype, role, permlevel and if-owner combination already exists.",
			],
		)

	def test_salary_component_account_defaults_cover_hrms_and_za_components(self):
		from za_local.sa_setup.install import DEFAULT_SALARY_COMPONENT_ACCOUNT_NAMES

		for component in ("Income Tax", "Basic", "Arrear", "Leave Encashment"):
			self.assertIn(component, DEFAULT_SALARY_COMPONENT_ACCOUNT_NAMES)

		for component in ("PAYE", "UIF Employee Contribution", "UIF Employer Contribution", "SDL Contribution"):
			self.assertIn(component, DEFAULT_SALARY_COMPONENT_ACCOUNT_NAMES)

	def test_salary_component_seed_derives_required_component_field_from_name(self):
		from za_local.sa_setup.install import create_salary_component_if_not_exists

		captured = {}

		class FakeSalaryComponent:
			def __init__(self, data):
				self.data = data

			def insert(self, **kwargs):
				captured.update(self.data)

		def exists(doctype, name=None, *args, **kwargs):
			return doctype == "DocType" and name == "Salary Component"

		with (
			patch("za_local.sa_setup.install.is_hrms_installed", return_value=True),
			patch("za_local.sa_setup.install.frappe.db.exists", side_effect=exists),
			patch(
				"za_local.sa_setup.install.frappe.get_doc",
				side_effect=lambda data: FakeSalaryComponent(data),
			),
		):
			create_salary_component_if_not_exists(
				{
					"name": "PAYE",
					"salary_component_abbr": "PAYE",
					"type": "Deduction",
				}
			)

		self.assertEqual(captured["name"], "PAYE")
		self.assertEqual(captured["salary_component"], "PAYE")

	def test_salary_component_setup_skips_without_hrms(self):
		from za_local.sa_setup.install import setup_default_salary_components

		with (
			patch("za_local.sa_setup.install.is_hrms_installed", return_value=False),
			patch("za_local.sa_setup.install.frappe.get_doc") as get_doc,
		):
			setup_default_salary_components()

		get_doc.assert_not_called()

	def test_first_run_setup_skips_hrms_master_loaders(self):
		from za_local.sa_setup.setup_wizard import setup_za_localization

		with (
			patch("frappe.defaults.get_user_default", return_value=None),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", return_value=1),
			patch("za_local.accounts.setup_chart.load_sa_chart_of_accounts", return_value=True) as chart,
			patch("za_local.sa_setup.install.ensure_sa_print_formats") as ensure_print_formats,
			patch("za_local.sa_setup.install.repair_salary_component_accounts") as repair_accounts,
			patch("za_local.sa_setup.setup_wizard.setup_sa_print_formats") as setup_print_formats,
			patch("za_local.sa_setup.install.sync_sa_navigation") as sync_navigation,
			patch("za_local.sa_setup.install.stop_setup_warning_suppression") as stop_suppression,
			patch("za_local.sa_setup.install.load_data_from_json") as load_json,
		):
			setup_za_localization(
				frappe._dict(
					country="South Africa",
					company_name="Test ZA Company",
					za_load_salary_components=1,
					za_load_tax_slabs=1,
				)
			)

		chart.assert_called_once_with("Test ZA Company")
		repair_accounts.assert_called_once_with("Test ZA Company")
		ensure_print_formats.assert_called_once()
		setup_print_formats.assert_called_once_with(include_hrms=False)
		sync_navigation.assert_called_once()
		stop_suppression.assert_called_once()
		load_json.assert_not_called()

	def test_first_run_setup_does_not_augment_chart_before_accounts_exist(self):
		from za_local.sa_setup.setup_wizard import setup_za_localization

		with (
			patch("frappe.defaults.get_user_default", return_value=None),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", return_value=0),
			patch("za_local.accounts.setup_chart.load_sa_chart_of_accounts") as chart,
			patch("za_local.sa_setup.install.ensure_sa_print_formats") as ensure_print_formats,
			patch("za_local.sa_setup.install.repair_salary_component_accounts") as repair_accounts,
			patch("za_local.sa_setup.setup_wizard.setup_sa_print_formats") as setup_print_formats,
			patch("za_local.sa_setup.install.sync_sa_navigation") as sync_navigation,
			patch("za_local.sa_setup.install.stop_setup_warning_suppression") as stop_suppression,
		):
			setup_za_localization(frappe._dict(country="South Africa", company_name="Test ZA Company"))

		chart.assert_not_called()
		repair_accounts.assert_not_called()
		ensure_print_formats.assert_not_called()
		setup_print_formats.assert_not_called()
		sync_navigation.assert_not_called()
		stop_suppression.assert_called_once()

	def test_first_run_setup_logs_errors_without_blocking_erpnext_setup(self):
		from za_local.sa_setup.setup_wizard import setup_za_localization

		with (
			patch("frappe.defaults.get_user_default", return_value=None),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", return_value=1),
			patch(
				"za_local.accounts.setup_chart.load_sa_chart_of_accounts",
				side_effect=RuntimeError("chart augmentation failed"),
			),
			patch("za_local.sa_setup.setup_wizard.frappe.log_error") as log_error,
			patch("za_local.sa_setup.install.stop_setup_warning_suppression") as stop_suppression,
		):
			setup_za_localization(frappe._dict(country="South Africa", company_name="Test ZA Company"))

		log_error.assert_called_once()
		self.assertEqual(log_error.call_args.args[1], "ZA Local Setup")
		stop_suppression.assert_called_once()


class TestNavigationStabilisation(UnitTestCase):
	def test_workspace_paths_exclude_payroll_without_hrms(self):
		from za_local.sa_setup.install import _sa_workspace_definition_paths, _za_sidebar_workspace_names

		no_hrms_paths = [path.as_posix() for path in _sa_workspace_definition_paths(False)]
		hrms_paths = [path.as_posix() for path in _sa_workspace_definition_paths(True)]

		self.assertFalse(any("/sa_payroll/" in path for path in no_hrms_paths))
		self.assertTrue(any("/sa_payroll/" in path for path in hrms_paths))
		self.assertNotIn("SA Payroll", _za_sidebar_workspace_names(False))
		self.assertIn("SA Payroll", _za_sidebar_workspace_names(True))

	def test_sidebar_module_mapping_uses_area_modules_for_boot_permissions(self):
		from za_local.sa_setup.install import _sidebar_module_for_workspace

		self.assertEqual(_sidebar_module_for_workspace("SA Overview"), "SA Setup")
		self.assertEqual(_sidebar_module_for_workspace("SA VAT"), "SA VAT")
		self.assertEqual(_sidebar_module_for_workspace("SA Labour"), "SA Labour")
		self.assertEqual(_sidebar_module_for_workspace("SA COIDA"), "SA COIDA")
		self.assertEqual(_sidebar_module_for_workspace("SA Payroll"), "SA Payroll")

	def test_desktop_layout_repair_merges_missing_child_icons(self):
		from za_local.sa_setup.install import _repair_za_local_desktop_layouts

		layout = [{"label": "SA Localisation", "icon_type": "App", "app": "za_local"}]
		desktop_icons = [
			frappe._dict(
				name="SA Localisation",
				label="SA Localisation",
				icon_type="App",
				app="za_local",
				link_type="External",
				link="/desk/sa-overview",
				parent_icon=None,
				hidden=0,
				idx=0,
			),
			frappe._dict(
				name="SA Overview",
				label="SA Overview",
				icon_type="Link",
				app="za_local",
				link_type="Workspace Sidebar",
				link_to="SA Overview",
				parent_icon="SA Localisation",
				hidden=0,
				idx=0,
			),
			frappe._dict(
				name="SA VAT",
				label="SA VAT",
				icon_type="Link",
				app="za_local",
				link_type="Workspace Sidebar",
				link_to="SA VAT",
				parent_icon="SA Localisation",
				hidden=0,
				idx=1,
			),
			frappe._dict(
				name="SA Labour",
				label="SA Labour",
				icon_type="Link",
				app="za_local",
				link_type="Workspace Sidebar",
				link_to="SA Labour",
				parent_icon="SA Localisation",
				hidden=0,
				idx=2,
			),
			frappe._dict(
				name="SA COIDA",
				label="SA COIDA",
				icon_type="Link",
				app="za_local",
				link_type="Workspace Sidebar",
				link_to="SA COIDA",
				parent_icon="SA Localisation",
				hidden=0,
				idx=3,
			),
		]

		def get_all(doctype, *args, **kwargs):
			if doctype == "Desktop Icon":
				return desktop_icons
			if doctype == "Desktop Layout":
				return [frappe._dict(name="test@example.com", layout=json.dumps(layout))]
			return []

		with (
			patch("za_local.sa_setup.install.frappe.db.table_exists", return_value=True),
			patch("za_local.sa_setup.install.frappe.get_all", side_effect=get_all),
			patch("za_local.sa_setup.install.frappe.db.set_value") as set_value,
		):
			_repair_za_local_desktop_layouts("SA Localisation", hrms_available=False)

		updated_layout = json.loads(set_value.call_args.args[3])
		labels = [icon["label"] for icon in updated_layout]
		self.assertEqual(labels, ["SA Localisation", "SA Overview", "SA VAT", "SA Labour", "SA COIDA"])
		self.assertTrue(
			all(
				icon.get("parent_icon") == "SA Localisation"
				for icon in updated_layout
				if icon.get("label", "").startswith("SA ") and icon.get("label") != "SA Localisation"
			)
		)

	def test_desktop_layout_repair_removes_payroll_without_hrms(self):
		from za_local.sa_setup.install import _repair_za_local_desktop_layouts

		layout = [
			{"label": "SA Localisation", "icon_type": "App", "app": "za_local"},
			{"label": "SA Payroll", "icon_type": "Link", "parent_icon": "SA Localisation"},
		]
		desktop_icons = [
			frappe._dict(
				name="SA Localisation",
				label="SA Localisation",
				icon_type="App",
				app="za_local",
				link_type="External",
				link="/desk/sa-overview",
				parent_icon=None,
				hidden=0,
				idx=0,
			)
		]

		def get_all(doctype, *args, **kwargs):
			if doctype == "Desktop Icon":
				return desktop_icons
			if doctype == "Desktop Layout":
				return [frappe._dict(name="test@example.com", layout=json.dumps(layout))]
			return []

		with (
			patch("za_local.sa_setup.install.frappe.db.table_exists", return_value=True),
			patch("za_local.sa_setup.install.frappe.get_all", side_effect=get_all),
			patch("za_local.sa_setup.install.frappe.db.set_value") as set_value,
		):
			_repair_za_local_desktop_layouts("SA Localisation", hrms_available=False)

		updated_layout = json.loads(set_value.call_args.args[3])
		self.assertEqual([icon["label"] for icon in updated_layout], ["SA Localisation"])

	def test_app_permission_requires_system_manager_system_user(self):
		from za_local.api import check_app_permission

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="manager@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="System User"),
			patch("za_local.api.frappe.get_roles", return_value=["System Manager"]),
		):
			self.assertTrue(check_app_permission())

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="accounts@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="System User"),
			patch("za_local.api.frappe.get_roles", return_value=["Accounts Manager"]),
		):
			self.assertFalse(check_app_permission())

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="portal@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="Website User"),
			patch("za_local.api.frappe.get_roles", return_value=["System Manager"]),
		):
			self.assertFalse(check_app_permission())

	def test_workspace_navigation_removes_hrms_only_and_missing_targets(self):
		from za_local.sa_setup.install import _sanitize_workspace_navigation

		data = {
			"shortcuts": [
				{"label": "SA Payroll", "type": "URL", "url": "/desk/sa-payroll"},
				{"label": "SA VAT", "type": "URL", "url": "/desk/sa-vat"},
			],
			"quick_lists": [
				{"label": "Payroll Correction", "document_type": "Payroll Correction"},
				{"label": "Company", "document_type": "Company"},
			],
			"content": (
				'[{"type":"paragraph","data":{"text":"payroll masters, VAT, payroll runs, and incidents.'
				'<br><br><b>SA Payroll</b> — payroll/accounting reports."}},'
				'{"type":"card","data":{"card_name":"Payroll configuration"}},'
				'{"type":"card","data":{"card_name":"Organisation"}}]'
			),
			"links": [
				{"type": "Card Break", "label": "Payroll configuration", "link_count": 1},
				{
					"type": "Link",
					"label": "Payroll Settings",
					"link_type": "DocType",
					"link_to": "Payroll Settings",
				},
				{"type": "Card Break", "label": "Organisation", "link_count": 2},
				{"type": "Link", "label": "Company", "link_type": "DocType", "link_to": "Company"},
				{"type": "Link", "label": "Missing", "link_type": "DocType", "link_to": "Missing DocType"},
			],
		}

		def exists(doctype, name=None, *args, **kwargs):
			return doctype == "DocType" and name == "Company"

		with patch("za_local.sa_setup.install.frappe.db.exists", side_effect=exists):
			_sanitize_workspace_navigation(data, hrms_available=False)

		self.assertEqual([row["label"] for row in data["shortcuts"]], ["SA VAT"])
		self.assertEqual([row["label"] for row in data["quick_lists"]], ["Company"])
		self.assertEqual([row["label"] for row in data["links"]], ["Organisation", "Company"])
		self.assertIn("Organisation", data["content"])
		self.assertNotIn("SA Payroll", data["content"])
		self.assertNotIn("payroll masters", data["content"])
		self.assertNotIn("Payroll configuration", data["content"])

	def test_manual_setup_rejects_hrms_options_without_hrms(self):
		from za_local.sa_setup.install import validate_za_local_setup_hrms_options

		doc = frappe._dict(load_salary_components=1)

		with patch("za_local.sa_setup.install.is_hrms_installed", return_value=False):
			self.assertRaises(frappe.ValidationError, validate_za_local_setup_hrms_options, doc)

	def test_manual_setup_allows_hrms_options_with_hrms(self):
		from za_local.sa_setup.install import validate_za_local_setup_hrms_options

		doc = frappe._dict(load_salary_components=1, load_tax_slabs=1)

		with patch("za_local.sa_setup.install.is_hrms_installed", return_value=True):
			validate_za_local_setup_hrms_options(doc)


class TestConnectionLinkStabilisation(UnitTestCase):
	def test_doctype_connection_links_hide_hrms_targets_without_hrms(self):
		from za_local.sa_setup.custom_fields import _get_doctype_link_records

		with (
			patch("za_local.sa_setup.custom_fields.is_hrms_installed", return_value=False),
			patch("za_local.sa_setup.custom_fields._doctype_exists_for_link", return_value=True),
		):
			records = _get_doctype_link_records()

		parents = {record["parent"] for record in records}
		targets = {record["link_doctype"] for record in records}
		self.assertNotIn("Employee", parents)
		self.assertNotIn("Payroll Entry", parents)
		self.assertNotIn("Retirement Fund", targets)
		self.assertIn("Workplace Skills Plan", targets)
