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

		self.assertEqual(get_sa_localization_stages(frappe._dict(country="United States")), [])
		self.assertEqual(len(get_sa_localization_stages(frappe._dict(country="South Africa"))), 1)

	def test_first_run_setup_skips_hrms_master_loaders(self):
		from za_local.sa_setup.setup_wizard import setup_za_localization

		with (
			patch("frappe.defaults.get_user_default", return_value=None),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", return_value=1),
			patch("za_local.accounts.setup_chart.load_sa_chart_of_accounts", return_value=True) as chart,
			patch("za_local.sa_setup.install.ensure_sa_print_formats") as ensure_print_formats,
			patch("za_local.sa_setup.setup_wizard.setup_sa_print_formats") as setup_print_formats,
			patch("za_local.sa_setup.install.sync_sa_navigation") as sync_navigation,
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
		ensure_print_formats.assert_called_once()
		setup_print_formats.assert_called_once_with(include_hrms=False)
		sync_navigation.assert_called_once()
		load_json.assert_not_called()

	def test_first_run_setup_does_not_augment_chart_before_accounts_exist(self):
		from za_local.sa_setup.setup_wizard import setup_za_localization

		with (
			patch("frappe.defaults.get_user_default", return_value=None),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", return_value=0),
			patch("za_local.accounts.setup_chart.load_sa_chart_of_accounts") as chart,
			patch("za_local.sa_setup.install.ensure_sa_print_formats") as ensure_print_formats,
			patch("za_local.sa_setup.setup_wizard.setup_sa_print_formats") as setup_print_formats,
			patch("za_local.sa_setup.install.sync_sa_navigation") as sync_navigation,
		):
			setup_za_localization(frappe._dict(country="South Africa", company_name="Test ZA Company"))

		chart.assert_not_called()
		ensure_print_formats.assert_not_called()
		setup_print_formats.assert_not_called()
		sync_navigation.assert_not_called()


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
