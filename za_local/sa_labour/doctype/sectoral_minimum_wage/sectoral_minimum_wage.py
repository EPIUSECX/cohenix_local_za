# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SectoralMinimumWage(Document):
	def validate(self):
		if flt(self.hourly_rate) <= 0 and flt(self.monthly_rate) <= 0:
			frappe.throw(_("Set at least an hourly or monthly minimum wage rate."))

		if flt(self.hourly_rate) < 0 or flt(self.monthly_rate) < 0:
			frappe.throw(_("Minimum wage rates cannot be negative."))

	def validate_employee_salary(self):
		return {
			"sector": self.sector,
			"position_category": self.position_category,
			"hourly_rate": flt(self.hourly_rate),
			"monthly_rate": flt(self.monthly_rate),
		}
