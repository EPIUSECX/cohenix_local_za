from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from za_local.overrides import journal_entry


class TestJournalEntryCleanupGuards(UnitTestCase):
	def set_site(self, site):
		self._old_site = getattr(frappe.local, "site", None)
		frappe.local.site = site

	def restore_site(self):
		frappe.local.site = getattr(self, "_old_site", None)

	def test_allows_cleanup_in_test_context(self):
		with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
			frappe.flags, {"in_test": True}, clear=False
		):
			journal_entry._require_cleanup_access()

		only_for.assert_called_once_with("System Manager")

	def test_blocks_cleanup_on_non_dev_production_context(self):
		self.set_site("erp.example.com")
		try:
			with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
				frappe.flags, {"in_test": False}, clear=False
			), patch.dict(
				journal_entry.frappe.conf, {"developer_mode": 0}, clear=False
			):
				with self.assertRaises(frappe.ValidationError):
					journal_entry._require_cleanup_access()
		finally:
			self.restore_site()

		only_for.assert_called_once_with("System Manager")

	def test_allows_cleanup_on_dev_non_production_site(self):
		self.set_site("payroll-dev.local")
		try:
			with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
				frappe.flags, {"in_test": False}, clear=False
			), patch.dict(
				journal_entry.frappe.conf, {"developer_mode": 1}, clear=False
			):
				journal_entry._require_cleanup_access()
		finally:
			self.restore_site()

		only_for.assert_called_once_with("System Manager")
