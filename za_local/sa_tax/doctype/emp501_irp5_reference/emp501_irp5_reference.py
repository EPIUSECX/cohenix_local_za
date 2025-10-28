# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EMP501IRP5Reference(Document):
    def validate(self):
        if self.irp5_certificate:
            # Fetch values from IRP5 Certificate
            irp5 = frappe.get_doc("IRP5 Certificate", self.irp5_certificate)
            self.employee = irp5.employee
            self.employee_name = irp5.employee_name
            self.status = irp5.status
