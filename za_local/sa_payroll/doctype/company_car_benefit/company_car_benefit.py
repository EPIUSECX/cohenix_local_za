# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CompanyCarBenefit(Document):
	def autoname(self):
		"""Set name based on employee and vehicle"""
		if self.employee and self.vehicle_registration:
			self.name = f"{self.employee}-{self.vehicle_registration}"
			
	def validate(self):
		"""Validate company car benefit"""
		self.calculate_usage()
		self.calculate_monthly_benefit()
		
	def calculate_usage(self):
		"""Calculate total km and private use percentage"""
		private_km = flt(self.private_km_per_month)
		business_km = flt(self.business_km_per_month)
		
		self.total_km_per_month = private_km + business_km
		
		if self.total_km_per_month > 0:
			self.private_use_percentage = (private_km / self.total_km_per_month) * 100
		else:
			self.private_use_percentage = 0
			
	def calculate_monthly_benefit(self):
		"""
		Calculate monthly taxable value based on CO2 emissions
		
		SARS formula: (Purchase Price / 1000) * CO2 Rate * 3.5% per month
		CO2 Rate increases with emissions:
		- 0-120 g/km: 1x multiplier
		- 121-160 g/km: 1.25x multiplier  
		- 161-200 g/km: 1.5x multiplier
		- > 200 g/km: 1.75x multiplier
		"""
		purchase_price = flt(self.purchase_price)
		co2 = flt(self.co2_emissions)
		
		# Determine CO2 multiplier
		if co2 <= 120:
			co2_multiplier = 1.0
			bracket = "0-120 g/km"
		elif co2 <= 160:
			co2_multiplier = 1.25
			bracket = "121-160 g/km"
		elif co2 <= 200:
			co2_multiplier = 1.5
			bracket = "161-200 g/km"
		else:
			co2_multiplier = 1.75
			bracket = "> 200 g/km"
			
		# Base taxable value per month (3.5% of purchase price)
		base_value = (purchase_price * 0.035)
		
		# Apply CO2 multiplier
		self.monthly_taxable_value = base_value * co2_multiplier
		
		# Set calculation method for transparency
		self.calculation_method = (
			f"Purchase Price: R{purchase_price:,.2f}\n"
			f"Base Rate: 3.5% per month = R{base_value:,.2f}\n"
			f"CO2 Emissions: {co2} g/km ({bracket})\n"
			f"CO2 Multiplier: {co2_multiplier}x\n"
			f"Monthly Taxable Value: R{self.monthly_taxable_value:,.2f}"
		)
		
		return self.monthly_taxable_value


@frappe.whitelist()
def get_co2_multiplier(co2_emissions):
	"""
	Get CO2 multiplier for given emissions
	
	Args:
		co2_emissions: CO2 emissions in g/km
		
	Returns:
		dict: multiplier and bracket
	"""
	co2 = flt(co2_emissions)
	
	if co2 <= 120:
		return {"multiplier": 1.0, "bracket": "0-120 g/km"}
	elif co2 <= 160:
		return {"multiplier": 1.25, "bracket": "121-160 g/km"}
	elif co2 <= 200:
		return {"multiplier": 1.5, "bracket": "161-200 g/km"}
	else:
		return {"multiplier": 1.75, "bracket": "> 200 g/km"}

