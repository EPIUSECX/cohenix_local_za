# EEA2 Income Differentials Report

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Occupational Level"), "fieldname": "occupational_level", "fieldtype": "Data", "width": 150},
        {"label": _("Race"), "fieldname": "race", "fieldtype": "Data", "width": 100},
        {"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 100},
        {"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 80},
        {"label": _("Total Remuneration"), "fieldname": "total_remuneration", "fieldtype": "Currency", "width": 150},
        {"label": _("Average Remuneration"), "fieldname": "avg_remuneration", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    company = filters.get("company")
    
    query = """
        SELECT 
            e.za_occupational_level as occupational_level,
            e.za_race as race,
            e.gender,
            COUNT(*) as count,
            SUM(ssa.base) as total_remuneration,
            AVG(ssa.base) as avg_remuneration
        FROM `tabEmployee` e
        LEFT JOIN `tabSalary Structure Assignment` ssa ON ssa.employee = e.name AND ssa.docstatus = 1
        WHERE e.company = %(company)s
            AND e.status = 'Active'
            AND e.za_occupational_level IS NOT NULL
            AND e.za_race IS NOT NULL
        GROUP BY e.za_occupational_level, e.za_race, e.gender
        ORDER BY e.za_occupational_level, e.za_race, e.gender
    """
    
    return frappe.db.sql(query, {"company": company}, as_dict=1)
