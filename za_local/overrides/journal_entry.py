"""
South African Journal Entry Hooks

This module provides hooks for Journal Entry to handle payroll-related
journal entry tracking and cleanup.
"""

import frappe


def on_trash(doc, event):
    """
    Handle journal entry trash event.
    
    Updates payroll entry detail flags when draft journal entries are deleted.
    
    Args:
        doc: Journal Entry document
        event: Event name
    """
    if doc.docstatus == 0:
        update_employee_journal_entry_flags(doc)


def on_cancel(doc, event):
    """
    Handle journal entry cancel event.
    
    Updates payroll entry detail flags when journal entries are cancelled.
    
    Args:
        doc: Journal Entry document
        event: Event name
    """
    update_employee_journal_entry_flags(doc)


def update_employee_journal_entry_flags(doc):
    """
    Update Payroll Employee Detail flags when journal entries are removed.
    
    This ensures that bank entries and company contribution entries can be
    regenerated if the original journal entry is deleted or cancelled.
    
    Args:
        doc: Journal Entry document
    """
    for row in doc.accounts:
        # Check if this is a payroll-related entry
        if (row.reference_type == "Payroll Entry" and 
            row.reference_name and 
            row.party_type == "Employee" and 
            row.party):
            
            # Update bank entry flag
            if row.get("za_is_payroll_entry"):
                frappe.db.set_value(
                    "Payroll Employee Detail",
                    {
                        "parent": row.reference_name,
                        "employee": row.party
                    },
                    "za_is_bank_entry_created",
                    0
                )
            
            # Update company contribution flag
            elif row.get("za_is_company_contribution"):
                frappe.db.set_value(
                    "Payroll Employee Detail",
                    {
                        "parent": row.reference_name,
                        "employee": row.party
                    },
                    "za_is_company_contribution_created",
                    0
                )

