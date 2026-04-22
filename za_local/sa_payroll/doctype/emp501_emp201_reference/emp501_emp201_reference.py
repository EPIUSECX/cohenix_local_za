import frappe
from frappe.model.document import Document

class EMP501EMP201Reference(Document):
    def validate(self):
        if self.emp201_submission:
            # Fetch values from EMP201 Submission
            emp201 = frappe.get_doc("EMP201 Submission", self.emp201_submission)
            self.submission_date = emp201.submission_date
            self.paye = emp201.paye_payable
            self.sdl = emp201.sdl_payable
            self.uif = emp201.uif_payable
            self.eti = emp201.eti_utilized
