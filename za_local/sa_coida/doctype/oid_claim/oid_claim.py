import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

class OIDClaim(Document):
    def validate(self):
        self.validate_dates()
        self.validate_workplace_injury()
        
    def validate_dates(self):
        """Validate that injury date is not in the future"""
        if getdate(self.injury_date) > getdate():
            frappe.throw(_("Injury Date cannot be in the future"))
        
        if self.claim_date and getdate(self.claim_date) < getdate(self.injury_date):
            frappe.throw(_("Claim Date cannot be before Injury Date"))
            
        if self.payment_date and getdate(self.payment_date) < getdate(self.claim_date or self.injury_date):
            frappe.throw(_("Payment Date cannot be before Claim Date"))
    
    def validate_workplace_injury(self):
        """If workplace injury is linked, validate and fetch details"""
        if self.workplace_injury:
            injury = frappe.get_doc("Workplace Injury", self.workplace_injury)
            
            # Ensure the employee matches
            if injury.employee != self.employee:
                frappe.throw(_("The employee in the Workplace Injury does not match this claim"))
            
            # Fetch details from workplace injury if not already set
            if not self.injury_date:
                self.injury_date = injury.injury_date
            
            if not self.injury_type:
                self.injury_type = injury.injury_type
            
            if not self.injury_location:
                self.injury_location = injury.injury_location
            
            if not self.injury_description:
                self.injury_description = injury.injury_description
    
    def on_submit(self):
        """Update status when submitted"""
        if self.claim_status == "Pending":
            self.claim_status = "Submitted"
            self.claim_date = today()
    
    def on_update_after_submit(self):
        """Update linked workplace injury when claim status changes"""
        if self.workplace_injury:
            status_mapping = {
                "Submitted": "Investigating",
                "Under Review": "Investigating",
                "Approved": "Treating",
                "Rejected": "Closed",
                "Paid": "Closed"
            }
            
            if self.claim_status in status_mapping:
                injury_status = status_mapping[self.claim_status]
                frappe.db.set_value("Workplace Injury", self.workplace_injury, "status", injury_status)
    
    def on_cancel(self):
        """Reset status when cancelled"""
        self.claim_status = "Pending"
        self.claim_date = None
        
        # Update linked workplace injury
        if self.workplace_injury:
            frappe.db.set_value("Workplace Injury", self.workplace_injury, "status", "Reported")
    
    @frappe.whitelist()
    def update_claim_status(self, status, compensation_amount=None, payment_date=None):
        """Update claim status and related fields"""
        if status not in ["Pending", "Submitted", "Under Review", "Approved", "Rejected", "Paid"]:
            frappe.throw(_("Invalid claim status"))
        
        self.claim_status = status
        
        if status == "Approved" and compensation_amount:
            self.compensation_amount = compensation_amount
        
        if status == "Paid" and payment_date:
            self.payment_date = payment_date
        
        self.save()
        
        if self.docstatus == 1:  # If submitted
            self.on_update_after_submit()
        
        return self
