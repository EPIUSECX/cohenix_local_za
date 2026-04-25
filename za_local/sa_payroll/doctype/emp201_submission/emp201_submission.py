# Copyright (c) 2024, Kartoza and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, get_first_day, get_last_day, getdate

PAYE_CODES = {"4102"}
UIF_CODES = {"4141"}
SDL_CODES = {"4142"}
ETI_CODES = {"4118"}


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


class EMP201Submission(Document):
	# Main class for EMP201 Submission
	def validate(self):
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

	@frappe.whitelist()
	def set_submission_period_dates(self):
		if self.month and self.fiscal_year:
			year = int(self.fiscal_year.split("-")[0])
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
			}[self.month]

			# Adjust year for months that fall in the next calendar year of the fiscal year
			if month_number < 3:  # Jan & Feb belong to the previous fiscal year's start
				year += 1

			start_date = get_first_day(f"{year}-{month_number}-01")
			end_date = get_last_day(f"{year}-{month_number}-01")

			self.submission_period_start_date = start_date
			self.submission_period_end_date = end_date

			return {"submission_period_start_date": start_date, "submission_period_end_date": end_date}

	@frappe.whitelist()
	def fetch_emp201_data(self):
		from frappe.utils import flt, get_first_day

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
				"start_date": [">=", self.submission_period_start_date],
				"end_date": ["<=", self.submission_period_end_date],
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

		# Get previous month's ETI carried forward
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

		eti_carried_forward_from_previous = flt(previous_submission)
		total_eti_available = eti_carried_forward_from_previous + eti_generated
		eti_utilized = min(gross_paye, total_eti_available)
		net_paye = gross_paye - eti_utilized
		eti_to_be_carried_forward = total_eti_available - eti_utilized

		# Return a dictionary of calculated values
		return {
			"gross_paye_before_eti": gross_paye,
			"eti_carried_forward_from_previous": eti_carried_forward_from_previous,
			"eti_generated_current_month": eti_generated,
			"total_eti_available": total_eti_available,
			"eti_utilized_current_month": eti_utilized,
			"net_paye_payable": net_paye,
			"eti_to_be_carried_forward": eti_to_be_carried_forward,
			"uif_payable": uif,
			"sdl_payable": sdl,
		}

	def on_submit(self):
		self.status = "Submitted"

	def on_cancel(self):
		self.status = "Cancelled"
