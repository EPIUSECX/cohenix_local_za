# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today
from za_local.utils.termination_utils import calculate_severance_tax
from za_local.utils.lump_sum_tax_utils import calculate_lump_sum_tax


class EmployeeFinalSettlement(Document):
	def validate(self):
		"""Validate final settlement"""
		self.calculate_settlement()
		
	def before_submit(self):
		"""Actions before submission"""
		if not self.total_gross:
			frappe.throw(_("Please calculate settlement before submitting"))
			
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
		
		# Calculate tax
		# Notice pay: Normal PAYE
		# Severance: First R500k tax-free, then lump sum rates
		# Leave: Lump sum rates
		
		severance_tax = calculate_severance_tax(severance) if severance > 0 else 0
		leave_tax = calculate_lump_sum_tax(leave, "termination") if leave > 0 else 0
		
		# Notice pay taxed at normal rates (simplified - use 25%)
		notice_tax = notice_pay * 0.25 if notice_pay > 0 else 0
		
		self.paye = severance_tax + leave_tax + notice_tax
		
		# UIF only on notice pay (capped)
		uif_threshold = 17712  # Monthly UIF threshold (R177,120 / 12)
		if notice_pay > 0:
			self.uif = min(notice_pay, uif_threshold) * 0.01  # 1% employee contribution
		else:
			self.uif = 0
		
		# Net settlement
		self.net_settlement = self.total_gross - self.paye - self.uif
		
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
			
		# Create salary slip
		# TODO: Implement salary slip creation
		frappe.msgprint(_("Final payslip generation - To be implemented"))
		
	@frappe.whitelist()
	def create_final_irp5(self):
		"""
		Create final IRP5 certificate for terminated employee.
		
		Returns:
			str: Name of created IRP5 certificate
		"""
		if self.docstatus != 1:
			frappe.throw(_("Settlement must be submitted first"))
			
		# TODO: Implement IRP5 creation
		frappe.msgprint(_("Final IRP5 creation - To be implemented"))
