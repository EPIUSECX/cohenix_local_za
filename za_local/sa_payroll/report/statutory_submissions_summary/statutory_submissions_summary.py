# Statutory Submissions Summary Report

import frappe
from frappe import _


def execute(filters=None):
	filters = _validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart


def _validate_filters(filters):
	filters = frappe._dict(filters or {})
	if not filters.company or not filters.from_date or not filters.to_date:
		frappe.throw(_("Company, From Date, and To Date are required."))
	frappe.has_permission("Company", "read", doc=filters.company, throw=True)
	return filters


def get_columns():
	return [
		{"label": _("Component"), "fieldname": "component", "fieldtype": "Data", "width": 150},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
	]


def get_data(filters):
	# Get totals for PAYE, UIF, SDL, and ETI using SARS code mappings.
	query = """
		SELECT component, SUM(amount) AS amount
		FROM (
			SELECT
				CASE
					WHEN sd.salary_component = 'PAYE' OR sc.za_sars_payroll_code = '4102' THEN 'PAYE'
					WHEN sd.salary_component IN ('UIF', 'UIF Employee Contribution') OR sc.za_sars_payroll_code = '4141' THEN 'UIF Employee Contribution'
					WHEN (sd.salary_component = 'ETI' OR sc.za_sars_payroll_code = '4118')
						AND IFNULL(ss.za_monthly_eti, 0) = 0 THEN 'ETI'
				END AS component,
				sd.amount AS amount
			FROM `tabSalary Detail` sd
			INNER JOIN `tabSalary Slip` ss ON ss.name = sd.parent
			LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
			WHERE ss.company = %(company)s
				AND ss.end_date BETWEEN %(from_date)s AND %(to_date)s
				AND ss.docstatus = 1
				AND sd.parentfield = 'deductions'

			UNION ALL

			SELECT
				CASE
					WHEN cc.salary_component IN ('UIF Employer Contribution') OR sc.za_sars_payroll_code = '4141' THEN 'UIF Employer Contribution'
					WHEN cc.salary_component IN ('SDL', 'SDL Contribution', 'Skills Development Levy') OR sc.za_sars_payroll_code = '4142' THEN 'SDL Contribution'
				END AS component,
				cc.amount AS amount
			FROM `tabCompany Contribution` cc
			INNER JOIN `tabSalary Slip` ss ON ss.name = cc.parent
			LEFT JOIN `tabSalary Component` sc ON sc.name = cc.salary_component
			WHERE ss.company = %(company)s
				AND ss.end_date BETWEEN %(from_date)s AND %(to_date)s
				AND ss.docstatus = 1
				AND cc.parenttype = 'Salary Slip'

			UNION ALL

			SELECT
				'ETI' AS component,
				ss.za_monthly_eti AS amount
			FROM `tabSalary Slip` ss
			WHERE ss.company = %(company)s
				AND ss.end_date BETWEEN %(from_date)s AND %(to_date)s
				AND ss.docstatus = 1
				AND IFNULL(ss.za_monthly_eti, 0) != 0
		) statutory
		WHERE component IS NOT NULL
		GROUP BY component
		ORDER BY FIELD(component, 'PAYE', 'UIF Employee Contribution', 'UIF Employer Contribution', 'SDL Contribution', 'ETI'), component
	"""

	return frappe.db.sql(query, filters, as_dict=1)


def get_chart_data(data):
	return {
		"data": {"labels": [d.component for d in data], "datasets": [{"values": [d.amount for d in data]}]},
		"type": "bar",
	}
