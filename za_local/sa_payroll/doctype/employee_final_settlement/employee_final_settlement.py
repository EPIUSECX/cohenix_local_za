# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

from za_local.utils.tax_utils import calculate_south_african_tax, calculate_uif_contribution
from za_local.utils.termination_utils import calculate_severance_tax


class EmployeeFinalSettlement(Document):
	def validate(self):
		"""Validate final settlement"""
		self.calculate_settlement()

	def before_submit(self):
		"""Actions before submission"""
		if not self.total_gross:
			frappe.throw(_("Please calculate settlement before submitting"))
		self.validate_tax_directive()

	def on_submit(self):
		"""Actions on submission"""
		frappe.msgprint(_("Final Settlement submitted. Generate payslip to process payment."))

	def calculate_settlement(self):
		"""
		Calculate complete final settlement.

		Components:
		- Notice pay (if not worked)
		- Severance pay (if applicable)
		- Leave payout (untaken annual leave)
		- Pro-rata bonus (if applicable)

		Deductions:
		- PAYE (special lump sum rates)
		- UIF (if applicable)
		"""
		# Total gross components
		notice_pay = flt(self.notice_pay)
		severance = flt(self.severance_pay)
		leave = flt(self.leave_payout)
		bonus = flt(self.bonus_prorata)

		self.total_gross = notice_pay + severance + leave + bonus

		severance_tax = self.get_directive_tax_amount()
		if not severance_tax and severance > 0:
			severance_tax = calculate_severance_tax(
				severance,
				date_value=self.separation_date,
				previous_lump_sums=self.previous_lump_sum_benefits,
			)

		normal_taxable = notice_pay + leave + bonus
		normal_tax = self.calculate_normal_termination_tax(normal_taxable)

		self.paye = flt(severance_tax) + flt(normal_tax)

		# UIF applies to normal termination remuneration, not severance benefits.
		self.uif = calculate_uif_contribution(normal_taxable)[0] if normal_taxable > 0 else 0

		# Net settlement
		self.net_settlement = self.total_gross - self.paye - self.uif

	def validate_tax_directive(self):
		if flt(self.severance_pay) <= 0:
			return
		if not self.tax_directive:
			frappe.throw(
				_("A SARS tax directive is required before submitting a settlement with a severance benefit."),
				title=_("Tax Directive Required"),
			)
		directive = frappe.get_doc("Tax Directive", self.tax_directive)
		if directive.employee != self.employee:
			frappe.throw(_("Tax Directive must belong to employee {0}.").format(self.employee))
		if directive.docstatus != 1 or directive.status != "Active":
			frappe.throw(_("Tax Directive {0} must be submitted and Active.").format(directive.directive_number))

	def get_directive_tax_amount(self):
		if not self.tax_directive:
			return 0
		directive = frappe.get_doc("Tax Directive", self.tax_directive)
		if directive.directive_type in {"Fixed Amount", "Severance / Lump Sum"}:
			return flt(directive.fixed_amount)
		return 0

	def calculate_normal_termination_tax(self, amount):
		if flt(amount) <= 0:
			return 0
		annual_base = self.get_employee_annual_base()
		base_tax = calculate_south_african_tax(annual_base)
		total_tax = calculate_south_african_tax(annual_base + flt(amount))
		return flt(max(0, total_tax - base_tax), 2)

	def get_employee_annual_base(self):
		assignment = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1, "from_date": ["<=", self.separation_date]},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		if not assignment:
			return 0
		return flt(assignment[0].base) * 12

	@frappe.whitelist()
	def generate_final_payslip(self):
		"""
		Generate final salary slip for the settlement.

		Returns:
			str: Name of created salary slip
		"""
		if self.docstatus != 1:
			frappe.throw(_("Settlement must be submitted first"))

		# Check if payslip already exists
		existing = frappe.db.exists("Salary Slip", {"employee": self.employee, "remarks": f"Final Settlement: {self.name}"})
		if existing:
			frappe.throw(_("Salary Slip already generated: {0}").format(existing))

		self.validate_tax_directive()
		slip = frappe.new_doc("Salary Slip")
		slip.employee = self.employee
		slip.employee_name = self.employee_name
		slip.company = frappe.db.get_value("Employee", self.employee, "company")
		slip.posting_date = self.separation_date
		slip.start_date = getdate(self.separation_date).replace(day=1)
		slip.end_date = self.separation_date
		slip.payroll_frequency = "Monthly"
		slip.remarks = f"Final Settlement: {self.name}"

		for component, amount in (
			("Notice Pay", self.notice_pay),
			("Severance Benefit", self.severance_pay),
			("Leave Payout", self.leave_payout),
			("Performance Bonus", self.bonus_prorata),
		):
			if flt(amount):
				slip.append("earnings", {"salary_component": component, "amount": flt(amount)})

		for component, amount in (("PAYE", self.paye), ("UIF Employee Contribution", self.uif)):
			if flt(amount):
				slip.append("deductions", {"salary_component": component, "amount": flt(amount)})

		slip.gross_pay = self.total_gross
		slip.total_deduction = self.paye + self.uif
		slip.net_pay = self.net_settlement
		slip.flags.ignore_permissions = True
		slip.flags.ignore_mandatory = True
		slip.insert(ignore_permissions=True, ignore_mandatory=True)
		return slip.name

	@frappe.whitelist()
	def create_final_irp5(self):
		"""
		Create final IRP5 certificate for terminated employee.

		Returns:
			str: Name of created IRP5 certificate
		"""
		if self.docstatus != 1:
			frappe.throw(_("Settlement must be submitted first"))

		frappe.throw(
			_(
				"Automatic final IRP5 creation from settlement is not available yet. "
				"Generate the IRP5/IT3(a) certificate from the EMP501 process after the final payroll is posted."
			),
			title=_("Use EMP501 Certificate Flow"),
		)
