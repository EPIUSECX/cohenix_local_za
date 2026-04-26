import frappe
from frappe.model.document import Document
from frappe.utils import flt


class COIDAIndustryRate(Document):
    def validate(self):
        self.validate_rate()

    def validate_rate(self):
        """Validate that the rate is within acceptable range"""
        rate = flt(self.assessment_rate)
        if rate < 0:
            frappe.throw("COIDA Industry Rate cannot be negative")

        if rate > 10:
            # Rates are typically less than 10%, so warn if higher
            frappe.msgprint(
                "COIDA Industry Rate is unusually high (>10%). Please verify this is correct.",
                indicator="orange",
                alert=True
            )
