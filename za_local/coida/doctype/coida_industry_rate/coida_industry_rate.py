# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class COIDAIndustryRate(Document):
    def validate(self):
        self.validate_rate()
        
    def validate_rate(self):
        """Validate that the rate is within acceptable range"""
        if self.rate < 0:
            frappe.throw("COIDA Industry Rate cannot be negative")
        
        if self.rate > 10:
            # Rates are typically less than 10%, so warn if higher
            frappe.msgprint(
                "COIDA Industry Rate is unusually high (>10%). Please verify this is correct.",
                indicator="orange",
                alert=True
            )
