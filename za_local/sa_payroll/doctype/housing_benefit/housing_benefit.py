# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today

from za_local.sa_payroll.fringe_benefits.calculations import calculate_housing_values


class HousingBenefit(Document):
	def autoname(self):
		if self.employee and self.property_address:
			address_short = self.property_address[:20].replace("\n", " ")
			self.name = f"{self.employee}-{address_short}"

	def validate(self):
		self.calculation_date = self.calculation_date or today()
		if flt(self.remuneration_proxy) <= 0:
			frappe.throw(_("Remuneration Proxy must be greater than zero."))
		self.calculate_monthly_benefit()

	@frappe.whitelist()
	def calculate_monthly_benefit(self):
		"""Calculate residential accommodation under paragraph 9."""
		values = calculate_housing_values(
			self.remuneration_proxy,
			date_value=self.calculation_date or today(),
			room_count=self.room_count,
			furnished=self.furnished,
			power_or_fuel_provided=self.power_or_fuel_provided,
			abatement_reduced_to_zero=self.abatement_reduced_to_zero,
			provided_by=self.owned_by,
			employer_monthly_expenditure=self.monthly_rental_value,
			employee_consideration=self.employee_rental_contribution,
		)
		for fieldname, value in values.items():
			self.set(fieldname, value)
		self.calculation_method = _(
			"(R{0:,.2f} - R{1:,.2f}) x {2}% / 12 = R{3:,.2f}\n"
			"Provided by: {4}\nLess employee consideration: R{5:,.2f}\n"
			"Monthly taxable value: R{6:,.2f}"
		).format(
			flt(self.remuneration_proxy),
			values["statutory_abatement"],
			values["formula_percentage"],
			values["monthly_formula_value"],
			self.owned_by,
			flt(self.employee_rental_contribution),
			values["monthly_taxable_value"],
		)
		return values
