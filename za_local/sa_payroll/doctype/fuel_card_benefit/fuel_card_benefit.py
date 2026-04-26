# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate, today


class FuelCardBenefit(Document):
	def validate(self):
		"""Validate FuelCardBenefit"""
		self.calculate_monthly_benefit()

	def calculate_monthly_benefit(self):
		"""Calculate taxable private fuel benefit from private mileage evidence."""
		private_km = flt(self.private_km_per_month)
		consumption = flt(self.vehicle_fuel_consumption)
		rate = flt(self.fuel_rate_per_liter)
		private_fuel_cost = (private_km / 100) * consumption * rate

		monthly_limit = flt(self.monthly_limit)
		self.monthly_taxable_value = min(private_fuel_cost, monthly_limit) if monthly_limit else private_fuel_cost
		return self.monthly_taxable_value
