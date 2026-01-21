"""
South African Journal Entry Hooks

This module provides hooks for Journal Entry to handle payroll-related
journal entry tracking and cleanup.
"""

import frappe
from frappe import _


@frappe.whitelist()
def force_delete_all_cancelled_payroll_journal_entries():
    """
    Force delete ALL cancelled payroll-related Journal Entries.
    
    WARNING: This bypasses standard ERPNext audit trail protection.
    Only use for test data cleanup during development.
    
    Returns:
        dict: List of deleted Journal Entries
    """
    # Find all cancelled payroll Journal Entries
    jes = frappe.db.sql("""
        SELECT DISTINCT je.name, je.docstatus, je.posting_date
        FROM `tabJournal Entry` je
        INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
        WHERE jea.reference_type = 'Payroll Entry'
        AND je.docstatus = 2
        ORDER BY je.name
    """, as_dict=True)
    
    deleted = []
    failed = []
    
    for je in jes:
        try:
            je_doc = frappe.get_doc("Journal Entry", je.name)
            
            # Update flags first
            update_employee_journal_entry_flags(je_doc)
            
            # Change docstatus to 0, then delete
            frappe.db.set_value("Journal Entry", je.name, "docstatus", 0)
            frappe.delete_doc("Journal Entry", je.name, force=1)
            deleted.append(je.name)
        except Exception as e:
            failed.append({"name": je.name, "error": str(e)})
    
    frappe.db.commit()
    
    return {
        "deleted": deleted,
        "failed": failed,
        "message": _("Deleted {0} cancelled payroll Journal Entries").format(len(deleted))
    }


@frappe.whitelist()
def force_delete_cancelled_payroll_journal_entry(journal_entry_name):
    """
    Force delete a cancelled payroll-related Journal Entry.
    
    WARNING: This bypasses standard ERPNext audit trail protection.
    Only use for test data cleanup during development.
    
    Args:
        journal_entry_name: Name of the Journal Entry to delete
        
    Returns:
        dict: Success message
    """
    if not journal_entry_name:
        frappe.throw(_("Journal Entry name is required"))
    
    je = frappe.get_doc("Journal Entry", journal_entry_name)
    
    # Verify it's a payroll-related entry
    is_payroll_entry = False
    if je.accounts:
        for row in je.accounts:
            if (row.reference_type == "Payroll Entry" and 
                row.reference_name and 
                row.party_type == "Employee" and 
                row.party):
                is_payroll_entry = True
                break
    
    if not is_payroll_entry:
        frappe.throw(_("This Journal Entry is not payroll-related. Cannot force delete."))
    
    if je.docstatus != 2:
        frappe.throw(_("Journal Entry must be cancelled (docstatus=2) to use force delete."))
    
    # Update flags before deletion
    update_employee_journal_entry_flags(je)
    
    # Force delete by setting docstatus to 0 first, then delete
    # This bypasses the standard validation
    frappe.db.set_value("Journal Entry", journal_entry_name, "docstatus", 0)
    frappe.delete_doc("Journal Entry", journal_entry_name, force=1)
    
    return {
        "message": _("Cancelled payroll Journal Entry {0} deleted successfully").format(journal_entry_name)
    }


def on_trash(doc, event):
    """
    Handle journal entry trash event.
    
    Updates payroll entry detail flags when journal entries are deleted.
    Allows deletion of cancelled payroll-related entries for testing/cleanup.
    
    Args:
        doc: Journal Entry document
        event: Event name
    """
    # Update flags for both draft and cancelled payroll entries
    if doc.docstatus in [0, 2]:
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
                    0,
                    update_modified=False,
                    ignore_permissions=True,  # Permission already checked on parent Journal Entry
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
                    0,
                    update_modified=False,
                    ignore_permissions=True,  # Permission already checked on parent Journal Entry
                )

