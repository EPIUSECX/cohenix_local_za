"""
South African Journal Entry Hooks

This module provides hooks for Journal Entry to handle payroll-related
journal entry tracking and cleanup.
"""

import frappe
from frappe import _

DESTRUCTIVE_CLEANUP_CONFIG_KEY = "allow_za_local_destructive_payroll_cleanup"


def _require_cleanup_access():
    """Allow destructive cleanup only when a System Manager explicitly enables it."""
    frappe.only_for("System Manager")

    if frappe.flags.in_test:
        return

    developer_mode = bool(frappe.conf.get("developer_mode"))
    cleanup_enabled = bool(frappe.conf.get(DESTRUCTIVE_CLEANUP_CONFIG_KEY))
    if developer_mode and cleanup_enabled:
        return

    frappe.throw(
        _(
            "Payroll journal entry force deletion is only available to System Managers "
            "when developer mode and the explicit destructive-cleanup site setting are enabled."
        ),
        title=_("Restricted Operation"),
    )


@frappe.whitelist(methods=["POST"])
def force_delete_all_cancelled_payroll_journal_entries():
    """
    Force delete ALL cancelled payroll-related Journal Entries.

    WARNING: This bypasses standard ERPNext audit trail protection.
    Only use for test data cleanup during development.

    Returns:
        dict: List of deleted Journal Entries
    """
    _require_cleanup_access()

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

    for index, je in enumerate(jes):
        savepoint = f"za_payroll_je_cleanup_{index}"
        frappe.db.savepoint(savepoint)
        try:
            je_doc = frappe.get_doc("Journal Entry", je.name)
            _delete_cancelled_payroll_journal_entry(je_doc)
            frappe.db.release_savepoint(savepoint)
            deleted.append(je.name)
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            frappe.db.release_savepoint(savepoint)
            frappe.log_error(
                title=f"Payroll Journal Entry cleanup failed: {je.name}",
                message=frappe.get_traceback(),
                reference_doctype="Journal Entry",
                reference_name=je.name,
            )
            failed.append(
                {
                    "name": je.name,
                    "error": _("Deletion failed. Review the Error Log for details."),
                }
            )

    return {
        "deleted": deleted,
        "failed": failed,
        "message": _("Deleted {0} cancelled payroll Journal Entries").format(len(deleted))
    }


@frappe.whitelist(methods=["POST"])
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
    _require_cleanup_access()

    if not journal_entry_name:
        frappe.throw(_("Journal Entry name is required"))

    savepoint = "za_payroll_je_cleanup_single"
    frappe.db.savepoint(savepoint)
    try:
        je = frappe.get_doc("Journal Entry", journal_entry_name)
        _delete_cancelled_payroll_journal_entry(je)
        frappe.db.release_savepoint(savepoint)
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        frappe.db.release_savepoint(savepoint)
        frappe.log_error(
            title=f"Payroll Journal Entry cleanup failed: {journal_entry_name}",
            message=frappe.get_traceback(),
            reference_doctype="Journal Entry",
            reference_name=journal_entry_name,
        )
        raise

    return {
        "message": _("Cancelled payroll Journal Entry {0} deleted successfully").format(journal_entry_name)
    }


def _delete_cancelled_payroll_journal_entry(je):
    if not any(
        row.reference_type == "Payroll Entry"
        and row.reference_name
        and row.party_type == "Employee"
        and row.party
        for row in je.accounts
    ):
        frappe.throw(_("This Journal Entry is not payroll-related. Cannot force delete."))

    if je.docstatus != 2:
        frappe.throw(_("Journal Entry must be cancelled (docstatus=2) to use force delete."))

    update_employee_journal_entry_flags(je)
    frappe.db.set_value("Journal Entry", je.name, "docstatus", 0)
    frappe.delete_doc("Journal Entry", je.name, force=1)


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
