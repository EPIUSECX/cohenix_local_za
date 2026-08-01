import json
from itertools import pairwise

import frappe
from frappe import _  # Ensure _ is imported for translations
from frappe.model.document import Document
from frappe.utils import add_days, add_months, escape_html, flt, get_first_day, get_last_day, getdate

from za_local.sa_payroll.doctype.irp5_certificate.irp5_certificate import (
	get_active_certificate_names,
	require_certificate_generation_permissions,
)

DIRECTIVE_INCOME_CODES = {
	"3901",
	"3907",
	"3908",
	"3909",
	"3915",
	"3920",
	"3921",
	"3922",
	"3923",
	"3924",
	"3926",
}
DIRECTIVE_DEDUCTION_CODES = {"4115"}
TOTAL_TOLERANCE = 0.01


def _get_reconciliation_period_dates(tax_year, reconciliation_period):
	try:
		fiscal_year = frappe.get_doc("Fiscal Year", tax_year)
	except frappe.DoesNotExistError:
		frappe.throw(_("Fiscal Year {0} not found.").format(tax_year), title=_("Invalid Tax Year"))

	from_date = getdate(fiscal_year.year_start_date)
	fiscal_year_end = getdate(fiscal_year.year_end_date)
	expected_year_end = add_days(add_months(from_date, 12), -1)
	if (from_date.month, from_date.day) != (3, 1) or fiscal_year_end != expected_year_end:
		frappe.throw(
			_(
				"Fiscal Year {0} must run from 1 March to the last day of February for SARS reconciliation."
			).format(tax_year),
			title=_("Invalid South African Tax Year"),
		)

	if reconciliation_period == "Interim":
		to_date = add_days(add_months(from_date, 6), -1)
	elif reconciliation_period == "Final":
		to_date = fiscal_year_end
	else:
		frappe.throw(_("Invalid Reconciliation Period selected."), title=_("Validation Error"))

	return from_date, to_date


@frappe.whitelist()
def get_company_tax_details(company):
	# frappe.db.get_value does no permission check; these are the company's SARS
	# PAYE/SDL/UIF registration numbers.
	if not frappe.has_permission("Company", "read", company):
		frappe.throw(
			_("You are not permitted to read {0}.").format(company),
			frappe.PermissionError,
			title=_("Insufficient Permission"),
		)

	details = frappe.db.get_value(
		"Company",
		company,
		["za_paye_reference_number", "za_sdl_reference_number", "za_uif_reference_number"],
		as_dict=True,
	)
	return details


@frappe.whitelist()
def get_period_dates(tax_year, reconciliation_period):
	from_date, to_date = _get_reconciliation_period_dates(tax_year, reconciliation_period)
	return {"from_date": from_date, "to_date": to_date}


