from unittest.mock import patch

import frappe

from za_local.overrides import journal_entry
from za_local.tests.compat import UnitTestCase


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

	def test_allows_cleanup_with_explicit_developer_opt_in(self):
		self.set_site("payroll.example.com")
		try:
			with patch("za_local.overrides.journal_entry.frappe.only_for") as only_for, patch.dict(
				frappe.flags, {"in_test": False}, clear=False
			), patch.dict(
				journal_entry.frappe.conf,
				{"developer_mode": 1, "allow_za_local_destructive_payroll_cleanup": 1},
				clear=False,
			):
				journal_entry._require_cleanup_access()
		finally:
			self.restore_site()

		only_for.assert_called_once_with("System Manager")

	def test_site_name_alone_never_enables_destructive_cleanup(self):
		self.set_site("payroll-dev.local")
		try:
			with patch("za_local.overrides.journal_entry.frappe.only_for"), patch.dict(
				frappe.flags, {"in_test": False}, clear=False
			), patch.dict(
				journal_entry.frappe.conf,
				{"developer_mode": 1, "allow_za_local_destructive_payroll_cleanup": 0},
				clear=False,
			):
				with self.assertRaises(frappe.ValidationError):
					journal_entry._require_cleanup_access()
		finally:
			self.restore_site()

	def test_bulk_cleanup_rolls_back_failed_entry_to_savepoint(self):
		journal = frappe._dict(name="JV-TEST", docstatus=2, accounts=[])
		with (
			patch("za_local.overrides.journal_entry._require_cleanup_access"),
			patch("za_local.overrides.journal_entry.frappe.db.sql", return_value=[journal]),
			patch("za_local.overrides.journal_entry.frappe.get_doc", return_value=journal),
			patch(
				"za_local.overrides.journal_entry._delete_cancelled_payroll_journal_entry",
				side_effect=RuntimeError("delete failed"),
			),
			patch("za_local.overrides.journal_entry.frappe.db.savepoint") as savepoint,
			patch("za_local.overrides.journal_entry.frappe.db.rollback") as rollback,
			patch("za_local.overrides.journal_entry.frappe.db.release_savepoint") as release,
			patch("za_local.overrides.journal_entry.frappe.log_error") as log_error,
		):
			result = journal_entry.force_delete_all_cancelled_payroll_journal_entries()

		savepoint.assert_called_once_with("za_payroll_je_cleanup_0")
		rollback.assert_called_once_with(save_point="za_payroll_je_cleanup_0")
		release.assert_called_once_with("za_payroll_je_cleanup_0")
		log_error.assert_called_once()
		self.assertEqual(result["failed"][0]["name"], "JV-TEST")
