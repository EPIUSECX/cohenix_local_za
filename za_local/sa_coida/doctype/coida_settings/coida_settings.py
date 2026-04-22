import frappe
from frappe.model.document import Document

class COIDASettings(Document):
    def validate(self):
        self.validate_industry_rates()
    
    def validate_industry_rates(self):
        """Ensure industry rates are valid percentages"""
        for rate in self.industry_rates:
            if rate.assessment_rate <= 0 or rate.assessment_rate > 100:
                frappe.throw(f"Assessment rate for {rate.industry_class} must be between 0 and 100%")
