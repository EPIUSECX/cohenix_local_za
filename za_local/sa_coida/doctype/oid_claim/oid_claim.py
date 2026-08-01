from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

ALLOWED_TRANSITIONS = {
	"Submitted": {"Under Review", "Approved", "Rejected"},
	"Under Review": {"Approved", "Rejected"},
	"Approved": {"Paid"},
}
CLAIM_ADMIN_ROLES = ("HR Manager", "System Manager")


class OIDClaim(Document):
	def validate(self):
		self.validate_dates()
		self.validate_workplace_injury()
		self.validate_medical_reports()
		self.validate_saved_status_transition()

	def validate_dates(self):
		if getdate(self.injury_date) > getdate():
			frappe.throw(_("Injury Date cannot be in the future"))
		if self.claim_date and getdate(self.claim_date) < getdate(self.injury_date):
			frappe.throw(_("Claim Date cannot be before Injury Date"))
		if self.payment_date and getdate(self.payment_date) < getdate(self.claim_date or self.injury_date):
			frappe.throw(_("Payment Date cannot be before Claim Date"))

	def validate_workplace_injury(self):
		if not self.workplace_injury:
			return

		injury = frappe.get_doc("Workplace Injury", self.workplace_injury, check_permission=True)
		if injury.employee != self.employee:
			frappe.throw(_("The employee in the Workplace Injury does not match this claim"))
		if injury.company != self.company:
			frappe.throw(_("The company in the Workplace Injury does not match this claim"))

		for fieldname in ("injury_date", "injury_type", "injury_location", "injury_description"):
			if not self.get(fieldname):
				self.set(fieldname, injury.get(fieldname))

	def validate_medical_reports(self):
		for report in self.get("medical_reports") or []:
			if getdate(report.report_date) > getdate():
				frappe.throw(
					_("Row {0}: Medical Report Date cannot be in the future").format(report.idx)
				)
			if report.report_type == "Final Report" and self.claim_status not in {"Approved", "Paid"}:
				frappe.msgprint(
					_("A Final Medical Report has been recorded while the claim is not Approved or Paid."),
					alert=True,
					indicator="orange",
				)

	def validate_saved_status_transition(self):
		previous = self.get_doc_before_save()
		if not previous or previous.docstatus != 1 or previous.claim_status == self.claim_status:
			return
		frappe.only_for(CLAIM_ADMIN_ROLES)
		self._validate_transition(previous.claim_status, self.claim_status)
		self._validate_status_fields(self.claim_status, self.compensation_amount, self.payment_date)

	def on_submit(self):
		claim_date = self.claim_date or today()
		self.db_set(
			{"claim_status": "Submitted", "claim_date": claim_date},
			update_modified=False,
		)
		self.claim_status = "Submitted"
		self.claim_date = claim_date
		self._sync_workplace_injury_status()

	def on_update_after_submit(self):
		self._sync_workplace_injury_status()

	def on_cancel(self):
		self.db_set("claim_status", "Cancelled", update_modified=False)
		if self.workplace_injury:
			frappe.db.set_value("Workplace Injury", self.workplace_injury, "status", "Reported")

	@frappe.whitelist()
	def update_claim_status(self, status, compensation_amount=None, payment_date=None):
		"""Perform a role-gated, one-way claim workflow transition."""
		self.check_permission("write")
		frappe.only_for(CLAIM_ADMIN_ROLES)
		if self.docstatus != 1:
			frappe.throw(_("Submit the OID Claim before changing its workflow status."))

		status = (status or "").strip()
		self._validate_transition(self.claim_status, status)
		compensation_amount = (
			flt(compensation_amount) if compensation_amount is not None else flt(self.compensation_amount)
		)
		payment_date = payment_date or self.payment_date
		self._validate_status_fields(status, compensation_amount, payment_date)

		values = {"claim_status": status}
		if status == "Approved":
			values["compensation_amount"] = compensation_amount
		if status == "Paid":
			values["payment_date"] = getdate(payment_date)

		self.db_set(values, update_modified=True)
		self.update(values)
		self._sync_workplace_injury_status()
		return {"claim_status": status}

	@frappe.whitelist()
	def add_medical_report(self, report_date, medical_provider, report_type, diagnosis, attachment=None):
		"""Append a validated medical report to a submitted claim."""
		self.check_permission("write")
		if self.docstatus != 1:
			frappe.throw(_("Use the Medical Reports table directly while the OID Claim is in Draft."))

		self.append(
			"medical_reports",
			{
				"report_date": report_date,
				"medical_provider": medical_provider,
				"report_type": report_type,
				"diagnosis": diagnosis,
				"attachment": attachment,
			},
		)
		self.save()
		return len(self.medical_reports)

	def _validate_transition(self, current_status, new_status):
		if new_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
			frappe.throw(
				_("OID Claim status cannot change from {0} to {1}.").format(
					frappe.bold(current_status), frappe.bold(new_status or _("Not specified"))
				)
			)

	def _validate_status_fields(self, status, compensation_amount, payment_date):
		if status == "Approved" and flt(compensation_amount) <= 0:
			frappe.throw(_("Compensation Amount must be greater than zero when approving a claim."))
		if status == "Paid" and not payment_date:
			frappe.throw(_("Payment Date is required when marking a claim as Paid."))
		if payment_date and getdate(payment_date) < getdate(self.claim_date or self.injury_date):
			frappe.throw(_("Payment Date cannot be before Claim Date."))

	def _sync_workplace_injury_status(self):
		if not self.workplace_injury:
			return
		status_mapping = {
			"Submitted": "Investigating",
			"Under Review": "Investigating",
			"Approved": "Treating",
			"Rejected": "Closed",
			"Paid": "Closed",
		}
		if self.claim_status in status_mapping:
			frappe.db.set_value(
				"Workplace Injury",
				self.workplace_injury,
				"status",
				status_mapping[self.claim_status],
			)
