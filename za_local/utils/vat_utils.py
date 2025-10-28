"""
VAT Utility Functions

Utilities for South African Value Added Tax (VAT) calculations and compliance.
"""

import frappe
from frappe.utils import flt


def calculate_vat_amounts(net_amount, vat_rate=15.0, is_inclusive=True):
    """
    Calculate VAT amounts for a transaction.
    
    Args:
        net_amount (float): Net amount (excluding VAT if is_inclusive=False)
        vat_rate (float): VAT rate percentage (default 15%)
        is_inclusive (bool): Whether VAT is included in net_amount
        
    Returns:
        dict: {net: float, vat: float, gross: float}
    """
    vat_rate = flt(vat_rate)
    net_amount = flt(net_amount)
    
    if is_inclusive:
        # VAT is included in the amount
        gross_amount = net_amount
        vat_divisor = 100 + vat_rate
        vat_amount = (gross_amount * vat_rate) / vat_divisor
        net_amount = gross_amount - vat_amount
    else:
        # VAT is not included
        vat_amount = (net_amount * vat_rate) / 100
        gross_amount = net_amount + vat_amount
    
    return {
        "net": flt(net_amount, 2),
        "vat": flt(vat_amount, 2),
        "gross": flt(gross_amount, 2)
    }


def get_vat_rate(item_code=None, company=None):
    """
    Get applicable VAT rate.
    
    Args:
        item_code (str): Optional item code for item-specific rates
        company (str): Optional company for company-specific settings
        
    Returns:
        float: VAT rate percentage
    """
    # Get VAT settings
    vat_settings = frappe.get_all(
        "SA VAT Settings",
        filters={"company": company} if company else {},
        fields=["name"],
        limit=1
    )
    
    if not vat_settings:
        # Default to 15% if no settings found
        return 15.0
    
    settings_doc = frappe.get_doc("SA VAT Settings", vat_settings[0].name)
    
    # Get standard rate
    if settings_doc.vat_rates:
        for rate in settings_doc.vat_rates:
            if rate.is_standard_rate:
                return flt(rate.rate)
    
    # Default to 15%
    return 15.0


def validate_vat_rates(vat_rates):
    """
    Validate VAT rate configuration.
    
    Args:
        vat_rates (list): List of VAT rate entries
        
    Returns:
        dict: {valid: bool, errors: list}
    """
    errors = []
    
    if not vat_rates:
        errors.append("At least one VAT rate must be configured")
        return {"valid": False, "errors": errors}
    
    standard_count = 0
    
    for rate in vat_rates:
        # Check for standard rate
        if rate.is_standard_rate:
            standard_count += 1
            
            # Standard rate should be positive
            if flt(rate.rate) <= 0:
                errors.append("Standard VAT rate must be greater than 0")
        
        # Zero-rated items must have 0% rate
        if rate.is_zero_rated and flt(rate.rate) != 0:
            errors.append(f"Zero-rated items must have 0% rate, not {rate.rate}%")
        
        # Exempt items must have 0% rate
        if rate.is_exempt and flt(rate.rate) != 0:
            errors.append(f"Exempt items must have 0% rate, not {rate.rate}%")
        
        # Can't be both zero-rated and exempt
        if rate.is_zero_rated and rate.is_exempt:
            errors.append("Rate cannot be both zero-rated and exempt")
    
    # Must have exactly one standard rate
    if standard_count == 0:
        errors.append("Exactly one standard VAT rate must be configured")
    elif standard_count > 1:
        errors.append(f"Only one standard VAT rate allowed, found {standard_count}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def calculate_vat201_totals(company, from_date, to_date):
    """
    Calculate VAT201 return totals for a period.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        
    Returns:
        dict: VAT201 calculation results
    """
    # Get VAT settings
    vat_settings = frappe.get_all(
        "SA VAT Settings",
        filters={"company": company},
        fields=["name", "output_vat_account", "input_vat_account"],
        limit=1
    )
    
    if not vat_settings:
        frappe.throw(f"VAT Settings not configured for {company}")
    
    settings = vat_settings[0]
    
    # Calculate output VAT (sales)
    output_vat = get_vat_from_transactions(
        company, 
        from_date, 
        to_date, 
        "Sales Invoice",
        settings.output_vat_account
    )
    
    # Calculate input VAT (purchases)
    input_vat = get_vat_from_transactions(
        company, 
        from_date, 
        to_date, 
        "Purchase Invoice",
        settings.input_vat_account
    )
    
    # Calculate net VAT payable/refundable
    net_vat = output_vat["total_vat"] - input_vat["total_vat"]
    
    return {
        "output_vat": flt(output_vat["total_vat"], 2),
        "input_vat": flt(input_vat["total_vat"], 2),
        "net_vat": flt(net_vat, 2),
        "vat_payable": flt(net_vat, 2) if net_vat > 0 else 0,
        "vat_refundable": flt(abs(net_vat), 2) if net_vat < 0 else 0,
        "standard_rated_supplies": flt(output_vat["standard_rated"], 2),
        "zero_rated_supplies": flt(output_vat["zero_rated"], 2),
        "exempt_supplies": flt(output_vat["exempt"], 2)
    }


def get_vat_from_transactions(company, from_date, to_date, doctype, vat_account):
    """
    Get VAT amounts from transactions.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        doctype (str): Transaction doctype (Sales Invoice or Purchase Invoice)
        vat_account (str): VAT account to filter
        
    Returns:
        dict: VAT transaction details
    """
    # Get invoices
    invoices = frappe.get_all(
        doctype,
        filters={
            "company": company,
            "posting_date": ["between", [from_date, to_date]],
            "docstatus": 1
        },
        fields=["name", "base_net_total", "base_total", "base_total_taxes_and_charges"]
    )
    
    total_vat = 0
    standard_rated = 0
    zero_rated = 0
    exempt = 0
    
    for invoice in invoices:
        # Get tax details
        taxes = frappe.get_all(
            f"{doctype} Item" if doctype == "Sales Invoice" else f"{doctype} Item",
            filters={"parent": invoice.name},
            fields=["item_code", "amount", "net_amount"]
        )
        
        # Simplified calculation - would need item-level VAT classification for accuracy
        invoice_vat = flt(invoice.base_total_taxes_and_charges)
        total_vat += invoice_vat
        
        # Categorize (simplified - would need item tax templates for accuracy)
        if invoice_vat > 0:
            standard_rated += flt(invoice.base_net_total)
        else:
            zero_rated += flt(invoice.base_net_total)
    
    return {
        "total_vat": flt(total_vat, 2),
        "standard_rated": flt(standard_rated, 2),
        "zero_rated": flt(zero_rated, 2),
        "exempt": flt(exempt, 2)
    }

