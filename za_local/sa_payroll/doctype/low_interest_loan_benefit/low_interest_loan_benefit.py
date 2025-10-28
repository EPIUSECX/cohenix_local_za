# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class LowInterestLoanBenefit(Document):
	def autoname(self):
		"""Set name based on employee and loan date"""
		if self.employee and self.loan_start_date:
			self.name = f"{self.employee}-{self.loan_start_date}"
			
	def validate(self):
		"""Validate low interest loan benefit"""
		self.calculate_interest_benefit()
		
	def calculate_interest_benefit(self):
		"""
		Calculate monthly interest benefit for low-interest loans.
		
		SARS Rule: Difference between official rate and actual rate applied to loan amount.
		Official rate is set by SARS (currently around 10% p.a.)
		
		Formula: (Official Rate - Actual Rate) * Loan Amount / 12
		"""
		loan_amount = flt(self.loan_amount)
		actual_rate = flt(self.interest_rate) / 100  # Convert percentage to decimal
		official_rate = flt(self.official_interest_rate) / 100
		
		if official_rate <= actual_rate:
			# No benefit if actual rate >= official rate
			self.monthly_interest_benefit = 0
			return 0
		
		# Annual benefit
		annual_benefit = (official_rate - actual_rate) * loan_amount
		
		# Monthly benefit
		self.monthly_interest_benefit = annual_benefit / 12
		
		return self.monthly_interest_benefit
		
	@frappe.whitelist()
	def get_official_rate(self):
		"""
		Get current SARS official interest rate.
		
		Returns:
			float: Official interest rate (default 10.25%)
		"""
		# TODO: Fetch from SARS rate master (to be created)
		# For now, return default rate
		default_rate = 10.25
		
		# Check if there's a system-wide setting
		official_rate = frappe.db.get_single_value("Payroll Settings", "za_official_interest_rate")
		
		if official_rate:
			self.official_interest_rate = official_rate
		else:
			self.official_interest_rate = default_rate
			
		self.calculate_interest_benefit()
		
		return self.official_interest_rate


@frappe.whitelist()
def get_current_official_rate():
	"""
	Get current SARS official interest rate for low-interest loans.
	
	Returns:
		float: Current official rate
	"""
	# TODO: Implement proper rate tracking
	# For now return 2024 rate
	return 10.25
