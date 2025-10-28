# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
    if not filters:
        filters = {}
        
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    """Return columns for the report"""
    columns = [
        {
            "label": _("Document Type"),
            "fieldname": "document_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Document"),
            "fieldname": "document",
            "fieldtype": "Dynamic Link",
            "options": "document_type",
            "width": 180
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 90
        },
        {
            "label": _("Customer/Supplier"),
            "fieldname": "party",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("VAT Rate"),
            "fieldname": "vat_rate",
            "fieldtype": "Percent",
            "width": 80
        },
        {
            "label": _("Net Amount"),
            "fieldname": "net_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("VAT Amount"),
            "fieldname": "vat_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("VAT Type"),
            "fieldname": "vat_type",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("VAT Account"),
            "fieldname": "vat_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 180
        }
    ]
    
    return columns

def get_data(filters):
    """Get data for the report"""
    data = []
    
    # Get VAT settings
    vat_settings = frappe.get_doc("South African VAT Settings")
    
    # Get date range
    from_date, to_date = get_date_range(filters)
    
    # Get sales invoices with VAT
    sales_invoices = get_sales_invoices(filters, from_date, to_date, vat_settings)
    data.extend(sales_invoices)
    
    # Get purchase invoices with VAT
    purchase_invoices = get_purchase_invoices(filters, from_date, to_date, vat_settings)
    data.extend(purchase_invoices)
    
    return data

def get_date_range(filters):
    """Get date range from filters"""
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    return from_date, to_date

def get_sales_invoices(filters, from_date, to_date, vat_settings):
    """Get sales invoices with VAT"""
    result = []
    
    # Query sales invoices
    conditions = ""
    if from_date:
        conditions += f" AND posting_date >= '{from_date}'"
    if to_date:
        conditions += f" AND posting_date <= '{to_date}'"
    if filters.get("company"):
        conditions += f" AND company = '{filters.get('company')}'"
        
    sales_invoices = frappe.db.sql(f"""
        SELECT 
            name, posting_date, customer, customer_name, 
            base_net_total, base_total, base_total_taxes_and_charges
        FROM 
            `tabSales Invoice`
        WHERE 
            docstatus = 1 
            AND base_total_taxes_and_charges > 0
            {conditions}
        ORDER BY 
            posting_date
    """, as_dict=1)
    
    # Process each invoice
    for invoice in sales_invoices:
        # Get tax details
        taxes = frappe.db.sql(f"""
            SELECT 
                account_head, rate, tax_amount, item_wise_tax_detail
            FROM 
                `tabSales Taxes and Charges`
            WHERE 
                parent = '{invoice.name}'
                AND account_head = '{vat_settings.output_vat_account}'
        """, as_dict=1)
        
        for tax in taxes:
            result.append({
                "document_type": "Sales Invoice",
                "document": invoice.name,
                "date": invoice.posting_date,
                "party": invoice.customer_name or invoice.customer,
                "vat_rate": tax.rate,
                "net_amount": invoice.base_net_total,
                "vat_amount": tax.tax_amount,
                "total_amount": invoice.base_total,
                "vat_type": "Output VAT",
                "vat_account": tax.account_head
            })
            
    return result

def get_purchase_invoices(filters, from_date, to_date, vat_settings):
    """Get purchase invoices with VAT"""
    result = []
    
    # Query purchase invoices
    conditions = ""
    if from_date:
        conditions += f" AND posting_date >= '{from_date}'"
    if to_date:
        conditions += f" AND posting_date <= '{to_date}'"
    if filters.get("company"):
        conditions += f" AND company = '{filters.get('company')}'"
        
    purchase_invoices = frappe.db.sql(f"""
        SELECT 
            name, posting_date, supplier, supplier_name, 
            base_net_total, base_total, base_total_taxes_and_charges
        FROM 
            `tabPurchase Invoice`
        WHERE 
            docstatus = 1 
            AND base_total_taxes_and_charges > 0
            {conditions}
        ORDER BY 
            posting_date
    """, as_dict=1)
    
    # Process each invoice
    for invoice in purchase_invoices:
        # Get tax details
        taxes = frappe.db.sql(f"""
            SELECT 
                account_head, rate, tax_amount, item_wise_tax_detail
            FROM 
                `tabPurchase Taxes and Charges`
            WHERE 
                parent = '{invoice.name}'
                AND account_head = '{vat_settings.input_vat_account}'
        """, as_dict=1)
        
        for tax in taxes:
            result.append({
                "document_type": "Purchase Invoice",
                "document": invoice.name,
                "date": invoice.posting_date,
                "party": invoice.supplier_name or invoice.supplier,
                "vat_rate": tax.rate,
                "net_amount": invoice.base_net_total,
                "vat_amount": tax.tax_amount,
                "total_amount": invoice.base_total,
                "vat_type": "Input VAT",
                "vat_account": tax.account_head
            })
            
    return result
