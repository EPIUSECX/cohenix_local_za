# EE Workforce Profile Report

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Metric"), "fieldname": "metric", "fieldtype": "Data", "width": 200},
        {"label": _("African"), "fieldname": "african", "fieldtype": "Int", "width": 100},
        {"label": _("Coloured"), "fieldname": "coloured", "fieldtype": "Int", "width": 100},
        {"label": _("Indian"), "fieldname": "indian", "fieldtype": "Int", "width": 100},
        {"label": _("White"), "fieldname": "white", "fieldtype": "Int", "width": 100},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
    ]

def get_data(filters):
    company = filters.get("company")
    
    data = []
    
    # Overall totals
    totals = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN za_race = 'African' THEN 1 ELSE 0 END) as african,
            SUM(CASE WHEN za_race = 'Coloured' THEN 1 ELSE 0 END) as coloured,
            SUM(CASE WHEN za_race = 'Indian' THEN 1 ELSE 0 END) as indian,
            SUM(CASE WHEN za_race = 'White' THEN 1 ELSE 0 END) as white,
            COUNT(*) as total
        FROM `tabEmployee`
        WHERE company = %(company)s AND status = 'Active'
    """, {"company": company}, as_dict=1)[0]
    
    data.append({
        "metric": "Total Employees",
        **totals
    })
    
    # By Gender
    gender_data = frappe.db.sql("""
        SELECT 
            gender as metric,
            SUM(CASE WHEN za_race = 'African' THEN 1 ELSE 0 END) as african,
            SUM(CASE WHEN za_race = 'Coloured' THEN 1 ELSE 0 END) as coloured,
            SUM(CASE WHEN za_race = 'Indian' THEN 1 ELSE 0 END) as indian,
            SUM(CASE WHEN za_race = 'White' THEN 1 ELSE 0 END) as white,
            COUNT(*) as total
        FROM `tabEmployee`
        WHERE company = %(company)s AND status = 'Active'
        GROUP BY gender
    """, {"company": company}, as_dict=1)
    
    data.extend(gender_data)
    
    # Disabled
    disabled_data = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN za_race = 'African' AND za_is_disabled = 1 THEN 1 ELSE 0 END) as african,
            SUM(CASE WHEN za_race = 'Coloured' AND za_is_disabled = 1 THEN 1 ELSE 0 END) as coloured,
            SUM(CASE WHEN za_race = 'Indian' AND za_is_disabled = 1 THEN 1 ELSE 0 END) as indian,
            SUM(CASE WHEN za_race = 'White' AND za_is_disabled = 1 THEN 1 ELSE 0 END) as white,
            SUM(CASE WHEN za_is_disabled = 1 THEN 1 ELSE 0 END) as total
        FROM `tabEmployee`
        WHERE company = %(company)s AND status = 'Active'
    """, {"company": company}, as_dict=1)[0]
    
    data.append({
        "metric": "Persons with Disabilities",
        **disabled_data
    })
    
    return data
