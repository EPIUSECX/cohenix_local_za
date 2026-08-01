"""Shared validation for sensitive SA Labour reports."""

from __future__ import annotations

import frappe
from frappe import _


def get_permitted_company(filters):
	filters = filters or {}
	company = filters.get("company")
	if not company:
		frappe.throw(_("Company is required to run this report."))
	frappe.has_permission("Company", "read", company, throw=True)
	return company


def validate_employee_fields(required_fields):
	meta = frappe.get_meta("Employee")
	missing_fields = sorted(field for field in required_fields if not meta.has_field(field))
	if missing_fields:
		frappe.throw(
			_("Employment Equity setup is incomplete. Missing Employee fields: {0}").format(
				", ".join(missing_fields)
			),
			title=_("Setup Required"),
		)
