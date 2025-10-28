# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today

class OIDMedicalReport(Document):
    def validate(self):
        """Validate medical report details"""
        # Check report date is not in the future
        if getdate(self.report_date) > getdate(today()):
            frappe.throw("Report Date cannot be in the future")
            
        # Check if this is a final report when parent is an OID Claim
        if self.parent_doctype == "OID Claim" and self.report_type == "Final Report":
            # Get the parent OID Claim
            parent = frappe.get_doc("OID Claim", self.parent)
            
            # If claim is not in Approved or Paid status, prompt a message
            if parent.claim_status not in ["Approved", "Paid"]:
                frappe.msgprint(
                    "You're marking this as a Final Report. Consider updating the claim status to Approved.",
                    indicator="orange",
                    alert=True
                )
