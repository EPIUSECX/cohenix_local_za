import frappe
from frappe.model.document import Document


class SARSPayrollCode(Document):
	def validate(self):
		self.code = (self.code or "").strip()
		self.description = (self.description or "").strip()
		if self.code:
			self.code = self.code.replace(" ", "")

		if self.print_sequence is None:
			self.print_sequence = 0

		if self.code and not self.name:
			self.name = self.code

