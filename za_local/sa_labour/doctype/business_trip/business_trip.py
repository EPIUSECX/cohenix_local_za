# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Business Trip

Main DocType for managing employee business trips including:
- Daily allowances and per diem rates
- Transport and mileage claims
- Accommodation expenses
- Other expenses
- Automatic expense claim generation
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class BusinessTrip(Document):
	"""Business Trip document with expense tracking and claim generation"""
	
	def validate(self):
		"""Validate business trip data"""
		self.validate_dates()
		self.fetch_mileage_rates()
		self.calculate_allowance_totals()
		self.calculate_journey_totals()
		self.calculate_accommodation_total()
		self.calculate_other_expenses_total()
		self.calculate_grand_total()
	
	def validate_dates(self):
		"""Ensure from_date is before to_date"""
		if self.from_date and self.to_date:
			if getdate(self.from_date) > getdate(self.to_date):
				frappe.throw(_("From Date cannot be after To Date"))
	
	def fetch_mileage_rates(self):
		"""Fetch mileage rate from settings for journey calculations"""
		if not self.journeys:
			return
		
		settings = frappe.get_cached_doc("Business Trip Settings")
		mileage_rate = settings.mileage_allowance_rate or 4.25
		
		for journey in self.journeys:
			if journey.transport_mode == "Car (Private)":
				journey.mileage_rate = mileage_rate
				if journey.distance_km:
					journey.mileage_claim = flt(journey.distance_km) * flt(mileage_rate)
	
	def calculate_allowance_totals(self):
		"""Calculate totals for daily allowances"""
		self.total_allowance = 0
		self.total_incidental = 0
		
		for allowance in self.allowances:
			# Calculate total for this row
			daily = flt(allowance.daily_rate)
			incidental = flt(allowance.incidental_rate)
			allowance.total = daily + incidental
			
			# Add to totals
			self.total_allowance += daily
			self.total_incidental += incidental
	
	def calculate_journey_totals(self):
		"""Calculate totals for journeys"""
		self.total_mileage_claim = 0
		self.total_receipt_claims = 0
		
		for journey in self.journeys:
			if journey.transport_mode == "Car (Private)":
				self.total_mileage_claim += flt(journey.mileage_claim)
			else:
				self.total_receipt_claims += flt(journey.receipt_amount)
	
	def calculate_accommodation_total(self):
		"""Calculate total accommodation expenses"""
		self.total_accommodation = sum(flt(acc.amount) for acc in self.accommodations)
	
	def calculate_other_expenses_total(self):
		"""Calculate total other expenses"""
		self.total_other_expenses = sum(flt(exp.amount) for exp in self.other_expenses)
	
	def calculate_grand_total(self):
		"""Calculate grand total of all expenses"""
		self.grand_total = (
			flt(self.total_allowance) +
			flt(self.total_incidental) +
			flt(self.total_mileage_claim) +
			flt(self.total_receipt_claims) +
			flt(self.total_accommodation) +
			flt(self.total_other_expenses)
		)
	
	def on_submit(self):
		"""On submit, create expense claim if configured"""
		self.status = "Submitted"
		
		settings = frappe.get_cached_doc("Business Trip Settings")
		if settings.auto_create_expense_claim_on_submit:
			self.create_expense_claim()
	
	def on_cancel(self):
		"""On cancel, update status"""
		self.status = "Cancelled"
		
		# Cancel linked expense claim if it exists and is not submitted
		if self.expense_claim:
			expense_claim = frappe.get_doc("Expense Claim", self.expense_claim)
			if expense_claim.docstatus == 0:
				frappe.delete_doc("Expense Claim", self.expense_claim)
				self.expense_claim = None
			elif expense_claim.docstatus == 1:
				frappe.msgprint(
					_("Linked Expense Claim {0} must be cancelled separately").format(self.expense_claim),
					alert=True
				)
	
	def create_expense_claim(self):
		"""Create Expense Claim from Business Trip"""
		if self.expense_claim:
			frappe.msgprint(_("Expense Claim already created: {0}").format(self.expense_claim))
			return
		
		settings = frappe.get_cached_doc("Business Trip Settings")
		
		# Create Expense Claim
		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.employee = self.employee
		expense_claim.expense_approver = frappe.db.get_value("Employee", self.employee, "reports_to")
		expense_claim.company = self.company
		expense_claim.posting_date = self.to_date
		
		# Add custom field reference to business trip
		if hasattr(expense_claim, "business_trip"):
			expense_claim.business_trip = self.name
		
		# Add allowances
		if self.total_allowance or self.total_incidental:
			claim_type = settings.meal_expense_claim_type or "Travel"
			expense_claim.append("expenses", {
				"expense_date": self.from_date,
				"description": f"Business Trip Allowances: {self.trip_purpose}",
				"expense_type": claim_type,
				"amount": flt(self.total_allowance) + flt(self.total_incidental)
			})
		
		# Add mileage claims
		if self.total_mileage_claim:
			claim_type = settings.mileage_expense_claim_type or "Travel"
			expense_claim.append("expenses", {
				"expense_date": self.from_date,
				"description": f"Mileage Claims: {self.trip_purpose}",
				"expense_type": claim_type,
				"amount": flt(self.total_mileage_claim)
			})
		
		# Add transport receipts
		if self.total_receipt_claims:
			expense_claim.append("expenses", {
				"expense_date": self.from_date,
				"description": f"Transport (Flights/Trains/Rental): {self.trip_purpose}",
				"expense_type": "Travel",
				"amount": flt(self.total_receipt_claims)
			})
		
		# Add accommodation
		if self.total_accommodation:
			expense_claim.append("expenses", {
				"expense_date": self.from_date,
				"description": f"Accommodation: {self.trip_purpose}",
				"expense_type": "Travel",
				"amount": flt(self.total_accommodation)
			})
		
		# Add other expenses
		if self.total_other_expenses:
			expense_claim.append("expenses", {
				"expense_date": self.from_date,
				"description": f"Other Expenses: {self.trip_purpose}",
				"expense_type": "Others",
				"amount": flt(self.total_other_expenses)
			})
		
		# Save and link
		expense_claim.insert()
		
		self.expense_claim = expense_claim.name
		self.status = "Expense Claim Created"
		self.db_update()
		
		frappe.msgprint(
			_("Expense Claim {0} created successfully").format(expense_claim.name),
			alert=True,
			indicator="green"
		)
		
		return expense_claim.name


