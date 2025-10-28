# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HousingBenefit(Document):
	def autoname(self):
		"""Set name based on employee and property"""
		if self.employee and self.property_address:
			# Use first 20 chars of address for name
			address_short = self.property_address[:20].replace("\n", " ")
			self.name = f"{self.employee}-{address_short}"
			
	def validate(self):
		"""Validate housing benefit"""
		self.calculate_monthly_benefit()
		
	def calculate_monthly_benefit(self):
		"""
		Calculate monthly taxable value for housing benefit.
		
		SARS Rules:
		- Company-owned property: Lower of actual cost or market rental
		- Housing allowance: Full allowance is taxable
		- Electricity/water: Add to taxable value if provided free
		
		Simplified calculation:
		- Owned by Company: Use rental value (assumed to be market-related)
		- Third Party: Full rental value taxable
		"""
		monthly_rental = flt(self.monthly_rental_value)
		electricity = flt(self.electricity_contribution)
		water = flt(self.water_contribution)
		
		# Base taxable value
		if self.owned_by == "Company":
			# Company-owned: rental value is taxable
			base_taxable = monthly_rental
		else:
			# Third party: full rental value
			base_taxable = monthly_rental
		
		# Add utilities if provided free
		self.monthly_taxable_value = base_taxable + electricity + water
		
		# Set calculation method for transparency
		self.calculation_method = (
			f"Rental Value: R{monthly_rental:,.2f}\n"
			f"Owned By: {self.owned_by}\n"
			f"Electricity: R{electricity:,.2f}\n"
			f"Water: R{water:,.2f}\n"
			f"Total Monthly Taxable Value: R{self.monthly_taxable_value:,.2f}"
		)
		
		return self.monthly_taxable_value


@frappe.whitelist()
def get_housing_tax_rate(owned_by):
	"""
	Get housing benefit tax rate based on ownership.
	
	Args:
		owned_by: "Company" or "Third Party"
		
	Returns:
		dict: Tax treatment information
	"""
	if owned_by == "Company":
		return {
			"treatment": "Use market rental or actual cost (lower)",
			"taxable_percentage": 100
		}
	else:
		return {
			"treatment": "Full rental value taxable",
			"taxable_percentage": 100
		}
