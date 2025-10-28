# Statutory Submissions Summary Report

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart

def get_columns():
	return [
		{"label": _("Component"), "fieldname": "component", "fieldtype": "Data", "width": 150},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150}
	]

def get_data(filters):
	# Get totals for PAYE, UIF, SDL, ETI
	query = """
		SELECT
			sd.salary_component as component,
			SUM(sd.amount) as amount
		FROM `tabSalary Detail` sd
		INNER JOIN `tabSalary Slip` ss ON ss.name = sd.parent
		WHERE ss.company = %(company)s
			AND ss.start_date >= %(from_date)s
			AND ss.end_date <= %(to_date)s
			AND ss.docstatus = 1
			AND sd.salary_component IN ('PAYE', 'UIF', 'SDL', 'ETI')
		GROUP BY sd.salary_component
		ORDER BY sd.salary_component
	"""
	
	return frappe.db.sql(query, filters, as_dict=1)

def get_chart_data(data):
	return {
		"data": {
			"labels": [d.component for d in data],
			"datasets": [{"values": [d.amount for d in data]}]
		},
		"type": "bar"
	}
