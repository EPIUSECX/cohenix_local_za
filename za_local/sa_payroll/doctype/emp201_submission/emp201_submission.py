# Copyright (c) 2024, Kartoza and contributors
# For license information, please see license.txt

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, get_first_day, get_last_day, getdate

PAYE_CODES = {"4102", "4115"}
UIF_CODES = {"4141"}
SDL_CODES = {"4142"}
ETI_CODES = {"4118"}
ETI_RECONCILIATION_END_MONTHS = {2, 8}
ETI_RECONCILIATION_OPENING_MONTHS = {3, 9}


def _get_salary_component_metadata(component_name):
	if not component_name:
		return frappe._dict()

	return (
		frappe.db.get_value(
			"Salary Component",
			component_name,
			["za_sars_payroll_code", "is_income_tax_component"],
			as_dict=True,
		)
		or frappe._dict()
	)


def _get_emp201_bucket(component_name):
	metadata = _get_salary_component_metadata(component_name)
	code = metadata.get("za_sars_payroll_code")

	if code in PAYE_CODES:
		return "paye", metadata
	if code in UIF_CODES:
		return "uif", metadata
	if code in SDL_CODES:
		return "sdl", metadata
	if code in ETI_CODES:
		return "eti", metadata

	return None, metadata


def _looks_like_legacy_statutory_component(component_name, metadata):
	component_name_lower = (component_name or "").strip().lower()
	tokens = (
		"uif",
		"unemployment insurance fund",
		"sdl",
		"skills development levy",
		"eti",
		"employment tax incentive",
	)

	return bool(metadata.get("is_income_tax_component")) or any(
		token in component_name_lower for token in tokens
	)


def calculate_eti_utilisation(gross_paye, eti_generated, previous_carry_forward, period_start_date):
	"""Apply the employer PAYE cap and six-month ETI reconciliation boundaries."""
	period_start_date = getdate(period_start_date)
	gross_paye = max(0, flt(gross_paye))
	eti_generated = max(0, flt(eti_generated))
	previous_carry_forward = max(0, flt(previous_carry_forward))

	if period_start_date.month in ETI_RECONCILIATION_OPENING_MONTHS:
		previous_carry_forward = 0

	total_available = previous_carry_forward + eti_generated
	utilized = min(gross_paye, total_available)
	unused = total_available - utilized
	is_reconciliation_end = period_start_date.month in ETI_RECONCILIATION_END_MONTHS
	refund_due = unused if is_reconciliation_end else 0
	carry_forward = 0 if is_reconciliation_end else unused

	return frappe._dict(
		eti_carried_forward_from_previous=flt(previous_carry_forward, 2),
		total_eti_available=flt(total_available, 2),
		eti_utilized_current_month=flt(utilized, 2),
		net_paye_payable=flt(gross_paye - utilized, 2),
		eti_to_be_carried_forward=flt(carry_forward, 2),
		eti_reconciliation_refund=flt(refund_due, 2),
	)


