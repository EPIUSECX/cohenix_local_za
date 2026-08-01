import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class EmployeePrivateBenefit(Document):
	def validate(self):
		if self.effective_from and self.to and getdate(self.to) < getdate(self.effective_from):
			frappe.throw(_("To Date cannot be before Effective From Date."))

		if (flt(self.private_medical_aid) > 0 or flt(self.annuity_amount) > 0) and not self.effective_from:
			frappe.throw(_("Effective From Date is required for an active private benefit."))

		if flt(self.medical_aid_dependant) < 0:
			frappe.throw(_("Medical Aid Dependants cannot be negative."))

		self.validate_no_overlapping_active_period()

	def validate_no_overlapping_active_period(self):
		"""Keep one authoritative private-benefit record active per employee/date."""
		if self.disable or not self.employee or not self.effective_from:
			return

		filters = [
			["employee", "=", self.employee],
			["disable", "=", 0],
			["name", "!=", self.name or ""],
		]
		if self.to:
			filters.append(["effective_from", "<=", self.to])

		overlaps = frappe.get_all(
			"Employee Private Benefit",
			filters=filters,
			or_filters=[["to", "is", "not set"], ["to", ">=", self.effective_from]],
			fields=["name", "effective_from", "to"],
			order_by="effective_from desc",
			limit=1,
		)
		if overlaps:
			overlap = overlaps[0]
			frappe.throw(
				_("Employee {0} already has an active private benefit period that overlaps this record: {1}.").format(
					frappe.bold(self.employee),
					frappe.utils.get_link_to_form("Employee Private Benefit", overlap.name),
				),
				title=_("Overlapping Private Benefit Period"),
			)
