# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, add_months, get_first_day, get_last_day, today


class FringeBenefit(Document):
	def validate(self):
		"""Validate fringe benefit"""
		self.validate_dates()
		self.calculate_taxable_value()
		self.update_status()
		
	def before_submit(self):
		"""Actions before submission"""
		self.generate_monthly_breakdown()
		
	def on_submit(self):
		"""Actions on submission"""
		self.status = "Active"
		
	def on_cancel(self):
		"""Actions on cancellation"""
		self.status = "Inactive"
		
	def validate_dates(self):
		"""Validate from/to dates"""
		if not self.from_date:
			frappe.throw(_("From Date is required"))
			
		if self.to_date and getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date"))
			
	def update_status(self):
		"""Update status based on dates"""
		if not self.from_date:
			return
			
		current_date = getdate(today())
		from_date = getdate(self.from_date)
		
		if from_date > current_date:
			self.status = "Pending"
		elif self.to_date and getdate(self.to_date) < current_date:
			self.status = "Expired"
		elif self.docstatus == 1:
			self.status = "Active"
			
	@frappe.whitelist()
	def calculate_taxable_value(self):
		"""Calculate taxable value based on benefit type"""
		if self.benefit_type == "Company Car" and self.company_car_details:
			car = frappe.get_doc("Company Car Benefit", self.company_car_details)
			self.taxable_value = car.calculate_monthly_benefit()
			
		elif self.benefit_type == "Housing" and self.housing_details:
			housing = frappe.get_doc("Housing Benefit", self.housing_details)
			self.taxable_value = housing.calculate_monthly_benefit()
			
		elif self.benefit_type == "Low Interest Loan" and self.loan_details:
			loan = frappe.get_doc("Low Interest Loan Benefit", self.loan_details)
			self.taxable_value = loan.calculate_interest_benefit()
			
		else:
			# For other benefits, use the benefit value directly
			self.taxable_value = flt(self.benefit_value)
			
	@frappe.whitelist()
	def generate_monthly_breakdown(self):
		"""Generate monthly breakdown of fringe benefit"""
		# Clear existing breakdown
		self.monthly_breakdown = []
		
		if not self.from_date:
			return
			
		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date) if self.to_date else getdate(today())
		
		# Generate breakdown for each month in the period
		current_month = get_first_day(from_date)
		end_month = get_first_day(to_date)
		
		while current_month <= end_month:
			# Calculate days in month
			month_start = max(current_month, from_date)
			month_end = min(get_last_day(current_month), to_date)
			days_in_month = (month_end - month_start).days + 1
			total_days_in_month = (get_last_day(current_month) - get_first_day(current_month)).days + 1
			
			# Pro-rata calculation
			monthly_taxable = flt(self.taxable_value) * (days_in_month / total_days_in_month)
			
			self.append("monthly_breakdown", {
				"month": current_month,
				"days_applicable": days_in_month,
				"taxable_value": monthly_taxable
			})
			
			# Move to next month
			current_month = add_months(current_month, 1)
			
	def get_monthly_tax_impact(self, month):
		"""
		Get the tax impact for a specific month
		
		Args:
			month: Date in the month
			
		Returns:
			float: Taxable amount for the month
		"""
		month_start = get_first_day(month)
		
		for row in self.monthly_breakdown:
			if getdate(row.month) == month_start:
				return flt(row.taxable_value)
				
		return 0.0


@frappe.whitelist()
def get_active_fringe_benefits(employee, date=None):
	"""
	Get all active fringe benefits for an employee on a specific date
	
	Args:
		employee: Employee ID
		date: Date to check (defaults to today)
		
	Returns:
		list: List of active fringe benefit documents
	"""
	if not date:
		date = today()
		
	benefits = frappe.get_all(
		"Fringe Benefit",
		filters={
			"employee": employee,
			"docstatus": 1,
			"status": "Active",
			"from_date": ["<=", date],
		},
		or_filters=[
			["to_date", ">=", date],
			["to_date", "is", "not set"]
		],
		fields=["name", "benefit_type", "taxable_value"]
	)
	
	return benefits

