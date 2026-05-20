from unittest.mock import patch

import frappe
from frappe.utils import add_days, today

from za_local.tests.compat import UnitTestCase


class FakeNotification:
	def __init__(self, sink):
		self._sink = sink

	def insert(self, ignore_permissions=False):
		self._sink.append(
			{
				key: value
				for key, value in self.__dict__.items()
				if key != "_sink"
			}
		)


def user_lookup(records):
	def get_value(doctype, name, fieldname=None, as_dict=False):
		if doctype != "User":
			return None
		record = records.get(name)
		if not record:
			return None
		if as_dict:
			return frappe._dict(record)
		if isinstance(fieldname, (list, tuple)):
			return [record.get(field) for field in fieldname]
		return record.get(fieldname)

	return get_value


class TestScheduledTaskNotifications(UnitTestCase):
	def test_hr_admin_users_ignore_non_user_role_parents(self):
		from za_local.tasks import get_hr_admin_users

		role_users = {
			"HR Manager": ["EEA2 Employment Equity Widget", "hr@example.com"],
			"HR User": ["hr@example.com", "portal@example.com"],
			"System Manager": ["disabled@example.com", "sys@example.com"],
		}
		users = {
			"hr@example.com": {"name": "hr@example.com", "enabled": 1, "user_type": "System User"},
			"portal@example.com": {
				"name": "portal@example.com",
				"enabled": 1,
				"user_type": "Website User",
			},
			"disabled@example.com": {
				"name": "disabled@example.com",
				"enabled": 0,
				"user_type": "System User",
			},
			"sys@example.com": {"name": "sys@example.com", "enabled": 1, "user_type": "System User"},
		}

		with (
			patch("za_local.tasks.get_users_with_role", side_effect=lambda role: role_users.get(role, [])),
			patch("za_local.tasks.frappe.db.get_value", side_effect=user_lookup(users)),
		):
			self.assertEqual(get_hr_admin_users(), ["hr@example.com", "sys@example.com"])

	def test_hr_admin_users_fall_back_to_enabled_administrator(self):
		from za_local.tasks import get_hr_admin_users

		users = {
			"Administrator": {"name": "Administrator", "enabled": 1, "user_type": "System User"},
		}

		with (
			patch("za_local.tasks.get_users_with_role", return_value=[]),
			patch("za_local.tasks.frappe.db.get_value", side_effect=user_lookup(users)),
		):
			self.assertEqual(get_hr_admin_users(), ["Administrator"])

	def test_notify_hr_admin_creates_logs_only_for_valid_users(self):
		from za_local.tasks import notify_hr_admin

		inserted = []
		users = {
			"hr@example.com": {"name": "hr@example.com", "enabled": 1, "user_type": "System User"},
			"sys@example.com": {"name": "sys@example.com", "enabled": 1, "user_type": "System User"},
		}

		with (
			patch("za_local.tasks.frappe.db.get_value", side_effect=user_lookup(users)),
			patch("za_local.tasks.frappe.new_doc", side_effect=lambda doctype: FakeNotification(inserted)),
			patch("za_local.tasks.frappe.log_error") as log_error,
		):
			count = notify_hr_admin(
				"Invalid SA ID Numbers Detected",
				"Some IDs are invalid",
				doctype="Employee",
				docname="EMP-0001",
				recipients=["hr@example.com", "EEA2 Employment Equity Widget", "sys@example.com"],
			)

		self.assertEqual(count, 2)
		self.assertEqual([row["for_user"] for row in inserted], ["hr@example.com", "sys@example.com"])
		self.assertTrue(all(row["type"] == "Alert" for row in inserted))
		self.assertTrue(all(row["document_type"] == "Employee" for row in inserted))
		log_error.assert_called_once()

	def test_notify_hr_admin_returns_zero_when_no_valid_user_exists(self):
		from za_local.tasks import notify_hr_admin

		with (
			patch("za_local.tasks.frappe.db.get_value", return_value=None),
			patch("za_local.tasks.frappe.new_doc") as new_doc,
			patch("za_local.tasks.frappe.log_error") as log_error,
		):
			count = notify_hr_admin("Subject", "Message", recipients=["Missing User"])

		self.assertEqual(count, 0)
		new_doc.assert_not_called()
		self.assertTrue(log_error.called)

	def test_tax_directive_expiry_uses_validated_notification_helper(self):
		from za_local.tasks import check_tax_directive_expiry

		directive = frappe._dict(
			name="TD-0001",
			employee="EMP-0001",
			employee_name="Test Employee",
			effective_to=add_days(today(), 5),
		)

		with (
			patch("za_local.tasks._doctype_has_fields", return_value=True),
			patch("za_local.tasks.frappe.get_all", return_value=[directive]),
			patch("za_local.tasks.notify_hr_admin", return_value=1) as notify,
		):
			check_tax_directive_expiry()

		notify.assert_called_once()
		self.assertEqual(notify.call_args.kwargs["doctype"], "Tax Directive")
		self.assertEqual(notify.call_args.kwargs["docname"], "TD-0001")

	def test_weekly_invalid_id_notifications_do_not_fail_scheduler(self):
		from za_local.tasks import weekly

		employee = frappe._dict(
			name="EMP-0001",
			employee_name="Test Employee",
			za_id_number="8505055651089",
		)

		with (
			patch("za_local.tasks._doctype_has_fields", return_value=True),
			patch("za_local.tasks.frappe.get_all", return_value=[employee]),
			patch("za_local.utils.tax_utils.validate_south_african_id", return_value=False),
			patch("za_local.tasks.notify_hr_admin", return_value=1) as notify,
		):
			weekly()

		notify.assert_called_once()
		self.assertEqual(notify.call_args.kwargs["subject"], "Invalid SA ID Numbers Detected")

	def test_daily_skips_missing_optional_doctypes_without_queries(self):
		from za_local.tasks import daily

		with (
			patch("za_local.tasks._doctype_has_fields", return_value=False),
			patch("za_local.tasks.frappe.get_all") as get_all,
		):
			daily()

		get_all.assert_not_called()
