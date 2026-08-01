# Payroll Register Report

import frappe
from frappe import _


def execute(filters=None):
	filters = _validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def _validate_filters(filters):
	filters = frappe._dict(filters or {})
	if not filters.company or not filters.from_date or not filters.to_date:
		frappe.throw(_("Company, From Date, and To Date are required."))
	frappe.has_permission("Company", "read", doc=filters.company, throw=True)
	return filters


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 120,
		},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 120},
		{"label": _("Basic"), "fieldname": "basic", "fieldtype": "Currency", "width": 100},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 120},
		{"label": _("PAYE"), "fieldname": "paye", "fieldtype": "Currency", "width": 100},
		{"label": _("UIF"), "fieldname": "uif", "fieldtype": "Currency", "width": 80},
		{
			"label": _("Total Deductions"),
			"fieldname": "total_deduction",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	query = """
		SELECT
			ss.employee,
			ss.employee_name,
			e.department,
			e.designation,
			(
				SELECT SUM(sd.amount)
				FROM `tabSalary Detail` sd
				LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE sd.parent = ss.name
					AND sd.parentfield = 'earnings'
					AND (sd.salary_component IN ('Basic', 'Basic Salary') OR sc.za_sars_payroll_code = '3601')
			) as basic,
			ss.gross_pay,
			ss.total_deduction,
			ss.net_pay,
			(
				SELECT SUM(sd.amount)
				FROM `tabSalary Detail` sd
				LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE sd.parent = ss.name
					AND sd.parentfield = 'deductions'
					AND (sd.salary_component = 'PAYE' OR sc.za_sars_payroll_code = '4102')
			) as paye,
			(
				SELECT SUM(sd.amount)
				FROM `tabSalary Detail` sd
				LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE sd.parent = ss.name
					AND sd.parentfield = 'deductions'
					AND (sd.salary_component IN ('UIF', 'UIF Employee Contribution') OR sc.za_sars_payroll_code = '4141')
			) as uif
		FROM `tabSalary Slip` ss
		INNER JOIN `tabEmployee` e ON e.name = ss.employee
		WHERE ss.company = %(company)s
			AND ss.end_date BETWEEN %(from_date)s AND %(to_date)s
			AND ss.docstatus = 1
		ORDER BY e.department, ss.employee_name
	"""

	return frappe.db.sql(query, filters, as_dict=1)
