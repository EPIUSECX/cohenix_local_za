"""Business Trip controller and guarded document actions."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from za_local.utils.statutory_rates import get_reimbursive_travel_rate


class BusinessTrip(Document):
	def validate(self):
		self.validate_dates()
		self.fetch_mileage_rates()
		self.calculate_allowance_totals()
		self.calculate_journey_totals()
		self.calculate_accommodation_total()
		self.calculate_other_expenses_total()
		self.calculate_grand_total()

	def validate_dates(self):
		if self.from_date and self.to_date and getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date cannot be after To Date"))

	def fetch_mileage_rates(self):
		for journey in self.get("journeys") or []:
			if journey.transport_mode != "Car (Private)":
				continue
			journey.mileage_rate = get_business_trip_mileage_rate(
				journey.date or self.to_date or self.from_date
			)
			journey.mileage_claim = flt(journey.distance_km) * flt(journey.mileage_rate)

	def calculate_allowance_totals(self):
		self.total_allowance = 0
		self.total_incidental = 0
		for allowance in self.get("allowances") or []:
			daily = flt(allowance.daily_rate)
			incidental = flt(allowance.incidental_rate)
			allowance.total = daily + incidental
			self.total_allowance += daily
			self.total_incidental += incidental

	def calculate_journey_totals(self):
		self.total_mileage_claim = 0
		self.total_receipt_claims = 0
		for journey in self.get("journeys") or []:
			if journey.transport_mode == "Car (Private)":
				self.total_mileage_claim += flt(journey.mileage_claim)
			else:
				self.total_receipt_claims += flt(journey.receipt_amount)

	def calculate_accommodation_total(self):
		self.total_accommodation = sum(flt(row.amount) for row in self.get("accommodations") or [])

	def calculate_other_expenses_total(self):
		self.total_other_expenses = sum(flt(row.amount) for row in self.get("other_expenses") or [])

	def calculate_grand_total(self):
		self.grand_total = sum(
			flt(value)
			for value in (
				self.total_allowance,
				self.total_incidental,
				self.total_mileage_claim,
				self.total_receipt_claims,
				self.total_accommodation,
				self.total_other_expenses,
			)
		)

	def on_submit(self):
		self.db_set("status", "Submitted", update_modified=False)
		settings = frappe.get_cached_doc("Business Trip Settings")
		if settings.auto_create_expense_claim_on_submit:
			self.create_expense_claim()

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)
		if not self.expense_claim:
			return

		expense_claim = frappe.get_doc("Expense Claim", self.expense_claim)
		if expense_claim.docstatus == 0:
			expense_claim.delete()
			self.db_set("expense_claim", None, update_modified=False)
		elif expense_claim.docstatus == 1:
			frappe.throw(
				_("Cancel linked Expense Claim {0} before cancelling this Business Trip.").format(
					frappe.bold(self.expense_claim)
				)
			)

	def create_expense_claim(self):
		if self.expense_claim:
			return self.expense_claim

		settings = frappe.get_cached_doc("Business Trip Settings")
		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.update(
			{
				"employee": self.employee,
				"expense_approver": self._get_expense_approver(),
				"company": self.company,
				"posting_date": self.to_date,
			}
		)
		if expense_claim.meta.has_field("business_trip"):
			expense_claim.business_trip = self.name

		self._append_expense(
			expense_claim,
			flt(self.total_allowance) + flt(self.total_incidental),
			settings.meal_expense_claim_type or "Travel",
			_("Business Trip Allowances: {0}").format(self.trip_purpose),
		)
		self._append_expense(
			expense_claim,
			self.total_mileage_claim,
			settings.mileage_expense_claim_type or "Travel",
			_("Mileage Claims: {0}").format(self.trip_purpose),
		)
		self._append_expense(
			expense_claim,
			self.total_receipt_claims,
			"Travel",
			_("Transport Receipts: {0}").format(self.trip_purpose),
		)
		self._append_expense(
			expense_claim,
			self.total_accommodation,
			"Travel",
			_("Accommodation: {0}").format(self.trip_purpose),
		)
		self._append_expense(
			expense_claim,
			self.total_other_expenses,
			"Others",
			_("Other Expenses: {0}").format(self.trip_purpose),
		)

		if not expense_claim.expenses:
			frappe.throw(_("No claimable Business Trip expenses were calculated."))
		expense_claim.insert()
		self.db_set(
			{"expense_claim": expense_claim.name, "status": "Expense Claim Created"},
			update_modified=False,
		)
		frappe.msgprint(
			_("Expense Claim {0} created successfully").format(frappe.bold(expense_claim.name)),
			alert=True,
			indicator="green",
		)
		return expense_claim.name

	def _append_expense(self, expense_claim, amount, expense_type, description):
		if not flt(amount):
			return
		expense_claim.append(
			"expenses",
			{
				"expense_date": self.from_date,
				"description": description,
				"expense_type": expense_type,
				"amount": flt(amount),
			},
		)

	def _get_expense_approver(self):
		"""Resolve an Expense Claim User, never an Employee document name."""
		employee = frappe.get_cached_value(
			"Employee",
			self.employee,
			["expense_approver", "reports_to"],
			as_dict=True,
		) or frappe._dict()
		if employee.expense_approver:
			return employee.expense_approver
		if employee.reports_to:
			return frappe.get_cached_value("Employee", employee.reports_to, "user_id")
		return None


def get_business_trip_mileage_rate(date_value=None):
	"""Use an explicit company setting, otherwise the date-effective rate pack."""
	configured_rate = flt(
		frappe.get_cached_doc("Business Trip Settings").mileage_allowance_rate
	)
	return configured_rate or get_reimbursive_travel_rate(date_value)


@frappe.whitelist()
def create_expense_claim_from_trip(business_trip_name):
	trip = frappe.get_doc("Business Trip", business_trip_name, check_permission=True)
	trip.check_permission("write")
	if trip.docstatus != 1:
		frappe.throw(_("Business Trip must be submitted before creating an Expense Claim."))
	return trip.create_expense_claim()


@frappe.whitelist()
def generate_allowances_for_date_range(business_trip_name, region):
	"""Generate one fully-valued allowance row per trip day."""
	trip = frappe.get_doc("Business Trip", business_trip_name, check_permission=True)
	trip.check_permission("write")
	if trip.docstatus != 0:
		frappe.throw(_("Allowances can be generated only while the Business Trip is in Draft."))
	if not trip.from_date or not trip.to_date:
		frappe.throw(_("Set From Date and To Date before generating allowances."))
	if not region:
		frappe.throw(_("Select a Business Trip Region."))

	region_values = frappe.get_cached_value(
		"Business Trip Region",
		region,
		["is_active", "daily_allowance_rate", "incidental_allowance_rate"],
		as_dict=True,
	)
	if not region_values or not region_values.is_active:
		frappe.throw(_("Business Trip Region {0} is not active or does not exist.").format(frappe.bold(region)))

	trip.set("allowances", [])
	current_date = getdate(trip.from_date)
	end_date = getdate(trip.to_date)
	while current_date <= end_date:
		trip.append(
			"allowances",
			{
				"date": current_date,
				"region": region,
				"daily_rate": region_values.daily_allowance_rate,
				"incidental_rate": region_values.incidental_allowance_rate,
				"total": flt(region_values.daily_allowance_rate)
				+ flt(region_values.incidental_allowance_rate),
			},
		)
		current_date += timedelta(days=1)

	trip.save()
	frappe.msgprint(
		_("{0} allowance rows generated for {1}").format(len(trip.allowances), frappe.bold(region)),
		alert=True,
		indicator="green",
	)
	return len(trip.allowances)
