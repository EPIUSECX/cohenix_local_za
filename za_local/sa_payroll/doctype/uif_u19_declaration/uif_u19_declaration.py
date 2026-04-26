# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class UifU19Declaration(Document):
	def validate(self):
		"""Validate UIF U19 declaration"""
		self.calculate_total_contributions()

	def calculate_total_contributions(self):
		"""
		Calculate total UIF contributions for the employee.

		Queries all salary slips to get total UIF paid.
		"""
		if not self.employee:
			return

		# Get total employee UIF from salary slips using SARS code mapping.
		uif_total = frappe.db.sql("""
			SELECT SUM(sd.amount)
			FROM `tabSalary Detail` sd
			INNER JOIN `tabSalary Slip` ss ON ss.name = sd.parent
			INNER JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
			WHERE ss.employee = %(employee)s
				AND ss.docstatus = 1
				AND sc.za_sars_payroll_code = '4141'
				AND sd.parentfield = 'deductions'
		""", {"employee": self.employee})

		if uif_total and uif_total[0][0]:
			self.total_uif_contributions = flt(uif_total[0][0])
		else:
			self.total_uif_contributions = 0

	@frappe.whitelist()
	def generate_u19_form(self):
		"""
		Generate UIF U19 form data.

		Returns:
			dict: Form data for U19
		"""
		employee = frappe.get_doc("Employee", self.employee)
		company = frappe.get_doc("Company", employee.company)

		form_data = {
			"employer_name": company.company_name,
			"employer_uif_number": company.get("za_uif_reference_number", ""),
			"employee_name": employee.employee_name,
			"employee_id_number": employee.get("za_id_number", ""),
			"last_day_worked": self.last_day_worked,
			"reason_for_leaving": self.reason_for_leaving,
			"total_uif_contributions": self.total_uif_contributions,
			"declaration_date": self.declaration_date or today()
		}

		return form_data

	@frappe.whitelist()
	def export_pdf(self):
		"""
		Export U19 declaration as PDF.
		"""
		frappe.throw(
			_("UIF U19 PDF export is not available yet. Use the generated form data for manual UIF preparation."),
			title=_("Manual Preparation Required"),
		)
