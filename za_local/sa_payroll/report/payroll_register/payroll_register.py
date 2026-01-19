# Payroll Register Report

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 120},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 120},
		{"label": _("Basic"), "fieldname": "basic", "fieldtype": "Currency", "width": 100},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 120},
		{"label": _("PAYE"), "fieldname": "paye", "fieldtype": "Currency", "width": 100},
		{"label": _("UIF"), "fieldname": "uif", "fieldtype": "Currency", "width": 80},
		{"label": _("Total Deductions"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 120},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 120}
	]

def get_data(filters):
	query = """
		SELECT
			ss.employee,
			ss.employee_name,
			e.department,
			e.designation,
			(SELECT SUM(amount) FROM `tabSalary Detail` WHERE parent = ss.name AND salary_component IN ('Basic', 'Basic Salary') AND parentfield = 'earnings') as basic,
			ss.gross_pay,
			ss.total_deduction,
			ss.net_pay,
			(SELECT SUM(amount) FROM `tabSalary Detail` WHERE parent = ss.name AND salary_component = 'PAYE' AND parentfield = 'deductions') as paye,
			(SELECT SUM(amount) FROM `tabSalary Detail` WHERE parent = ss.name AND salary_component = 'UIF' AND parentfield = 'deductions') as uif
		FROM `tabSalary Slip` ss
		INNER JOIN `tabEmployee` e ON e.name = ss.employee
		WHERE ss.company = %(company)s
			AND ss.start_date >= %(from_date)s
			AND ss.end_date <= %(to_date)s
			AND ss.docstatus = 1
		ORDER BY e.department, ss.employee_name
	"""
	
	return frappe.db.sql(query, filters, as_dict=1)
