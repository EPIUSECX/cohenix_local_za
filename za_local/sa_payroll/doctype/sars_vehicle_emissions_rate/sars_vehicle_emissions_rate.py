# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class SarsVehicleEmissionsRate(Document):
	def validate(self):
		"""Validate SarsVehicleEmissionsRate"""
		if self.co2_grams_per_km_to < self.co2_grams_per_km_from:
			frappe.throw(_("CO2 range end cannot be lower than range start"))

	def get_current_rate(self, co2_grams_per_km=None):
		"""Return the configured taxable value rate for a CO2 value."""
		co2 = flt(co2_grams_per_km if co2_grams_per_km is not None else self.co2_grams_per_km_from)
		return frappe.db.get_value(
			"Sars Vehicle Emissions Rate",
			{
				"co2_grams_per_km_from": ["<=", co2],
				"co2_grams_per_km_to": [">=", co2],
			},
			"monthly_taxable_value_per_r1000",
			order_by="effective_from desc",
		)
