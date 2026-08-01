# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from za_local.sa_payroll.fringe_benefits.calculations import calculate_company_car_values


class CompanyCarBenefit(Document):
	def autoname(self):
		if self.employee and self.vehicle_registration:
			self.name = f"{self.employee}-{self.vehicle_registration}"

	def validate(self):
		if flt(self.purchase_price) <= 0:
			frappe.throw(_("Determined Value must be greater than zero."))
		self.calculate_usage()
		self.calculate_monthly_benefit()

	def calculate_usage(self):
		private_km = flt(self.private_km_per_month)
		business_km = flt(self.business_km_per_month)
		if private_km < 0 or business_km < 0:
			frappe.throw(_("Private and business kilometres cannot be negative."))

		self.total_km_per_month = private_km + business_km
		self.private_use_percentage = (
			private_km / self.total_km_per_month * 100 if self.total_km_per_month else 0
		)

	@frappe.whitelist()
	def calculate_monthly_benefit(self):
		"""Calculate the SARS Seventh Schedule monthly cash equivalent."""
		values = calculate_company_car_values(
			self.purchase_price,
			has_maintenance_plan=self.has_maintenance_plan,
			employee_consideration=self.employee_consideration,
			business_use_at_least_80_percent=self.business_use_at_least_80_percent,
		)
		self.monthly_taxable_value = values["monthly_cash_equivalent"]
		self.paye_inclusion_percentage = values["paye_inclusion_percentage"]
		self.monthly_paye_value = values["monthly_paye_value"]
		self.calculation_method = _(
			"Determined value: R{0:,.2f}\nMonthly rate: {1}%\n"
			"Less employee consideration: R{2:,.2f}\nMonthly cash equivalent: R{3:,.2f}\n"
			"PAYE inclusion: {4}% = R{5:,.2f}"
		).format(
			flt(self.purchase_price),
			values["monthly_rate"],
			flt(self.employee_consideration),
			values["monthly_cash_equivalent"],
			values["paye_inclusion_percentage"],
			values["monthly_paye_value"],
		)
		return values
