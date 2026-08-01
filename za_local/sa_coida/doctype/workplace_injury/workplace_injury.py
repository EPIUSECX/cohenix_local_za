from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, getdate

from za_local.utils.hrms_detection import is_hrms_installed


class WorkplaceInjury(Document):
	def validate(self):
		self.validate_dates()
		if self.requires_leave:
			if not is_hrms_installed():
				frappe.throw(_("HRMS is required to create leave for a workplace injury."))
			if not self.leave_days:
				self.calculate_leave_days()

	def validate_dates(self):
		if getdate(self.injury_date) > getdate():
			frappe.throw(_("Injury Date cannot be in the future"))
		if self.expected_recovery_date and getdate(self.expected_recovery_date) < getdate(self.injury_date):
			frappe.throw(_("Expected Recovery Date cannot be before Injury Date"))

	def calculate_leave_days(self):
		self.leave_days = (
			date_diff(self.expected_recovery_date, self.injury_date) + 1
			if self.expected_recovery_date
			else 7
		)

	def on_submit(self):
		"""Create every linked statutory document requested on the injury."""
		if self.requires_leave:
			self.create_leave_application()
		if self.requires_claim:
			self.create_oid_claim()

	def create_leave_application(self):
		"""Create and submit an approved leave application or fail the injury transaction."""
		if self.leave_application:
			return self.leave_application
		if not is_hrms_installed() or not frappe.db.table_exists("Leave Application"):
			frappe.throw(_("Leave Application is unavailable. Install and configure HRMS first."))

		leave_type = frappe.db.get_value("Leave Type", {"name": ["like", "%Injury%"]}, "name")
		if not leave_type and frappe.db.exists("Leave Type", "Sick Leave"):
			leave_type = "Sick Leave"
		if not leave_type:
			frappe.throw(
				_("Configure an Injury leave type or a Sick Leave type before creating injury leave.")
			)

		leave_application = frappe.new_doc("Leave Application")
		leave_application.update(
			{
				"employee": self.employee,
				"leave_type": leave_type,
				"from_date": self.injury_date,
				"to_date": add_days(self.injury_date, cint(self.leave_days) - 1),
				"description": _("Workplace Injury: {0}").format(self.name),
				"status": "Approved",
			}
		)
		leave_application.insert()
		leave_application.submit()
		self.db_set("leave_application", leave_application.name, update_modified=False)
		frappe.msgprint(
			_("Leave Application {0} created").format(frappe.bold(leave_application.name)),
			alert=True,
			indicator="green",
		)
		return leave_application.name

	def create_oid_claim(self):
		"""Create a draft OID claim or fail the injury transaction."""
		if self.oid_claim:
			return self.oid_claim

		oid_claim = frappe.new_doc("OID Claim")
		oid_claim.update(
			{
				"workplace_injury": self.name,
				"employee": self.employee,
				"company": self.company,
				"injury_date": self.injury_date,
				"injury_type": self.injury_type,
				"injury_location": self.injury_location,
				"injury_description": self.injury_description,
			}
		)
		oid_claim.insert()
		self.db_set("oid_claim", oid_claim.name, update_modified=False)
		frappe.msgprint(
			_("OID Claim {0} created").format(frappe.bold(oid_claim.name)),
			alert=True,
			indicator="green",
		)
		return oid_claim.name

	@frappe.whitelist()
	def create_oid_claim_after_submit(self):
		"""Create a claim requested after the injury was submitted."""
		self.check_permission("write")
		self._require_submitted()
		if self.oid_claim:
			return self.oid_claim
		self.db_set("requires_claim", 1, update_modified=False)
		return self.create_oid_claim()

	@frappe.whitelist()
	def create_leave_application_after_submit(self, leave_days=None):
		"""Create injury leave requested after submission."""
		self.check_permission("write")
		self._require_submitted()
		if self.leave_application:
			return self.leave_application

		leave_days = cint(leave_days or self.leave_days)
		if leave_days <= 0:
			frappe.throw(_("Leave Days must be greater than zero."))
		self.db_set(
			{"requires_leave": 1, "leave_days": leave_days},
			update_modified=False,
		)
		self.leave_days = leave_days
		return self.create_leave_application()

	def _require_submitted(self):
		if self.docstatus != 1:
			frappe.throw(_("This action is available only for a submitted Workplace Injury."))

	def on_cancel(self):
		"""Reverse linked drafts/submissions or fail cancellation."""
		if self.leave_application and is_hrms_installed() and frappe.db.exists(
			"Leave Application", self.leave_application
		):
			leave_application = frappe.get_doc("Leave Application", self.leave_application)
			if leave_application.docstatus == 1:
				leave_application.cancel()

		if self.oid_claim and frappe.db.exists("OID Claim", self.oid_claim):
			oid_claim = frappe.get_doc("OID Claim", self.oid_claim)
			if oid_claim.docstatus == 0:
				oid_claim.delete()
			elif oid_claim.docstatus == 1:
				oid_claim.cancel()
