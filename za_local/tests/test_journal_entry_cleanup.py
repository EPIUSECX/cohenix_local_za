from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from za_local.overrides import journal_entry


class TestJournalEntryCleanupGuards(FrappeTestCase):
	def test_allows_cleanup_in_test_context(self):
		with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
			frappe.flags, {"in_test": True}, clear=False
		):
			journal_entry._require_cleanup_access()

		only_for.assert_called_once_with("System Manager")

	def test_blocks_cleanup_on_non_dev_production_context(self):
		with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
			frappe.flags, {"in_test": False}, clear=False
		), patch.dict(
			journal_entry.frappe.conf, {"developer_mode": 0}, clear=False
		), patch(
			"za_local.overrides.journal_entry.frappe.local.site", "erp.example.com", create=True
		):
			with self.assertRaises(frappe.ValidationError):
				journal_entry._require_cleanup_access()

		only_for.assert_called_once_with("System Manager")

	def test_allows_cleanup_on_dev_non_production_site(self):
		with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
			frappe.flags, {"in_test": False}, clear=False
		), patch.dict(
			journal_entry.frappe.conf, {"developer_mode": 1}, clear=False
		), patch(
			"za_local.overrides.journal_entry.frappe.local.site", "payroll-dev.local", create=True
		):
			journal_entry._require_cleanup_access()

		only_for.assert_called_once_with("System Manager")
