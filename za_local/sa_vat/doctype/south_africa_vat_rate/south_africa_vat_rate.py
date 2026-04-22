import frappe
from frappe.model.document import Document

class SouthAfricaVATRate(Document):
    def validate(self):
        self.validate_rate_flags()
        
    def validate_rate_flags(self):
        """Validate that rate flags are consistent"""
        # Standard rate cannot be zero-rated or exempt
        if self.is_standard_rate:
            if self.is_zero_rated:
                self.is_zero_rated = 0
                frappe.msgprint("Standard rate cannot be zero-rated. Zero-rated flag has been reset.", alert=True)
                
            if self.is_exempt:
                self.is_exempt = 0
                frappe.msgprint("Standard rate cannot be exempt. Exempt flag has been reset.", alert=True)
                
        # Zero-rated items must have 0% rate
        if self.is_zero_rated and self.rate != 0:
            self.rate = 0
            frappe.msgprint("Zero-rated items must have 0% rate. Rate has been set to 0%.", alert=True)
            
        # Exempt items must have 0% rate
        if self.is_exempt and self.rate != 0:
            self.rate = 0
            frappe.msgprint("Exempt items must have 0% rate. Rate has been set to 0%.", alert=True)
            
        # Zero-rated and exempt are mutually exclusive
        if self.is_zero_rated and self.is_exempt:
            self.is_exempt = 0
            frappe.msgprint("An item cannot be both zero-rated and exempt. Exempt flag has been reset.", alert=True)