class EMP501Reconciliation(Document):
	def validate(self):
		self.validate_dates()  # This should be called after tax_year and reconciliation_period are set
		self.calculate_totals()

	def _get_expected_emp201_period_starts(self):
		if not self.from_date or not self.to_date:
			return []

		expected_starts = []
		period_start = get_first_day(self.from_date)
		period_end = get_first_day(self.to_date)

		while getdate(period_start) <= getdate(period_end):
			expected_starts.append(getdate(period_start))
			period_start = add_months(period_start, 1)

		return expected_starts

	def validate_emp201_period_coverage(self, throw=False):
		if not self.company or not self.from_date or not self.to_date:
			return {"missing_periods": [], "duplicate_periods": [], "linked_submissions": []}

		expected_starts = self._get_expected_emp201_period_starts()
		if not expected_starts:
			return {"missing_periods": [], "duplicate_periods": [], "linked_submissions": []}

		submissions = frappe.get_all(
			"EMP201 Submission",
			filters={
				"company": self.company,
				"docstatus": 1,
				"submission_period_start_date": ["in", expected_starts],
			},
			fields=["name", "submission_period_start_date"],
		)
		found_starts = {
			getdate(submission.submission_period_start_date)
			for submission in submissions
			if submission.submission_period_start_date
		}
		missing_periods = [period for period in expected_starts if getdate(period) not in found_starts]
		period_counts = {}
		for submission in submissions:
			period = getdate(submission.submission_period_start_date)
			period_counts[period] = period_counts.get(period, 0) + 1
		duplicate_periods = sorted(period for period, count in period_counts.items() if count > 1)

		if throw and (missing_periods or duplicate_periods):
			details = []
			if missing_periods:
				details.append(
					_("Missing: {0}").format(
						", ".join(frappe.utils.formatdate(period, "MMM YYYY") for period in missing_periods)
					)
				)
			if duplicate_periods:
				details.append(
					_("Duplicate submitted declarations: {0}").format(
						", ".join(frappe.utils.formatdate(period, "MMM YYYY") for period in duplicate_periods)
					)
				)
			frappe.throw(
				_(
					"Exactly one submitted EMP201 declaration is required for each month of the EMP501 period:<br><br>{0}"
				).format("<br>".join(f"• {escape_html(detail)}" for detail in details)),
				title=_("Invalid EMP201 Coverage"),
			)

		return {
			"missing_periods": missing_periods,
			"duplicate_periods": duplicate_periods,
			"linked_submissions": submissions,
		}

	def validate_submission_readiness(self):
		missing = []
		for label, value in [
			(_("PAYE Reference Number"), self.paye_reference_number),
			(_("SDL Reference Number"), self.sdl_reference_number),
			(_("UIF Reference Number"), self.uif_reference_number),
		]:
			if not value:
				missing.append(label)

		if missing:
			frappe.throw(
				_("The company is missing required SARS employer references:<br><br>{0}").format(
					"<br>".join(f"• {frappe.bold(label)}" for label in missing)
				),
				title=_("Missing Employer References"),
			)

	def _get_salary_slip_employees(self):
		if not self.company or not self.from_date or not self.to_date:
			return {}

		salary_slips = frappe.get_all(
			"Salary Slip",
			filters={
				"company": self.company,
				"end_date": ["between", [self.from_date, self.to_date]],
				"docstatus": 1,
			},
			fields=["employee", "employee_name"],
		)
		return {slip.employee: slip.employee_name for slip in salary_slips if slip.employee}

	def validate_irp5_coverage(self):
		expected_employees = self._get_salary_slip_employees()
		if not expected_employees:
			frappe.throw(
				_("No submitted salary slips were found for this reconciliation period."),
				title=_("Salary Slips Required"),
			)

		certificate_names = [
			row.irp5_certificate for row in self.irp5_certificates or [] if row.irp5_certificate
		]
		certificate_rows = (
			frappe.get_all(
				"IRP5 Certificate",
				filters={"name": ["in", certificate_names]},
				fields=[
					"name",
					"employee",
					"company",
					"tax_year",
					"reconciliation_period",
					"from_date",
					"to_date",
					"docstatus",
					"status",
				],
			)
			if certificate_names
			else []
		)
		certificates_by_name = {certificate.name: certificate for certificate in certificate_rows}

		linked_certificates = {}
		draft_or_missing_status = []
		invalid_references = []
		seen_certificate_names = set()
		for row in self.irp5_certificates or []:
			if not row.employee or not row.irp5_certificate:
				continue
			if row.irp5_certificate in seen_certificate_names:
				invalid_references.append(
					_("Certificate {0} is linked more than once").format(row.irp5_certificate)
				)
				continue
			seen_certificate_names.add(row.irp5_certificate)

			certificate = certificates_by_name.get(row.irp5_certificate)
			if not certificate:
				draft_or_missing_status.append(row.employee_name or row.employee)
				continue
			if certificate.docstatus != 1 or certificate.status != "Submitted":
				draft_or_missing_status.append(row.employee_name or row.employee)
				continue
			if row.employee != certificate.employee:
				invalid_references.append(
					_("Certificate {0} belongs to employee {1}, not {2}").format(
						certificate.name,
						certificate.employee,
						row.employee,
					)
				)
				continue
			if any(
				[
					certificate.company != self.company,
					certificate.tax_year != self.tax_year,
					certificate.reconciliation_period != self.reconciliation_period,
					getdate(certificate.from_date) != getdate(self.from_date),
					getdate(certificate.to_date) != getdate(self.to_date),
				]
			):
				invalid_references.append(
					_("Certificate {0} does not belong to this company, tax year, and period").format(
						certificate.name
					)
				)
				continue
			if certificate.employee in linked_certificates:
				invalid_references.append(
					_("Employee {0} has more than one linked certificate").format(certificate.employee)
				)
				continue
			linked_certificates[row.employee] = row.irp5_certificate

		missing_employees = [
			employee_name
			for employee, employee_name in expected_employees.items()
			if employee not in linked_certificates
		]

		if missing_employees or draft_or_missing_status or invalid_references:
			details = []
			if missing_employees:
				details.append(
					_("Missing IRP5/IT3(a) certificate references for: {0}").format(
						", ".join(sorted(missing_employees))
					)
				)
			if draft_or_missing_status:
				details.append(
					_("Draft, invalid, or cancelled certificate references for: {0}").format(
						", ".join(sorted(set(draft_or_missing_status)))
					)
				)
			if invalid_references:
				details.extend(invalid_references)
			frappe.throw(
				_(
					"EMP501 cannot be submitted until every employee with submitted salary slips in the period has a valid IRP5/IT3(a) certificate.<br><br>{0}"
				).format("<br>".join(escape_html(detail) for detail in details)),
				title=_("Incomplete IRP5 Coverage"),
			)

	def validate_irp5_certificate_readiness(self):
		errors = []
		certificate_totals = frappe._dict(paye=0, uif=0, sdl=0, eti=0, tax_payable=0)

		for row in self.irp5_certificates or []:
			if not row.irp5_certificate or not frappe.db.exists("IRP5 Certificate", row.irp5_certificate):
				continue

			certificate = frappe.get_doc("IRP5 Certificate", row.irp5_certificate)
			label = certificate.employee_name or certificate.employee or certificate.name
			if certificate.docstatus != 1 or certificate.status != "Submitted":
				errors.append(_("{0}: certificate must be submitted before EMP501 submission").format(label))
				continue

			if hasattr(certificate, "validate_statutory_readiness"):
				missing = certificate.validate_statutory_readiness(throw=False)
				if missing:
					errors.append(
						_("{0}: missing SARS readiness fields: {1}").format(
							label,
							", ".join(sorted(set(missing))),
						)
					)

			missing_codes = []
			has_directive_income = False
			for income_row in certificate.income_details or []:
				if flt(income_row.amount) and not income_row.income_code:
					missing_codes.append(_("income line code"))
				if income_row.income_code in DIRECTIVE_INCOME_CODES:
					has_directive_income = True

			has_directive_tax = False
			for deduction_row in certificate.deduction_details or []:
				if flt(deduction_row.amount) and not deduction_row.deduction_code:
					missing_codes.append(_("deduction line code"))
				if deduction_row.deduction_code in DIRECTIVE_DEDUCTION_CODES:
					has_directive_tax = True

			for contribution_row in certificate.company_contribution_details or []:
				if flt(contribution_row.amount) and not contribution_row.contribution_code:
					missing_codes.append(_("employer contribution line code"))

			if missing_codes:
				errors.append(
					_("{0}: missing SARS payroll code on {1}").format(
						label,
						", ".join(sorted(set(missing_codes))),
					)
				)

			if (has_directive_income or has_directive_tax) and not certificate.directive_numbers:
				errors.append(
					_("{0}: directive income or tax exists but no directive number is recorded").format(label)
				)

			expected_tax_payable = flt(certificate.paye) + flt(certificate.uif) + flt(certificate.sdl)
			if abs(flt(certificate.total_tax_payable) - expected_tax_payable) > TOTAL_TOLERANCE:
				errors.append(
					_("{0}: certificate code 4149 does not reconcile to PAYE + UIF + SDL").format(label)
				)

			certificate_totals.paye += flt(certificate.paye)
			certificate_totals.uif += flt(certificate.uif)
			certificate_totals.sdl += flt(certificate.sdl)
			certificate_totals.eti += flt(certificate.eti)
			certificate_totals.tax_payable += flt(certificate.total_tax_payable)

		if errors:
			frappe.throw(
				_(
					"EMP501 cannot be submitted until linked IRP5/IT3(a) certificates are filing-ready:<br><br>{0}"
				).format("<br>".join(f"• {frappe.bold(escape_html(error))}" for error in errors)),
				title=_("IRP5 Certificate Readiness Required"),
			)

		return certificate_totals

	def _get_linked_emp201_rows(self):
		names = [row.emp201_submission for row in self.emp201_submissions or [] if row.emp201_submission]
		if not names:
			return []

		return frappe.get_all(
			"EMP201 Submission",
			filters={"name": ["in", names], "docstatus": 1},
			fields=[
				"name",
				"submission_period_start_date",
				"gross_paye_before_eti",
				"uif_payable",
				"sdl_payable",
				"eti_carried_forward_from_previous",
				"eti_generated_current_month",
				"eti_utilized_current_month",
				"eti_to_be_carried_forward",
				"eti_reconciliation_refund",
			],
			order_by="submission_period_start_date, name",
		)

	def validate_linked_emp201_references(self):
		coverage = self.validate_emp201_period_coverage(throw=False)
		if coverage["duplicate_periods"]:
			frappe.throw(
				_("Duplicate submitted EMP201 declarations exist in this reconciliation period."),
				title=_("Invalid EMP201 Coverage"),
			)
		expected_names = {row.name for row in coverage["linked_submissions"]}
		linked_names = [
			row.emp201_submission for row in self.emp201_submissions or [] if row.emp201_submission
		]
		duplicate_names = sorted({name for name in linked_names if linked_names.count(name) > 1})
		actual_names = {row.name for row in self._get_linked_emp201_rows()}
		missing_names = sorted(expected_names - actual_names)
		unexpected_names = sorted(actual_names - expected_names)

		if duplicate_names or missing_names or unexpected_names:
			details = []
			if duplicate_names:
				details.append(_("Duplicate EMP201 references: {0}").format(", ".join(duplicate_names)))
			if missing_names:
				details.append(_("Missing linked EMP201 declarations: {0}").format(", ".join(missing_names)))
			if unexpected_names:
				details.append(
					_("EMP201 declarations outside this period: {0}").format(", ".join(unexpected_names))
				)
			frappe.throw(
				_("Linked EMP201 declarations are incomplete or inconsistent:<br><br>{0}").format(
					"<br>".join(f"• {escape_html(detail)}" for detail in details)
				),
				title=_("Invalid EMP201 References"),
			)

	def validate_certificate_reconciliation(self, certificate_totals):
		emp201_rows = self._get_linked_emp201_rows()
		if not emp201_rows:
			frappe.throw(_("No submitted EMP201 declarations are linked to this reconciliation."))

		emp201_totals = frappe._dict(
			paye=sum(flt(row.gross_paye_before_eti) for row in emp201_rows),
			uif=sum(flt(row.uif_payable) for row in emp201_rows),
			sdl=sum(flt(row.sdl_payable) for row in emp201_rows),
			eti_generated=sum(flt(row.eti_generated_current_month) for row in emp201_rows),
			eti_utilized=sum(flt(row.eti_utilized_current_month) for row in emp201_rows),
		)

		errors = []
		comparisons = [
			(_("PAYE"), certificate_totals.paye, emp201_totals.paye),
			(_("UIF"), certificate_totals.uif, emp201_totals.uif),
			(_("SDL"), certificate_totals.sdl, emp201_totals.sdl),
			(_("ETI calculated (4118)"), certificate_totals.eti, emp201_totals.eti_generated),
		]
		for label, certificate_value, emp201_value in comparisons:
			if abs(flt(certificate_value) - flt(emp201_value)) > TOTAL_TOLERANCE:
				errors.append(
					_("{0}: certificates {1}, EMP201 declarations {2}").format(
						label,
						frappe.format_value(certificate_value, {"fieldtype": "Currency"}),
						frappe.format_value(emp201_value, {"fieldtype": "Currency"}),
					)
				)

		for previous_row, current_row in pairwise(emp201_rows):
			if (
				abs(
					flt(current_row.eti_carried_forward_from_previous)
					- flt(previous_row.eti_to_be_carried_forward)
				)
				> TOTAL_TOLERANCE
			):
				errors.append(
					_("ETI carry-forward does not flow from {0} to {1}").format(
						previous_row.name,
						current_row.name,
					)
				)

		opening_eti = flt(emp201_rows[0].eti_carried_forward_from_previous)
		closing_eti = flt(emp201_rows[-1].eti_to_be_carried_forward)
		refund_eti = sum(flt(row.eti_reconciliation_refund) for row in emp201_rows)
		expected_utilized = opening_eti + emp201_totals.eti_generated - closing_eti - refund_eti
		if abs(expected_utilized - emp201_totals.eti_utilized) > TOTAL_TOLERANCE:
			errors.append(
				_(
					"ETI utilisation does not reconcile: opening carry-forward + generated - closing carry-forward - reconciliation refunds must equal utilised."
				)
			)

		if errors:
			frappe.throw(
				_("EMP501 does not reconcile to the submitted employee certificates:<br><br>{0}").format(
					"<br>".join(f"• {frappe.bold(escape_html(error))}" for error in errors)
				),
				title=_("EMP501 Reconciliation Difference"),
			)

		return emp201_totals

	def validate_dates(self):
		"""
		Validate date ranges for EMP501 Reconciliation based on selected Tax Year and Period.
		Also sets from_date and to_date if they are not already set.
		"""
		if not self.tax_year:
			frappe.throw(_("Tax Year must be selected first."), title=_("Missing Tax Year"))

		if not self.reconciliation_period:
			frappe.throw(
				_("Reconciliation Period must be selected."), title=_("Missing Reconciliation Period")
			)

		expected_from_date, expected_to_date = _get_reconciliation_period_dates(
			self.tax_year,
			self.reconciliation_period,
		)

		# If from_date is not set, auto-populate it
		if not self.from_date:
			self.from_date = expected_from_date
		elif getdate(self.from_date) != expected_from_date:
			frappe.throw(
				_(
					"From Date {0} does not match expected start date {1} for Tax Year {2} and {3} period."
				).format(
					frappe.utils.formatdate(self.from_date),
					frappe.utils.formatdate(expected_from_date),
					self.tax_year,
					self.reconciliation_period,
				),
				title=_("Invalid From Date"),
			)

		# If to_date is not set, auto-populate it
		if not self.to_date:
			self.to_date = expected_to_date
		elif getdate(self.to_date) != expected_to_date:
			frappe.throw(
				_("To Date {0} does not match expected end date {1} for Tax Year {2} and {3} period.").format(
					frappe.utils.formatdate(self.to_date),
					frappe.utils.formatdate(expected_to_date),
					self.tax_year,
					self.reconciliation_period,
				),
				title=_("Invalid To Date"),
			)

	def calculate_totals(self):
		emp201_rows = self._get_linked_emp201_rows()
		self.total_paye = sum(flt(row.gross_paye_before_eti) for row in emp201_rows)
		self.total_sdl = sum(flt(row.sdl_payable) for row in emp201_rows)
		self.total_uif = sum(flt(row.uif_payable) for row in emp201_rows)
		self.total_eti = sum(flt(row.eti_utilized_current_month) for row in emp201_rows)

		self.total_tax_payable = self.total_paye + self.total_sdl + self.total_uif - self.total_eti

	def before_submit(self):
		"""
		Validate that EMP501 is ready for submission.
		EMP201 monthly declarations are a hard prerequisite for reconciliation.
		"""
		if not self.irp5_certificates or len(self.irp5_certificates) == 0:
			frappe.throw(
				_(
					"Please generate IRP5 certificates before submitting. Click 'Generate IRP5 Certificates' button in the Actions menu."
				),
				title=_("IRP5 Certificates Required"),
			)

		self.validate_submission_readiness()
		self.validate_emp201_period_coverage(throw=True)
		self.validate_linked_emp201_references()
		self.calculate_totals()
		self.validate_irp5_coverage()
		certificate_totals = self.validate_irp5_certificate_readiness()
		self.validate_certificate_reconciliation(certificate_totals)

	def on_submit(self):
		self.db_set("status", "Submitted", update_modified=False)

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)
		frappe.msgprint(_("EMP501 Reconciliation {0} has been cancelled.").format(self.name))

	@frappe.whitelist()
	def fetch_emp201_submissions(self):
		self.check_permission("write")
		if not self.from_date or not self.to_date:
			frappe.throw(
				_(
					"Please ensure Tax Year and Reconciliation Period are selected, then save to populate dates, or set From Date and To Date manually."
				),
				title=_("Missing Date Range"),
			)
		if not self.company:
			frappe.throw(_("Company is required to fetch EMP201 submissions"), title=_("Missing Company"))

		self.validate_submission_readiness()

		self.emp201_submissions = []

		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)

		try:
			emp201_docs = frappe.get_all(
				"EMP201 Submission",
				filters={
					"company": self.company,
					"docstatus": 1,
					"submission_period_start_date": [">=", from_date],
					"submission_period_end_date": ["<=", to_date],
				},
				fields=[
					"name",
					"submission_period_start_date as submission_date",
					"gross_paye_before_eti as paye",
					"sdl_payable as sdl",
					"uif_payable as uif",
					"eti_utilized_current_month as eti",
				],
			)
		except Exception as e:
			error_msg = str(e)
			if "Unknown column" in error_msg and "submission_period_start_date" in error_msg:
				frappe.throw(
					_(
						"The 'EMP201 Submission' Doctype seems to be missing 'submission_period_start_date' or 'submission_period_end_date'. Please check its definition."
					),
					title=_("Field Missing"),
				)
			frappe.log_error(frappe.get_traceback())
			frappe.throw(_("Error fetching EMP201 submissions: {0}").format(str(e)), title=_("Fetch Error"))

		count = 0
		for emp201_doc in emp201_docs:
			self.append(
				"emp201_submissions",
				{
					"emp201_submission": emp201_doc.name,
					"submission_date": emp201_doc.submission_date,
					"paye": emp201_doc.paye,
					"sdl": emp201_doc.sdl,
					"uif": emp201_doc.uif,
					"eti": emp201_doc.eti,
				},
			)
			count += 1

		self.calculate_totals()
		self.save(ignore_permissions=True)

		coverage = self.validate_emp201_period_coverage(throw=False)
		if coverage["missing_periods"] or coverage["duplicate_periods"]:
			coverage_details = []
			if coverage["missing_periods"]:
				coverage_details.append(
					_("Missing: {0}").format(
						", ".join(
							frappe.utils.formatdate(period, "MMM YYYY")
							for period in coverage["missing_periods"]
						)
					)
				)
			if coverage["duplicate_periods"]:
				coverage_details.append(
					_("Duplicates: {0}").format(
						", ".join(
							frappe.utils.formatdate(period, "MMM YYYY")
							for period in coverage["duplicate_periods"]
						)
					)
				)
			frappe.msgprint(
				_(
					"EMP201 coverage is incomplete or ambiguous for this reconciliation period:<br><br>{0}"
				).format("<br>".join(f"• {escape_html(detail)}" for detail in coverage_details)),
				title=_("Incomplete EMP201 Coverage"),
				indicator="orange",
			)

		return {
			"count": count,
			"missing_periods": [
				frappe.utils.formatdate(period, "MMM YYYY") for period in coverage["missing_periods"]
			],
			"duplicate_periods": [
				frappe.utils.formatdate(period, "MMM YYYY") for period in coverage["duplicate_periods"]
			],
			"message": _("{0} EMP201 submission(s) fetched successfully.").format(count)
			if count > 0
			else _("No EMP201 submissions found."),
		}

	@frappe.whitelist()
	def generate_irp5_certificates(self):
		"""
		Generate IRP5 Certificates in bulk for all employees with salary slips in the period.
		EMP201 monthly declarations must already exist for the whole reconciliation period.
		"""
		self.check_permission("write")
		require_certificate_generation_permissions()

		if not self.from_date or not self.to_date or not self.tax_year or not self.company:
			frappe.throw(_("Company, Tax Year, From Date, and To Date are required to generate IRP5s."))

		if not self.reconciliation_period:
			frappe.throw(_("Reconciliation Period is required to generate IRP5s."))

		self.validate_submission_readiness()
		self.validate_emp201_period_coverage(throw=True)

		# Ensure document is saved before generating certificates (needed for linking)
		if self.is_new() or (hasattr(self, "name") and self.name and self.name.startswith("new-")):
			# Save the document first to get a proper name
			self.save(ignore_permissions=True)

		unique_employees = self._get_salary_slip_employees()

		if not unique_employees:
			frappe.msgprint(
				_("No salary slips found for the selected period. Cannot generate IRP5 certificates."),
				indicator="orange",
			)
			return {"created": 0, "updated": 0, "errors": 0, "message": "No salary slips found"}

		# Clear existing references (will be regenerated)
		self.irp5_certificates = []

		created_count = 0
		updated_count = 0
		reused_count = 0
		errors = []

		for emp_id, emp_name in unique_employees.items():
			try:
				existing_certificates = get_active_certificate_names(
					{
						"employee": emp_id,
						"tax_year": self.tax_year,
						"company": self.company,
						"reconciliation_period": self.reconciliation_period,
					}
				)
				if len(existing_certificates) > 1:
					frappe.throw(
						_(
							"Multiple active certificates exist for {0}. Cancel the duplicate before generating again."
						).format(emp_name),
						title=_("Duplicate IRP5 Certificates"),
					)
				existing_cert_name = existing_certificates[0] if existing_certificates else None

				if existing_cert_name:
					# Update existing certificate
					cert = frappe.get_doc("IRP5 Certificate", existing_cert_name)

					# Only update if certificate is not submitted
					if cert.docstatus == 1:
						self.append(
							"irp5_certificates",
							{
								"irp5_certificate": existing_cert_name,
								"employee": emp_id,
								"employee_name": emp_name,
								"status": cert.status,
							},
						)
						reused_count += 1
						continue

					# Update certificate fields
					cert.from_date = self.from_date
					cert.to_date = self.to_date
					# Only update emp501_reconciliation if it's not already set or if it's different
					if not cert.emp501_reconciliation or cert.emp501_reconciliation != self.name:
						cert.emp501_reconciliation = self.name
					# Regenerate certificate data to ensure it's up to date
					cert.generate_certificate_data()
					cert.save(ignore_permissions=True)
					cert_status = cert.status
					irp5_cert_name = cert.name
					updated_count += 1
				else:
					# Create new certificate
					cert = frappe.new_doc("IRP5 Certificate")
					cert.employee = emp_id
					cert.tax_year = self.tax_year
					cert.company = self.company
					cert.from_date = self.from_date
					cert.to_date = self.to_date
					cert.reconciliation_period = self.reconciliation_period
					cert.emp501_reconciliation = self.name
					# Generate certificate data from salary slips
					cert.generate_certificate_data()
					# Validate before inserting
					cert.validate()
					cert.insert(ignore_permissions=True)
					# Refresh to get the actual saved document
					cert.reload()
					cert_status = cert.status
					irp5_cert_name = cert.name
					created_count += 1

				# Verify certificate exists in database before adding to child table
				if irp5_cert_name:
					# Double-check that the certificate actually exists
					cert_exists = frappe.db.exists("IRP5 Certificate", irp5_cert_name)
					if cert_exists:
						self.append(
							"irp5_certificates",
							{
								"irp5_certificate": irp5_cert_name,
								"employee": emp_id,
								"employee_name": emp_name,
								"status": cert_status,
							},
						)
					else:
						# Certificate was supposed to be created but doesn't exist
						error_msg = f"Certificate {irp5_cert_name} was created but not found in database"
						frappe.log_error(
							title=f"IRP5 Certificate Missing - {emp_name}",
							message=error_msg,
						)
						errors.append(
							{
								"employee": emp_name,
								"error": "Certificate creation failed - certificate not found in database",
							}
						)

			except Exception as e:
				# Log full traceback for debugging
				error_traceback = frappe.get_traceback()
				error_msg = f"Failed to process IRP5 for employee {emp_name} ({emp_id}): {e!s}"
				frappe.log_error(
					title=f"IRP5 Generation Error - {emp_name}",
					message=error_traceback,
				)
				# Include more details in error message
				error_details = {
					"employee": emp_name,
					"employee_id": emp_id,
					"error": str(e),
					"error_type": type(e).__name__,
				}
				errors.append(error_details)
				# Don't add to child table if certificate creation failed
				continue

		# Save EMP501 with updated IRP5 references
		self.save(ignore_permissions=True)

		# Prepare summary message
		total_processed = created_count + updated_count + reused_count
		message = _(
			"{0} IRP5 certificates processed. {1} newly created, {2} updated, {3} already submitted and reused."
		).format(total_processed, created_count, updated_count, reused_count)

		if errors:
			error_details = "\n".join(
				f"- {escape_html(e.get('employee', 'Unknown'))}: "
				f"{escape_html(e.get('error', 'Unknown error'))}"
				for e in errors[:5]
			)  # Show first 5 errors
			if len(errors) > 5:
				error_details += f"\n... and {len(errors) - 5} more errors"
			message += _(" {0} errors encountered.").format(len(errors))
			full_error_message = (
				message + "<br><br><b>Error Details:</b><br>" + error_details.replace("\n", "<br>")
			)
			frappe.msgprint(full_error_message, indicator="orange", title=_("IRP5 Generation Complete"))
		else:
			frappe.msgprint(message, indicator="green", title=_("IRP5 Generation Complete"))

		return {
			"created": created_count,
			"updated": updated_count,
			"errors": errors,  # Return full error details, not just count
			"error_count": len(errors),
			"reused": reused_count,
			"total": total_processed,
			"message": message,
		}

	@frappe.whitelist()
	def submit_to_sars(self):
		frappe.throw(
			_(
				"Direct SARS electronic submission is not supported in this release. "
				"Use SARS eFiling for up to 50 certificates or an approved e@syFile-compatible payroll export."
			),
			title=_("Manual Filing Required"),
		)
