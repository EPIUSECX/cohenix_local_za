# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class WorkplaceSkillsPlan(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft"
		self.validate_budget()

	def generate_wsp_report(self):
		self.status = "Prepared"
		if not self.submission_date:
			self.submission_date = today()
		return {
			"company": self.company,
			"fiscal_year": self.fiscal_year,
			"seta": self.seta,
			"training_interventions": len(self.training_details or []),
			"total_training_budget": flt(self.total_training_budget),
		}

	def validate_budget(self):
		calculated_budget = sum(flt(row.estimated_cost) for row in self.training_details or [])
		if calculated_budget:
			self.total_training_budget = calculated_budget

		for row in self.training_details or []:
			if flt(row.number_of_employees) < 0:
				frappe.throw(_("Number of employees cannot be negative."))
			if flt(row.estimated_cost) < 0:
				frappe.throw(_("Estimated training cost cannot be negative."))
