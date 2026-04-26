# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class AnnualTrainingReport(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft"
		self.calculate_actual_spend()

	def generate_atr_report(self):
		self.status = "Prepared"
		if not self.submission_date:
			self.submission_date = today()
		return {
			"company": self.company,
			"fiscal_year": self.fiscal_year,
			"seta": self.seta,
			"completed_interventions": len(self.training_completed or []),
			"actual_training_spend": flt(self.actual_training_spend),
		}

	def calculate_actual_spend(self):
		self.actual_training_spend = sum(flt(row.actual_cost) for row in self.training_completed or [])

		for row in self.training_completed or []:
			if flt(row.number_trained) < 0:
				frappe.throw(_("Number trained cannot be negative."))
			if flt(row.actual_cost) < 0:
				frappe.throw(_("Actual training cost cannot be negative."))
