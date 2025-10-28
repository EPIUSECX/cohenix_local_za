# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, date_diff

class WorkplaceInjury(Document):
    def validate(self):
        self.validate_dates()
        if self.requires_leave and not self.leave_days:
            self.calculate_leave_days()
    
    def validate_dates(self):
        """Validate that injury date is not in the future"""
        if getdate(self.injury_date) > getdate():
            frappe.throw(_("Injury Date cannot be in the future"))
        
        if self.expected_recovery_date and getdate(self.expected_recovery_date) < getdate(self.injury_date):
            frappe.throw(_("Expected Recovery Date cannot be before Injury Date"))
    
    def calculate_leave_days(self):
        """Calculate leave days based on expected recovery date"""
        if self.expected_recovery_date:
            self.leave_days = date_diff(self.expected_recovery_date, self.injury_date) + 1
        else:
            # Default to 7 days if no recovery date is specified
            self.leave_days = 7
    
    def on_submit(self):
        """Create leave application and OID claim if required"""
        if self.requires_leave:
            self.create_leave_application()
        
        if self.requires_claim:
            self.create_oid_claim()
    
    def create_leave_application(self):
        """Create a leave application for the injured employee"""
        if self.leave_application:
            return
        
        # Check if employee has a leave type for injury
        leave_type = frappe.db.get_value("Leave Type", {"name": ["like", "%Injury%"]}, "name")
        if not leave_type:
            leave_type = "Sick Leave"  # Default to sick leave if no injury leave type exists
        
        leave_application = frappe.new_doc("Leave Application")
        leave_application.employee = self.employee
        leave_application.leave_type = leave_type
        leave_application.from_date = self.injury_date
        
        # Calculate to_date based on leave_days
        to_date = frappe.utils.add_days(self.injury_date, self.leave_days - 1)
        leave_application.to_date = to_date
        
        leave_application.description = f"Workplace Injury: {self.name}"
        leave_application.status = "Approved"  # Auto-approve for workplace injuries
        
        try:
            leave_application.insert()
            leave_application.submit()
            self.leave_application = leave_application.name
            self.db_update()
            frappe.msgprint(_("Leave Application {0} created").format(
                frappe.bold(leave_application.name)))
        except Exception as e:
            frappe.msgprint(_("Could not create Leave Application: {0}").format(str(e)))
    
    def create_oid_claim(self):
        """Create an OID claim for the workplace injury"""
        if self.oid_claim:
            return
        
        oid_claim = frappe.new_doc("OID Claim")
        oid_claim.workplace_injury = self.name
        oid_claim.employee = self.employee
        oid_claim.injury_date = self.injury_date
        oid_claim.injury_type = self.injury_type
        oid_claim.injury_description = self.injury_description
        
        try:
            oid_claim.insert()
            self.oid_claim = oid_claim.name
            self.db_update()
            frappe.msgprint(_("OID Claim {0} created").format(
                frappe.bold(oid_claim.name)))
        except Exception as e:
            frappe.msgprint(_("Could not create OID Claim: {0}").format(str(e)))
    
    def on_cancel(self):
        """Cancel linked documents when injury is cancelled"""
        if self.leave_application:
            leave_app = frappe.get_doc("Leave Application", self.leave_application)
            if leave_app.docstatus == 1:  # If submitted
                leave_app.cancel()
                frappe.msgprint(_("Leave Application {0} cancelled").format(
                    frappe.bold(self.leave_application)))
        
        if self.oid_claim:
            oid_claim = frappe.get_doc("OID Claim", self.oid_claim)
            if oid_claim.docstatus == 0:  # If draft
                oid_claim.delete()
                frappe.msgprint(_("OID Claim {0} deleted").format(
                    frappe.bold(self.oid_claim)))
            elif oid_claim.docstatus == 1:  # If submitted
                oid_claim.cancel()
                frappe.msgprint(_("OID Claim {0} cancelled").format(
                    frappe.bold(self.oid_claim)))
