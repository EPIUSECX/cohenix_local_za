import frappe
from frappe.model.document import Document


class VATVendorType(Document):
    def validate(self):
        self.validate_vendor_type()

    def validate_vendor_type(self):
        """Validate vendor type and set default values."""
        if self.vendor_type == "Standard":
            if not self.turnover_threshold:
                self.turnover_threshold = 2300000
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"

        elif self.vendor_type == "Micro Business":
            if not self.turnover_threshold:
                self.turnover_threshold = 2300000
            if not self.filing_frequency:
                self.filing_frequency = "Quarterly"

        elif self.vendor_type == "Small Business":
            if not self.turnover_threshold:
                self.turnover_threshold = 2300000
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"

        elif self.vendor_type == "Voluntary":
            if not self.turnover_threshold:
                self.turnover_threshold = 120000
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"

        elif self.vendor_type == "Foreign Supplier":
            if not self.turnover_threshold:
                self.turnover_threshold = 2300000
            if not self.filing_frequency:
                self.filing_frequency = "Bi-Monthly"

    def on_update(self):
        """Update all VAT settings docs that use this vendor type."""
        for settings_name in frappe.get_all(
            "South Africa VAT Settings",
            filters={"vat_vendor_type": self.name},
            pluck="name",
        ):
            vat_settings = frappe.get_doc("South Africa VAT Settings", settings_name)
            if vat_settings.vat_filing_frequency != self.filing_frequency:
                vat_settings.vat_filing_frequency = self.filing_frequency
                vat_settings.flags.ignore_permissions = True
                vat_settings.save()
