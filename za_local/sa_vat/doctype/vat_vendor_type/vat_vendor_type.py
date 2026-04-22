import frappe
from frappe.model.document import Document

class VATVendorType(Document):
    def validate(self):
        self.validate_vendor_type()
        
    def validate_vendor_type(self):
        """Validate vendor type and set default values"""
        # Set default values based on vendor type
        if self.vendor_type == "Standard":
            # Standard VAT vendor
            if not self.turnover_threshold:
                self.turnover_threshold = 1000000  # 1 million ZAR
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"
                
        elif self.vendor_type == "Micro Business":
            # Micro business
            if not self.turnover_threshold:
                self.turnover_threshold = 1000000  # 1 million ZAR
            if not self.filing_frequency:
                self.filing_frequency = "Quarterly"
                
        elif self.vendor_type == "Small Business":
            # Small business
            if not self.turnover_threshold:
                self.turnover_threshold = 6500000  # 6.5 million ZAR
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"
                
        elif self.vendor_type == "Voluntary":
            # Voluntary VAT vendor
            if not self.turnover_threshold:
                self.turnover_threshold = 50000  # 50,000 ZAR
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"
                
        elif self.vendor_type == "Foreign Supplier":
            # Foreign supplier of electronic services
            if not self.turnover_threshold:
                self.turnover_threshold = 1000000  # 1 million ZAR
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"
                
    def on_update(self):
        """Update VAT settings if this is the default vendor type"""
        # Check if this is the vendor type used in VAT settings
        if frappe.db.exists("South Africa VAT Settings", {"vat_vendor_type": self.name}):
            vat_settings = frappe.get_doc("South Africa VAT Settings")
            
            # Update filing frequency if it's changed
            if vat_settings.vat_filing_frequency != self.filing_frequency:
                vat_settings.vat_filing_frequency = self.filing_frequency
                vat_settings.save()
                frappe.msgprint(f"Updated VAT filing frequency to {self.filing_frequency} in VAT Settings")
