# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from za_local.utils.integrations.eft_file_generator import (
	build_payment_batch_snapshot,
	normalize_bank_format,
	validate_payment_batch_header,
)


class PayrollPaymentBatch(Document):
	def validate(self):
		self._set_company_from_payroll_entry()
		self.bank_format = normalize_bank_format(self.bank_format)
		validate_payment_batch_header(self)

	def before_submit(self):
		self._validate_no_submitted_duplicate()
		snapshot = build_payment_batch_snapshot(self)
		self.total_employees = len(snapshot.recipients)
		self.total_amount = snapshot.total_amount
		self.eft_source_hash = snapshot.source_hash

	def _set_company_from_payroll_entry(self):
		if not self.payroll_entry:
			frappe.throw(_("Payroll Entry is required."))
		company = frappe.db.get_value("Payroll Entry", self.payroll_entry, "company")
		if not company:
			frappe.throw(
				_("Payroll Entry {0} does not exist.").format(frappe.bold(self.payroll_entry))
			)
		if self.company and self.company != company:
			frappe.throw(
				_("Company must match Payroll Entry company {0}.").format(frappe.bold(company))
			)
		self.company = company

	def _validate_no_submitted_duplicate(self):
		duplicate = frappe.db.get_value(
			"Payroll Payment Batch",
			{
				"payroll_entry": self.payroll_entry,
				"docstatus": 1,
				"name": ["!=", self.name],
			},
			"name",
		)
		if duplicate:
			frappe.throw(
				_("Payroll Entry {0} is already covered by submitted Payroll Payment Batch {1}.").format(
					frappe.bold(self.payroll_entry), frappe.bold(duplicate)
				),
				title=_("Duplicate Payroll Payment Batch"),
			)
