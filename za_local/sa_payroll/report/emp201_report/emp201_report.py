# Copyright (c) 2024, Kartoza and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "name", "label": _("EMP201 Reference"), "fieldtype": "Link", "options": "EMP201 Submission", "width": 180},
        {"fieldname": "company", "label": _("Company"), "fieldtype": "Link", "options": "Company", "width": 120},
        {"fieldname": "month", "label": _("Month"), "fieldtype": "Data", "width": 100},
        {"fieldname": "fiscal_year", "label": _("Fiscal Year"), "fieldtype": "Link", "options": "Fiscal Year", "width": 100},
        {"fieldname": "submission_period_start_date", "label": _("Period Start Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "submission_period_end_date", "label": _("Period End Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "gross_paye_before_eti", "label": _("Gross PAYE"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "eti_utilized_current_month", "label": _("ETI Utilized"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "net_paye_payable", "label": _("Net PAYE Payable"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "uif_payable", "label": _("UIF Payable"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "sdl_payable", "label": _("SDL Payable"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "total_payable", "label": _("Total Payable"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    conditions = []
    values = {}

    if filters:
        if filters.get("company"):
            conditions.append("company = %(company)s")
            values["company"] = filters["company"]
        if filters.get("fiscal_year"):
            conditions.append("fiscal_year = %(fiscal_year)s")
            values["fiscal_year"] = filters["fiscal_year"]
        if filters.get("month"):
            conditions.append("month = %(month)s")
            values["month"] = filters["month"]
        if filters.get("from_date") and filters.get("to_date"):
            # Assuming the filter dates should apply to the posting_date of the submission
            conditions.append("posting_date BETWEEN %(from_date)s AND %(to_date)s")
            values["from_date"] = filters["from_date"]
            values["to_date"] = filters["to_date"]
        elif filters.get("from_date"):
            conditions.append("posting_date >= %(from_date)s")
            values["from_date"] = filters["from_date"]
        elif filters.get("to_date"):
            conditions.append("posting_date <= %(to_date)s")
            values["to_date"] = filters["to_date"]
            
    sql_conditions = "WHERE " + " AND ".join(conditions) if conditions else ""

    data = frappe.db.sql(f"""
        SELECT
            name, company, month, fiscal_year, 
            submission_period_start_date, submission_period_end_date,
            gross_paye_before_eti, eti_utilized_current_month,
            net_paye_payable, uif_payable, sdl_payable,
            (net_paye_payable + uif_payable + sdl_payable) as total_payable,
            status 
        FROM `tabEMP201 Submission`
        {sql_conditions}
        ORDER BY posting_date DESC
    """, values, as_dict=1)

    return data
