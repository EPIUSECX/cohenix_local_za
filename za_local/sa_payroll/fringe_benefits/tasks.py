"""Scheduled maintenance for submitted Fringe Benefit records."""

import frappe
from frappe.utils import get_first_day, getdate, today

from za_local.sa_payroll.doctype.fringe_benefit.fringe_benefit import _assessment_year_end


def refresh_fringe_benefit_statuses():
	"""Refresh date-derived status and extend open-ended tax-year breakdowns."""
	current_date = getdate(today())
	failures = []
	benefits = frappe.get_all(
		"Fringe Benefit",
		filters={"docstatus": 1},
		fields=["name", "from_date", "to_date", "status"],
		order_by="name",
	)
	latest_breakdown_months = _get_latest_breakdown_months(
		[row.name for row in benefits if not row.to_date]
	)
	for row in benefits:
		try:
			status = _status_for_dates(row.from_date, row.to_date, current_date)
			if row.status != status:
				frappe.db.set_value(
					"Fringe Benefit",
					row.name,
					"status",
					status,
					update_modified=False,
				)
			if not row.to_date and _breakdown_needs_extension(
				latest_breakdown_months.get(row.name),
				_assessment_year_end(max(current_date, getdate(row.from_date))),
			):
				doc = frappe.get_doc("Fringe Benefit", row.name)
				doc.generate_monthly_breakdown()
				doc.save()
		except Exception:
			failures.append(row.name)
			frappe.log_error(
				title=f"Fringe Benefit refresh failed - {row.name}",
				message=frappe.get_traceback(),
			)

	if failures:
		raise frappe.ValidationError("Fringe Benefit refresh failed for: " + ", ".join(failures))


def _status_for_dates(from_date, to_date, current_date):
	if getdate(from_date) > current_date:
		return "Pending"
	if to_date and getdate(to_date) < current_date:
		return "Expired"
	return "Active"


def _get_latest_breakdown_months(parent_names):
	if not parent_names:
		return {}
	rows = frappe.get_all(
		"Fringe Benefit Detail",
		filters={
			"parent": ["in", parent_names],
			"parenttype": "Fringe Benefit",
			"parentfield": "monthly_breakdown",
		},
		fields=["parent", {"MAX": "month", "as": "latest_month"}],
		group_by="parent",
	)
	return {row.parent: row.latest_month for row in rows}


def _breakdown_needs_extension(latest_month, expected_end):
	return not latest_month or get_first_day(latest_month) != get_first_day(expected_end)
