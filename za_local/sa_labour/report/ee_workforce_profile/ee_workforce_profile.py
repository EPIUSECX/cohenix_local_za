from __future__ import annotations

import frappe
from frappe import _

from za_local.sa_labour.report_utils import get_permitted_company, validate_employee_fields


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Metric"), "fieldname": "metric", "fieldtype": "Data", "width": 200},
		{"label": _("African"), "fieldname": "african", "fieldtype": "Int", "width": 100},
		{"label": _("Coloured"), "fieldname": "coloured", "fieldtype": "Int", "width": 100},
		{"label": _("Indian"), "fieldname": "indian", "fieldtype": "Int", "width": 100},
		{"label": _("White"), "fieldname": "white", "fieldtype": "Int", "width": 100},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
	]


def get_data(filters):
	company = get_permitted_company(filters)
	validate_employee_fields({"za_is_disabled", "za_race"})
	params = {"company": company}

	totals = frappe.db.sql(
		"""
			SELECT
				SUM(CASE WHEN za_race = 'African' THEN 1 ELSE 0 END) AS african,
				SUM(CASE WHEN za_race = 'Coloured' THEN 1 ELSE 0 END) AS coloured,
				SUM(CASE WHEN za_race = 'Indian' THEN 1 ELSE 0 END) AS indian,
				SUM(CASE WHEN za_race = 'White' THEN 1 ELSE 0 END) AS white,
				COUNT(*) AS total
			FROM `tabEmployee`
			WHERE company = %(company)s AND status = 'Active'
		""",
		params,
		as_dict=True,
	)[0]
	data = [{"metric": _("Total Employees"), **totals}]

	data.extend(
		frappe.db.sql(
			"""
				SELECT
					gender AS metric,
					SUM(CASE WHEN za_race = 'African' THEN 1 ELSE 0 END) AS african,
					SUM(CASE WHEN za_race = 'Coloured' THEN 1 ELSE 0 END) AS coloured,
					SUM(CASE WHEN za_race = 'Indian' THEN 1 ELSE 0 END) AS indian,
					SUM(CASE WHEN za_race = 'White' THEN 1 ELSE 0 END) AS white,
					COUNT(*) AS total
				FROM `tabEmployee`
				WHERE company = %(company)s AND status = 'Active'
				GROUP BY gender
			""",
			params,
			as_dict=True,
		)
	)

	disabled = frappe.db.sql(
		"""
			SELECT
				SUM(CASE WHEN za_race = 'African' AND za_is_disabled = 1 THEN 1 ELSE 0 END) AS african,
				SUM(CASE WHEN za_race = 'Coloured' AND za_is_disabled = 1 THEN 1 ELSE 0 END) AS coloured,
				SUM(CASE WHEN za_race = 'Indian' AND za_is_disabled = 1 THEN 1 ELSE 0 END) AS indian,
				SUM(CASE WHEN za_race = 'White' AND za_is_disabled = 1 THEN 1 ELSE 0 END) AS white,
				SUM(CASE WHEN za_is_disabled = 1 THEN 1 ELSE 0 END) AS total
			FROM `tabEmployee`
			WHERE company = %(company)s AND status = 'Active'
		""",
		params,
		as_dict=True,
	)[0]
	data.append({"metric": _("Persons with Disabilities"), **disabled})
	return data