@frappe.whitelist()
def create_expense_claim_from_trip(business_trip_name):
	"""
	Create Expense Claim from Business Trip (callable from client).
	
	Args:
		business_trip_name: Name of Business Trip document
	
	Returns:
		str: Name of created Expense Claim
	"""
	trip = frappe.get_doc("Business Trip", business_trip_name)
	
	if trip.docstatus != 1:
		frappe.throw(_("Business Trip must be submitted before creating Expense Claim"))
	
	return trip.create_expense_claim()


@frappe.whitelist()
def generate_allowances_for_date_range(business_trip_name):
	"""
	Auto-generate daily allowance rows for the date range of the trip.
	
	Args:
		business_trip_name: Name of Business Trip document
	
	Returns:
		list: List of generated allowance rows
	"""
	trip = frappe.get_doc("Business Trip", business_trip_name)
	
	if not trip.from_date or not trip.to_date:
		frappe.throw(_("Please set From Date and To Date first"))
	
	from datetime import timedelta
	
	current_date = getdate(trip.from_date)
	end_date = getdate(trip.to_date)
	
	# Clear existing allowances
	trip.allowances = []
	
	# Generate one row per day
	while current_date <= end_date:
		trip.append("allowances", {
			"date": current_date,
			"region": None,  # User will select
			"daily_rate": 0,
			"incidental_rate": 0,
			"total": 0
		})
		current_date += timedelta(days=1)
	
	trip.save()
	
	frappe.msgprint(
		_("{0} allowance rows generated").format(len(trip.allowances)),
		alert=True,
		indicator="green"
	)
	
	return trip.allowances

