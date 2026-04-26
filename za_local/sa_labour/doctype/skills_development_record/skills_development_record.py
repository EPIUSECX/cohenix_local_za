# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate


class SkillsDevelopmentRecord(Document):
	def validate(self):
		self.validate_training_dates()
		self.calculate_bec_points()

	def calculate_bec_points(self):
		total_spend = flt(self.training_cost) + flt(self.bursary_amount)
		if not total_spend:
			self.bec_points = 0
			return

		duration_days = max(date_diff(self.end_date, self.start_date) + 1, 1) if self.start_date and self.end_date else 1
		disabled_multiplier = 1.25 if self.is_disabled_learner else 1
		self.bec_points = flt((total_spend / 1000) * (duration_days / 30) * disabled_multiplier, 2)

	def validate_training_dates(self):
		if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("Training End Date cannot be before Start Date."))

		if flt(self.training_cost) < 0 or flt(self.bursary_amount) < 0:
			frappe.throw(_("Training cost and bursary amount cannot be negative."))
