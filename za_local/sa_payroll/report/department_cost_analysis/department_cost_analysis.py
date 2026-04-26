# Department Cost Analysis Report

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Employee Count"), "fieldname": "employee_count", "fieldtype": "Int", "width": 120},
		{"label": _("Total Gross"), "fieldname": "total_gross", "fieldtype": "Currency", "width": 150},
		{"label": _("Total PAYE"), "fieldname": "total_paye", "fieldtype": "Currency", "width": 120},
		{"label": _("Total UIF"), "fieldname": "total_uif", "fieldtype": "Currency", "width": 100},
		{"label": _("Total SDL"), "fieldname": "total_sdl", "fieldtype": "Currency", "width": 100},
		{"label": _("Total Deductions"), "fieldname": "total_deductions", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Net Pay"), "fieldname": "total_net", "fieldtype": "Currency", "width": 150}
	]

def get_data(filters):
	query = """
		SELECT
			e.department,
			COUNT(DISTINCT ss.employee) as employee_count,
			SUM(ss.gross_pay) as total_gross,
			SUM(ss.total_deduction) as total_deductions,
			SUM(ss.net_pay) as total_net,
			SUM((
				SELECT IFNULL(SUM(sd.amount), 0)
				FROM `tabSalary Detail` sd
				LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE sd.parent = ss.name
					AND sd.parentfield = 'deductions'
					AND (sd.salary_component = 'PAYE' OR sc.za_sars_payroll_code = '4102')
			)) as total_paye,
			SUM((
				SELECT IFNULL(SUM(sd.amount), 0)
				FROM `tabSalary Detail` sd
				LEFT JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE sd.parent = ss.name
					AND sd.parentfield = 'deductions'
					AND (sd.salary_component IN ('UIF', 'UIF Employee Contribution')
						OR sc.za_sars_payroll_code = '4141')
			) + (
				SELECT IFNULL(SUM(cc.amount), 0)
				FROM `tabCompany Contribution` cc
				LEFT JOIN `tabSalary Component` sc ON sc.name = cc.salary_component
				WHERE cc.parent = ss.name
					AND (cc.salary_component = 'UIF Employer Contribution'
						OR sc.za_sars_payroll_code = '4141')
			)) as total_uif,
			SUM((
				SELECT IFNULL(SUM(cc.amount), 0)
				FROM `tabCompany Contribution` cc
				LEFT JOIN `tabSalary Component` sc ON sc.name = cc.salary_component
				WHERE cc.parent = ss.name
					AND (cc.salary_component IN ('SDL', 'SDL Contribution', 'Skills Development Levy')
						OR sc.za_sars_payroll_code = '4142')
			)) as total_sdl
		FROM `tabSalary Slip` ss
		INNER JOIN `tabEmployee` e ON e.name = ss.employee
		WHERE ss.company = %(company)s
			AND ss.start_date >= %(from_date)s
			AND ss.end_date <= %(to_date)s
			AND ss.docstatus = 1
		GROUP BY e.department
		ORDER BY total_gross DESC
	"""

	return frappe.db.sql(query, filters, as_dict=1)
