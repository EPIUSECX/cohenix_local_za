import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class EmployeeETILog(Document):
	def validate(self):
		self.validate_salary_slip_uniqueness()
		if cint(self.is_qualifying_month) and not (1 <= cint(self.qualifying_month_number) <= 24):
			frappe.throw(
				_("A qualifying ETI month number must be between 1 and 24."),
				title=_("Invalid ETI Qualifying Month"),
			)
		if flt(self.eti_amount) < 0:
			frappe.throw(_("ETI Amount cannot be negative."))

	def validate_salary_slip_uniqueness(self):
		if not self.against_salary_slip:
			return
		existing = frappe.db.exists(
			"Employee ETI Log",
			{
				"against_salary_slip": self.against_salary_slip,
				"name": ["!=", self.name],
				"docstatus": ["<", 2],
			},
		)
		if existing:
			frappe.throw(
				_("Salary Slip {0} already has an active Employee ETI Log: {1}.").format(
					self.against_salary_slip,
					frappe.bold(existing),
				),
				title=_("Duplicate ETI Audit Log"),
			)
