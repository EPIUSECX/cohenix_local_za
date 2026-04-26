import frappe
from frappe import _


RETIREMENT_FUND_CODES = {"4001", "4003", "4006", "4007"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": _("Salary Component"), "fieldname": "salary_component", "fieldtype": "Link", "options": "Salary Component", "width": 220},
		{"label": _("SARS Code"), "fieldname": "za_sars_payroll_code", "fieldtype": "Data", "width": 90},
		{"label": _("Employee Deduction"), "fieldname": "employee_deduction", "fieldtype": "Currency", "width": 140},
		{"label": _("Employer Contribution"), "fieldname": "employer_contribution", "fieldtype": "Currency", "width": 150},
		{"label": _("Retirement Taxable Excess"), "fieldname": "retirement_taxable_excess", "fieldtype": "Currency", "width": 170},
	]


def get_data(filters):
	if not filters.get("company"):
		return []

	conditions = [
		"ss.company = %(company)s",
		"ss.docstatus = 1",
	]
	if filters.get("from_date"):
		conditions.append("ss.start_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("ss.end_date <= %(to_date)s")
	if filters.get("employee"):
		conditions.append("ss.employee = %(employee)s")
	if filters.get("department"):
		conditions.append("e.department = %(department)s")

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			ss.name AS salary_slip,
			ss.employee,
			ss.employee_name,
			e.department,
			ss.posting_date,
			src.salary_component,
			sc.za_sars_payroll_code,
			SUM(CASE WHEN src.source_table = 'deductions' THEN src.amount ELSE 0 END) AS employee_deduction,
			SUM(CASE WHEN src.source_table = 'company_contribution' THEN src.amount ELSE 0 END) AS employer_contribution,
			MAX(IFNULL(ss.za_retirement_fund_taxable_excess, 0)) AS retirement_taxable_excess
		FROM (
			SELECT parent, salary_component, amount, 'deductions' AS source_table
			FROM `tabSalary Detail`
			WHERE parenttype = 'Salary Slip' AND parentfield = 'deductions'
			UNION ALL
			SELECT parent, salary_component, amount, 'company_contribution' AS source_table
			FROM `tabCompany Contribution`
		) src
		INNER JOIN `tabSalary Slip` ss ON ss.name = src.parent
		INNER JOIN `tabEmployee` e ON e.name = ss.employee
		LEFT JOIN `tabSalary Component` sc ON sc.name = src.salary_component
		WHERE {where_clause}
			AND (
				sc.za_sars_payroll_code IN %(retirement_codes)s
				OR LOWER(src.salary_component) LIKE '%%pension%%'
				OR LOWER(src.salary_component) LIKE '%%provident%%'
				OR LOWER(src.salary_component) LIKE '%%retirement annuity%%'
				OR LOWER(src.salary_component) LIKE '%%retirement fund%%'
			)
		GROUP BY
			ss.name,
			ss.employee,
			ss.employee_name,
			e.department,
			ss.posting_date,
			src.salary_component,
			sc.za_sars_payroll_code
		ORDER BY ss.posting_date, ss.employee_name, src.salary_component
		""",
		{**filters, "retirement_codes": tuple(RETIREMENT_FUND_CODES)},
		as_dict=True,
	)
