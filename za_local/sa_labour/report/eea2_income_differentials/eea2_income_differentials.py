from __future__ import annotations

import frappe
from frappe import _

from za_local.sa_labour.report_utils import get_permitted_company, validate_employee_fields


def execute(filters=None):
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Occupational Level"),
			"fieldname": "occupational_level",
			"fieldtype": "Data",
			"width": 150,
		},
		{"label": _("Race"), "fieldname": "race", "fieldtype": "Data", "width": 100},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 100},
		{"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 80},
		{
			"label": _("Total Remuneration"),
			"fieldname": "total_remuneration",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Average Remuneration"),
			"fieldname": "avg_remuneration",
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	company = get_permitted_company(filters)
	validate_employee_fields({"za_occupational_level", "za_race"})
	return frappe.db.sql(
		"""
			SELECT
				e.za_occupational_level AS occupational_level,
				e.za_race AS race,
				e.gender,
				COUNT(e.name) AS count,
				SUM(IFNULL(ssa.base, 0)) AS total_remuneration,
				AVG(IFNULL(ssa.base, 0)) AS avg_remuneration
			FROM `tabEmployee` e
			LEFT JOIN `tabSalary Structure Assignment` ssa
				ON ssa.name = (
					SELECT latest.name
					FROM `tabSalary Structure Assignment` latest
					WHERE latest.employee = e.name
						AND latest.company = e.company
						AND latest.docstatus = 1
						AND latest.from_date <= CURRENT_DATE
					ORDER BY latest.from_date DESC, latest.creation DESC
					LIMIT 1
				)
			WHERE e.company = %(company)s
				AND e.status = 'Active'
				AND e.za_occupational_level IS NOT NULL
				AND e.za_race IS NOT NULL
			GROUP BY e.za_occupational_level, e.za_race, e.gender
			ORDER BY e.za_occupational_level, e.za_race, e.gender
		""",
		{"company": company},
		as_dict=True,
	)
