# EEA4 Employment Equity Plan Report

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Occupational Level"), "fieldname": "occupational_level", "fieldtype": "Data", "width": 150},
        {"label": _("Current African"), "fieldname": "current_african", "fieldtype": "Int", "width": 100},
        {"label": _("Current Coloured"), "fieldname": "current_coloured", "fieldtype": "Int", "width": 100},
        {"label": _("Current Indian"), "fieldname": "current_indian", "fieldtype": "Int", "width": 100},
        {"label": _("Current White"), "fieldname": "current_white", "fieldtype": "Int", "width": 100},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
    ]

def get_data(filters):
    company = filters.get("company")
    
    query = """
        SELECT 
            za_occupational_level as occupational_level,
            SUM(CASE WHEN za_race = 'African' THEN 1 ELSE 0 END) as current_african,
            SUM(CASE WHEN za_race = 'Coloured' THEN 1 ELSE 0 END) as current_coloured,
            SUM(CASE WHEN za_race = 'Indian' THEN 1 ELSE 0 END) as current_indian,
            SUM(CASE WHEN za_race = 'White' THEN 1 ELSE 0 END) as current_white,
            COUNT(*) as total
        FROM `tabEmployee`
        WHERE company = %(company)s
            AND status = 'Active'
            AND za_occupational_level IS NOT NULL
        GROUP BY za_occupational_level
        ORDER BY za_occupational_level
    """
    
    return frappe.db.sql(query, {"company": company}, as_dict=1)