class EMP201Submission(Document):
	# Main class for EMP201 Submission
	def validate(self):
		self.set_submission_key()
		# Ensure company, fiscal_year, and month are set before checking for duplicates
		if self.company and self.fiscal_year and self.month:
			# For new documents, self.name will be temporary (e.g., "New EMP201 Submission-X")
			# and won't match existing records. For existing records, self.name is its unique ID.
			# This check prevents a document from conflicting with itself during an update.
			existing_submission = frappe.db.exists(
				"EMP201 Submission",
				{
					"company": self.company,
					"fiscal_year": self.fiscal_year,
					"month": self.month,
					"name": ["!=", self.name],  # Exclude the current document itself
					"docstatus": ["!=", 2],  # Not Cancelled (i.e., Draft or Submitted ones count as active)
				},
			)

			if existing_submission:
				frappe.throw(
					_(
						"An active EMP201 Submission for company '{0}', fiscal year '{1}', and month '{2}' already exists: {3}. Please cancel or delete the existing submission before creating a new one for the same period."
					).format(
						self.company,
						self.fiscal_year,
						self.month,
						frappe.utils.get_link_to_form("EMP201 Submission", existing_submission),
					),
					title=_("Duplicate Submission Period"),
					exc=frappe.DuplicateEntryError,
				)

		self.set_submission_period_dates()

	def set_submission_key(self):
		"""Persist a database-enforced identity for one active company period."""
		if not (self.company and self.fiscal_year and self.month):
			return
		identity = "|".join((self.company, self.fiscal_year, self.month))
		self.submission_key = hashlib.sha256(identity.encode()).hexdigest()

	@frappe.whitelist()
	def set_submission_period_dates(self):
		if not self.month or not self.fiscal_year:
			return None

		month_number = {
			"January": 1,
			"February": 2,
			"March": 3,
			"April": 4,
			"May": 5,
			"June": 6,
			"July": 7,
			"August": 8,
			"September": 9,
			"October": 10,
			"November": 11,
			"December": 12,
		}.get(self.month)
		if not month_number:
			frappe.throw(_("Invalid EMP201 month: {0}").format(self.month))

		fiscal_year = frappe.get_doc("Fiscal Year", self.fiscal_year)
		fiscal_start = getdate(fiscal_year.year_start_date)
		fiscal_end = getdate(fiscal_year.year_end_date)
		matching_periods = []
		for year in range(fiscal_start.year, fiscal_end.year + 1):
			start_date = getdate(f"{year}-{month_number:02d}-01")
			end_date = get_last_day(start_date)
			if fiscal_start <= start_date and end_date <= fiscal_end:
				matching_periods.append((start_date, end_date))

		if len(matching_periods) != 1:
			frappe.throw(
				_("Month {0} does not resolve to exactly one period inside Fiscal Year {1}.").format(
					self.month,
					self.fiscal_year,
				),
				title=_("Invalid EMP201 Period"),
			)

		start_date, end_date = matching_periods[0]
		self.submission_period_start_date = start_date
		self.submission_period_end_date = end_date

		return {"submission_period_start_date": start_date, "submission_period_end_date": end_date}

	@frappe.whitelist()
	def fetch_emp201_data(self):
		from frappe.utils import flt

		if not self.company or not self.submission_period_start_date or not self.submission_period_end_date:
			frappe.throw(_("Company and submission period dates are required to fetch data."))

		# Initialize local variables for calculation
		gross_paye = 0
		eti_generated = 0
		uif = 0
		sdl = 0
		unmapped_statutory_components = set()

		salary_slips = frappe.get_all(
			"Salary Slip",
			filters={
				"company": self.company,
				"end_date": [
					"between",
					[self.submission_period_start_date, self.submission_period_end_date],
				],
				"docstatus": 1,
			},
			fields=["name"],
		)

		if not salary_slips:
			frappe.msgprint(_("No submitted salary slips found for the selected period."))
			return {}

		for slip in salary_slips:
			ss = frappe.get_doc("Salary Slip", slip.name)
			slip_eti_amount = flt(ss.get("za_monthly_eti"))
			if slip_eti_amount:
				eti_generated += slip_eti_amount

			for table_name in ("deductions", "company_contribution", "earnings"):
				for comp in ss.get(table_name) or []:
					component_name = comp.get("salary_component")
					amount = flt(comp.amount)
					if not component_name or not amount:
						continue

					bucket, metadata = _get_emp201_bucket(component_name)
					if bucket == "paye":
						gross_paye += amount
					elif bucket == "uif":
						uif += amount
					elif bucket == "sdl":
						sdl += amount
					elif bucket == "eti" and not slip_eti_amount:
						eti_generated += amount
					elif _looks_like_legacy_statutory_component(component_name, metadata):
						unmapped_statutory_components.add(component_name)

		if unmapped_statutory_components:
			frappe.throw(
				_(
					"EMP201 data cannot be generated until all statutory salary components are mapped to SARS payroll codes. "
					"Update the following Salary Components first:<br><br>{0}"
				).format(
					"<br>".join(
						f"• {frappe.bold(component_name)}"
						for component_name in sorted(unmapped_statutory_components)
					)
				),
				title=_("Missing SARS Payroll Codes"),
			)

		previous_submission = 0
		if getdate(self.submission_period_start_date).month not in ETI_RECONCILIATION_OPENING_MONTHS:
			previous_month_date = add_months(self.submission_period_start_date, -1)
			previous_submission = frappe.db.get_value(
				"EMP201 Submission",
				{
					"company": self.company,
					"submission_period_start_date": get_first_day(previous_month_date),
					"docstatus": 1,
				},
				"eti_to_be_carried_forward",
			)

		eti_values = calculate_eti_utilisation(
			gross_paye,
			eti_generated,
			previous_submission,
			self.submission_period_start_date,
		)

		# Return a dictionary of calculated values
		return {
			"gross_paye_before_eti": gross_paye,
			"eti_carried_forward_from_previous": eti_values.eti_carried_forward_from_previous,
			"eti_generated_current_month": eti_generated,
			"total_eti_available": eti_values.total_eti_available,
			"eti_utilized_current_month": eti_values.eti_utilized_current_month,
			"net_paye_payable": eti_values.net_paye_payable,
			"eti_to_be_carried_forward": eti_values.eti_to_be_carried_forward,
			"eti_reconciliation_refund": eti_values.eti_reconciliation_refund,
			"uif_payable": uif,
			"sdl_payable": sdl,
		}

	def on_submit(self):
		self.db_set("status", "Submitted", update_modified=False)

	def on_cancel(self):
		cancelled_key = hashlib.sha256(f"{self.submission_key}|cancelled|{self.name}".encode()).hexdigest()
		self.db_set("submission_key", cancelled_key, update_modified=False)
		self.db_set("status", "Cancelled", update_modified=False)
