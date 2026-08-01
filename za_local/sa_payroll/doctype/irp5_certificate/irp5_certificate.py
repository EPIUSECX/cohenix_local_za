import base64
import hashlib
import json
from collections import defaultdict
from io import BytesIO

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, escape_html, flt, getdate, today

from za_local.utils.statutory_rates import get_rate_pack

pdf_generation_available = False
try:
	from reportlab.lib.colors import black
	from reportlab.pdfbase import pdfmetrics
	from reportlab.pdfbase.ttfonts import TTFont
	from reportlab.pdfgen import canvas

	pdf_generation_available = True
except ImportError:
	frappe.log_error(
		"PDF generation libraries not installed. Install PyPDF2 and reportlab for IRP5 functionality.",
	)

try:
	from za_local.sa_payroll.doctype.tax_directive.tax_directive import get_active_directive
except Exception:  # pragma: no cover - defensive import
	get_active_directive = None


MEDICAL_SCHEME_TAX_CREDIT_CODE = "4116"
ADDITIONAL_MEDICAL_EXPENSES_TAX_CREDIT_CODE = "4120"
VALID_IT3A_REASON_CODES = {"02", "03", "04", "05", "06", "07", "08", "09", "10"}
PAY_PERIODS_PER_YEAR = {
	"Monthly": 12,
	"Bimonthly": 24,
	"Fortnightly": 26,
	"Weekly": 52,
}


def build_certificate_key(
	company,
	employee,
	tax_year,
	reconciliation_period,
):
	"""Return the canonical identity for one employee certificate period."""
	parts = [
		company or "",
		employee or "",
		tax_year or "",
		reconciliation_period or "",
	]
	return hashlib.sha256("|".join(str(value).strip() for value in parts).encode()).hexdigest()


def get_active_certificate_names(filters):
	"""Return at most two active matches so legacy duplicates fail deterministically."""
	return frappe.get_all(
		"IRP5 Certificate",
		filters={**filters, "docstatus": ["<", 2]},
		pluck="name",
		order_by="docstatus desc, modified desc, creation desc, name desc",
		limit=2,
	)


def require_certificate_generation_permissions():
	"""Generation may create new certificates and replace draft snapshots."""
	for permission_type in ("create", "write"):
		if not frappe.has_permission("IRP5 Certificate", permission_type):
			frappe.throw(
				_("You are not permitted to generate or update IRP5 certificates."),
				frappe.PermissionError,
				title=_("Insufficient Permission"),
			)


class IRP5Certificate(Document):
	def autoname(self):
		self.set_certificate_key()
		if getattr(self, "generation_mode", None) == "Bulk":
			if not self.certificate_number:
				self.set_bulk_certificate_number()
		elif self.employee and self.tax_year and not self.certificate_number:
			self.set_certificate_number()

		if self.certificate_number:
			self.name = self.certificate_number

	def validate(self):
		if not self.status:
			self.status = "Draft"
		if not self.issue_date:
			self.issue_date = today()

		if getattr(self, "generation_mode", None) == "Bulk":
			if not self.tax_year or not self.from_date or not self.to_date or not self.reconciliation_period:
				frappe.throw(
					_(
						"Tax Year, From Date, To Date, and Reconciliation Period are required for Bulk generation."
					),
					title=_("Missing Required Fields"),
				)
			if not self.certificate_number:
				self.set_bulk_certificate_number()
		else:
			if not self.employee:
				frappe.throw(_("Employee is required"), title=_("Missing Employee"))
			self.validate_employee()
			if self.employee and self.tax_year and not self.certificate_number:
				self.set_certificate_number()

		self.validate_dates()
		self.set_certificate_key()

	def set_certificate_key(self):
		if not all(
			[
				self.company,
				self.employee,
				self.tax_year,
				self.reconciliation_period,
			]
		):
			return

		self.certificate_key = build_certificate_key(
			self.company,
			self.employee,
			self.tax_year,
			self.reconciliation_period,
		)

	def validate_dates(self):
		if not self.from_date or not self.to_date:
			frappe.throw(_("Both From Date and To Date are required"), title=_("Missing Required Dates"))

		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)
		if from_date > to_date:
			frappe.throw(_("From Date cannot be after To Date"), title=_("Invalid Date Range"))

		if self.reconciliation_period == "Interim":
			if not (from_date.month == 3 and from_date.day == 1):
				frappe.throw(
					_("For Interim reconciliation, From Date must be March 1"),
					title=_("Invalid Interim Period Start Date"),
				)
			if not (to_date.month == 8 and to_date.day == 31):
				frappe.throw(
					_("For Interim reconciliation, To Date must be August 31"),
					title=_("Invalid Interim Period End Date"),
				)
		elif self.reconciliation_period == "Final":
			if not (from_date.month == 3 and from_date.day == 1):
				frappe.throw(
					_("For Final reconciliation, From Date must be March 1"),
					title=_("Invalid Final Period Start Date"),
				)
			expected_end_day = 29 if _is_leap_year(to_date.year) else 28
			if not (to_date.month == 2 and to_date.day == expected_end_day):
				frappe.throw(
					_("For Final reconciliation, To Date must be the last day of February"),
					title=_("Invalid Final Period End Date"),
				)

	def validate_employee(self):
		if not self.employee:
			return

		employee_data = frappe.db.get_value(
			"Employee",
			self.employee,
			["employee_name", "company"],
			as_dict=True,
		)
		if employee_data:
			self.employee_name = employee_data.employee_name
			if not self.company:
				self.company = employee_data.company

	def before_submit(self):
		self.calculate_totals()
		self.validate_statutory_readiness(throw=True)
		self.status = "Submitted"

	def on_cancel(self):
		if self.certificate_key:
			cancelled_key = hashlib.sha256(
				f"{self.certificate_key}|cancelled|{self.name}".encode()
			).hexdigest()
			self.db_set("certificate_key", cancelled_key, update_modified=False)
		self.db_set("status", "Cancelled", update_modified=False)
		frappe.msgprint(_("IRP5 Certificate {0} has been cancelled.").format(self.name))

	def set_certificate_number(self):
		if not self.employee or not self.tax_year:
			return

		prefix = "IRP5" if (self.certificate_type or "IRP5") == "IRP5" else "IT3A"
		tax_year_str = str(self.tax_year).replace("/", "-")
		unique_hash = frappe.generate_hash(length=8)
		self.certificate_number = f"{prefix}-{tax_year_str}-{self.employee}-{unique_hash}"

	def set_bulk_certificate_number(self):
		if not self.tax_year:
			return
		prefix = "IRP5" if (self.certificate_type or "IRP5") == "IRP5" else "IT3A"
		tax_year_str = str(self.tax_year).replace("/", "-")
		unique_hash = frappe.generate_hash(length=8)
		self.certificate_number = f"{prefix}-BULK-{tax_year_str}-{unique_hash}"

	def calculate_totals(self):
		# Employees' tax includes ordinary PAYE (4102) and lump-sum/directive tax
		# (4115), matching the EMP201 PAYE bucket so the EMP501 reconciliation ties
		# on a gross (pre-ETI) PAYE basis.
		self.paye = self._sum_child_table(self.deduction_details, "deduction_code", {"4102", "4115"})
		self.uif = self._sum_child_table(self.deduction_details, "deduction_code", {"4141"})
		self.uif += self._sum_child_table(
			self.company_contribution_details,
			"contribution_code",
			{"4141"},
		)
		self.sdl = self._sum_child_table(self.deduction_details, "deduction_code", {"4142"})
		self.sdl += self._sum_child_table(
			self.company_contribution_details,
			"contribution_code",
			{"4142"},
		)

		self.medical_scheme_fees_tax_credit = self._sum_child_table(
			self.deduction_details,
			"deduction_code",
			{MEDICAL_SCHEME_TAX_CREDIT_CODE},
		)
		self.additional_medical_expenses_tax_credit = self._sum_child_table(
			self.deduction_details,
			"deduction_code",
			{ADDITIONAL_MEDICAL_EXPENSES_TAX_CREDIT_CODE},
		)
		self.total_deductions_contributions = sum(
			flt(row.amount) for row in self.deduction_details if self._is_4497_detail_code(row.deduction_code)
		) + sum(
			flt(row.amount)
			for row in self.company_contribution_details
			if self._is_4497_detail_code(row.contribution_code)
		)
		# SARS code 4149 is tax (4102/4115) + combined UIF (4141) + SDL
		# (4142). Medical credits and ETI are explicitly excluded.
		self.total_tax_payable = self.paye + self.uif + self.sdl
		self._apply_certificate_tax_control()

	@staticmethod
	def _is_4497_detail_code(code):
		code = str(code or "")
		return code != "4497" and code.startswith(("40", "44", "45"))

	def _apply_certificate_tax_control(self):
		if flt(self.paye) > 0:
			self.certificate_type = "IRP5"
			self.reason_for_non_deduction = None
			return

		self.certificate_type = "IT3(a)"
		if flt(self.gross_taxable_income) > 0 and not self.reason_for_non_deduction:
			if self._annualized_taxable_income_is_below_threshold():
				# SARS reason code 02: employee earns less than the applicable
				# annual tax threshold. This is deterministic from the statutory
				# pack and certificate period snapshot, so practitioner input is
				# only required for the remaining reason codes.
				self.reason_for_non_deduction = "02"
				return

		if (
			flt(self.gross_taxable_income) == 0
			and flt(self.non_taxable_income) > 0
			and not self.reason_for_non_deduction
		):
			# SARS reason code 04: non-taxable earnings. Other cases require
			# an explicit practitioner-selected code.
			self.reason_for_non_deduction = "04"

	def _annualized_taxable_income_is_below_threshold(self):
		if not self.tax_year or not self.date_of_birth:
			return False

		periods_worked = flt(self.periods_worked)
		periods_in_year = flt(self.periods_in_year)
		if periods_worked <= 0 or periods_in_year <= 0:
			return False

		pack = get_rate_pack(tax_year=self.tax_year)
		tax_year_end = getdate(pack["effective_to"])
		date_of_birth = getdate(self.date_of_birth)
		age = tax_year_end.year - date_of_birth.year - (
			(tax_year_end.month, tax_year_end.day) < (date_of_birth.month, date_of_birth.day)
		)
		if age >= 75:
			threshold_key = "age_75_plus"
		elif age >= 65:
			threshold_key = "age_65_to_74"
		else:
			threshold_key = "under_65"

		annualized_taxable_income = flt(self.gross_taxable_income) * periods_in_year / periods_worked
		return annualized_taxable_income <= flt(pack["paye"]["thresholds"][threshold_key])

	@frappe.whitelist()
	def validate_statutory_readiness(self, throw=False):
		missing = []

		required_pairs = [
			("Employer PAYE Reference Number", self.employer_paye_reference_number),
			("Employer SDL Reference Number", self.employer_sdl_reference_number),
			("Employer UIF Reference Number", self.employer_uif_reference_number),
			("Employee identity type", self.identity_type),
			("Employee identity number", self.employee_id_number),
			("Residential address", self.res_address_line_1),
			("Employment start date", self.employed_from),
			("Periods in year", self.periods_in_year),
			("Periods worked", self.periods_worked),
		]
		for label, value in required_pairs:
			if not value:
				missing.append(label)

		reason_code = str(self.reason_for_non_deduction or "").zfill(2)
		ordinary_paye = self._sum_child_table(self.deduction_details, "deduction_code", {"4102"})
		lump_sum_tax = self._sum_child_table(self.deduction_details, "deduction_code", {"4115"})
		tax_reference_optional = (self.certificate_type == "IT3(a)" and reason_code in {"02", "04"}) or (
			self.certificate_type == "IRP5" and not ordinary_paye and lump_sum_tax
		)
		if not self.income_tax_reference_number and not tax_reference_optional:
			missing.append("Employee income tax reference number")

		if not self.not_paid_electronically:
			for label, value in [
				("Bank account number", self.bank_account_no),
				("Bank account type", self.bank_account_type),
				("Bank account holder name", self.bank_account_holder_name),
			]:
				if not value:
					missing.append(label)

		if not self.income_details:
			missing.append("Income line items")

		if not getattr(self, "_unmapped_salary_components", None) and not getattr(
			self, "_mapping_errors", None
		):
			pass
		else:
			missing.extend(sorted(set(getattr(self, "_unmapped_salary_components", []))))
			missing.extend(sorted(set(getattr(self, "_mapping_errors", []))))

		if flt(self.paye) > 0:
			if self.certificate_type != "IRP5":
				missing.append("Certificate Type must be IRP5 when employees' tax was deducted")
			if self.reason_for_non_deduction:
				missing.append("Reason code 4150 must be blank when employees' tax was deducted")
		else:
			if self.certificate_type != "IT3(a)":
				missing.append("Certificate Type must be IT3(a) when no employees' tax was deducted")
			if reason_code not in VALID_IT3A_REASON_CODES:
				missing.append("Valid SARS reason code 4150 (02-10)")
			else:
				self._validate_it3a_reason_code(reason_code, missing)

		self.missing_sars_data = "\n".join(f"- {item}" for item in missing)

		if throw and missing:
			frappe.throw(
				_(
					"Cannot generate or export this certificate until the following SARS fields are complete:<br><br>{0}"
				).format("<br>".join(f"• {frappe.bold(escape_html(item))}" for item in missing)),
				title=_("Missing SARS Data"),
			)

		return missing

	def _validate_it3a_reason_code(self, reason_code, missing):
		income_codes = {str(row.income_code or "") for row in self.income_details or []}
		deduction_codes = {str(row.deduction_code or "") for row in self.deduction_details or []}
		if reason_code == "03" and not income_codes.intersection({"3616", "3666", "3620", "3670"}):
			missing.append("Reason code 03 requires income code 3616/3666 or 3620/3670")
		elif reason_code == "04" and not (
			self.directive_numbers
			or (flt(self.non_taxable_income) > 0 and flt(self.gross_taxable_income) == 0)
		):
			missing.append("Reason code 04 requires directive information or only non-taxable income")
		elif reason_code == "08" and not deduction_codes.intersection({"4116", "4120"}):
			missing.append("Reason code 08 requires medical tax credit code 4116 or 4120")
		elif reason_code == "10" and not (income_codes == {"4588"} or "4042" in deduction_codes):
			missing.append("Reason code 10 requires only code 4588 or deduction code 4042")

	@frappe.whitelist()
	def generate_certificate_data(self):
		require_certificate_generation_permissions()
		if not self.employee:
			frappe.throw(_("Employee is required to generate certificate data."))
		if not self.company:
			frappe.throw(_("Company is required to generate certificate data."))
		if not self.tax_year or not self.from_date or not self.to_date or not self.reconciliation_period:
			frappe.throw(_("Tax Year, Reconciliation Period, From Date, and To Date are required."))

		self.validate_employee()

		self.issue_date = today()
		self._reset_snapshot()
		self._snapshot_master_data()
		counts = self._generate_certificate_lines()
		self.calculate_eti()
		self.calculate_totals()
		self.set_certificate_key()
		if not self.certificate_number:
			self.set_certificate_number()
		missing = self.validate_statutory_readiness(throw=False)
		if missing:
			frappe.throw(
				_(
					"IRP5 certificate data was not generated because required SARS data is missing:<br><br>{0}"
				).format("<br>".join(f"• {frappe.bold(escape_html(item))}" for item in missing)),
				title=_("Missing SARS Data"),
			)

		self.status = "Prepared"
		return {
			**counts,
			"certificate_number": self.certificate_number,
			"message": _("Certificate data generated successfully."),
		}

	def _reset_snapshot(self):
		for fieldname in [
			"year_of_assessment",
			"transaction_year",
			"reconciliation_period_yyyymm",
			"employer_legal_name",
			"employer_trading_name",
			"employer_tax_id",
			"employer_paye_reference_number",
			"employer_sdl_reference_number",
			"employer_uif_reference_number",
			"identity_type",
			"employee_id_number",
			"passport_country_of_issue",
			"employee_initials",
			"employee_first_names",
			"employee_surname",
			"employee_gender",
			"income_tax_reference_number",
			"nature_of_person",
			"res_address_line_1",
			"res_address_line_2",
			"res_address_line_3",
			"res_address_line_4",
			"res_postal_code",
			"post_address_line_1",
			"post_address_line_2",
			"post_address_line_3",
			"post_address_line_4",
			"post_postal_code",
			"biz_address_line_1",
			"biz_address_line_2",
			"biz_address_line_3",
			"biz_address_line_4",
			"biz_postal_code",
			"bank_name",
			"bank_account_no",
			"bank_account_type",
			"bank_account_holder_name",
			"bank_account_holder_relationship",
			"directive_numbers",
			"missing_sars_data",
		]:
			self.set(fieldname, None)

		for fieldname in [
			"gross_taxable_income",
			"non_taxable_income",
			"total_deductions_contributions",
			"medical_scheme_fees_tax_credit",
			"additional_medical_expenses_tax_credit",
			"paye",
			"uif",
			"sdl",
			"eti",
			"total_tax_payable",
			"periods_in_year",
			"periods_worked",
		]:
			self.set(fieldname, 0)

		self.set("income_details", [])
		self.set("deduction_details", [])
		self.set("company_contribution_details", [])
		self._unmapped_salary_components = []
		self._mapping_errors = []
		self._sars_code_cache = {}

	def _snapshot_master_data(self):
		employee = frappe.get_doc("Employee", self.employee)
		company = frappe.get_doc("Company", self.company)
		self.employee_name = employee.employee_name

		to_date = getdate(self.to_date)
		self.year_of_assessment = str(to_date.year)
		self.transaction_year = str(getdate(self.issue_date).year if self.issue_date else to_date.year)
		self.reconciliation_period_yyyymm = to_date.strftime("%Y%m")

		self.employer_legal_name = company.company_name
		self.employer_trading_name = company.get("za_trading_name") or company.company_name
		self.employer_tax_id = company.tax_id
		self.employer_paye_reference_number = company.get("za_paye_reference_number")
		self.employer_sdl_reference_number = company.get("za_sdl_reference_number")
		self.employer_uif_reference_number = company.get("za_uif_reference_number")

		self.identity_type = employee.get("za_identity_type") or (
			"South African ID" if employee.get("za_id_number") else "Passport"
		)
		self.employee_id_number = employee.get("za_id_number") or employee.get("passport_number")
		self.passport_number = employee.get("passport_number")
		self.passport_country_of_issue = employee.get("za_passport_country_of_issue")
		self.employee_first_names = (
			" ".join(
				part for part in [employee.get("first_name"), employee.get("middle_name")] if part
			).strip()
			or employee.employee_name
		)
		self.employee_surname = employee.get("last_name") or employee.employee_name
		self.employee_initials = _make_initials(
			employee.get("first_name"),
			employee.get("middle_name"),
		)
		self.employee_gender = employee.get("gender")
		self.date_of_birth = employee.get("date_of_birth")
		self.income_tax_reference_number = employee.get("za_income_tax_reference_number")
		self.nature_of_person = employee.get("za_nature_of_person") or "Individual"

		self._set_address_snapshot(
			"res",
			self._resolve_employee_residential_address(employee),
		)
		self._set_address_snapshot(
			"post",
			self._resolve_employee_postal_address(employee),
		)
		self._set_address_snapshot(
			"biz",
			self._resolve_business_address(employee, company),
		)

		bank_details = self._resolve_bank_details(employee)
		self.bank_name = bank_details.get("bank_name")
		self.bank_account_no = bank_details.get("bank_account_no")
		self.bank_account_type = bank_details.get("bank_account_type")
		self.bank_account_holder_name = bank_details.get("bank_account_holder_name")
		self.bank_account_holder_relationship = bank_details.get("bank_account_holder_relationship")
		self.not_paid_electronically = bank_details.get("not_paid_electronically", 0)

		self.employed_from = employee.get("date_of_joining") or self.from_date
		self.employed_to = employee.get("relieving_date") or self.to_date
		self.directive_numbers = self._get_directive_numbers()

	def _generate_certificate_lines(self):
		salary_slips = self._get_salary_slips(self.employee, self.from_date, self.to_date)
		if not salary_slips:
			frappe.throw(_("No salary slips found for this employee in the selected period."))

		self._set_pay_period_snapshot(salary_slips)

		income_map = defaultdict(lambda: {"description": "", "amount": 0.0})
		deduction_map = defaultdict(lambda: {"description": "", "amount": 0.0})
		contribution_map = defaultdict(lambda: {"description": "", "amount": 0.0})
		medical_credits = defaultdict(float)
		gross_taxable_income = 0.0
		non_taxable_income = 0.0

		for salary_slip in salary_slips:
			salary_slip_doc = frappe.get_doc("Salary Slip", salary_slip.name)

			for earning in salary_slip_doc.earnings:
				code_doc = self._get_sars_payroll_code(earning.salary_component)
				if not code_doc:
					continue
				if code_doc.category != "Income":
					self._mapping_errors.append(
						f"{earning.salary_component} is mapped to {code_doc.category}, but appears in salary slip earnings"
					)
					continue
				income_map[code_doc.code]["description"] = code_doc.description
				income_map[code_doc.code]["amount"] += flt(earning.amount)
				if code_doc.tax_treatment == "Taxable":
					gross_taxable_income += flt(earning.amount)
				elif code_doc.tax_treatment == "Non-Taxable":
					non_taxable_income += flt(earning.amount)
				elif code_doc.tax_treatment != "Reference":
					self._mapping_errors.append(
						f"{earning.salary_component} has unsupported tax treatment '{code_doc.tax_treatment}'"
					)

			for deduction in salary_slip_doc.deductions:
				code_doc = self._get_sars_payroll_code(deduction.salary_component)
				if not code_doc:
					continue
				if code_doc.category == "Tax Credit":
					medical_credits[code_doc.code] += flt(deduction.amount)
					deduction_map[code_doc.code]["description"] = code_doc.description
					deduction_map[code_doc.code]["amount"] += flt(deduction.amount)
					continue
				if code_doc.category != "Deduction":
					self._mapping_errors.append(
						f"{deduction.salary_component} is mapped to {code_doc.category}, but appears in salary slip deductions"
					)
					continue
				deduction_map[code_doc.code]["description"] = code_doc.description
				deduction_map[code_doc.code]["amount"] += flt(deduction.amount)

			for contribution in getattr(salary_slip_doc, "company_contribution", []) or []:
				component_name = getattr(contribution, "salary_component", None)
				if not component_name:
					continue
				code_doc = self._get_sars_payroll_code(component_name)
				if not code_doc:
					continue
				if code_doc.category not in {"Employer Contribution", "Deduction"}:
					self._mapping_errors.append(
						f"{component_name} is mapped to {code_doc.category}, but appears in company contributions"
					)
					continue
				contribution_map[code_doc.code]["description"] = code_doc.description
				contribution_map[code_doc.code]["amount"] += flt(contribution.amount)

		for code, details in sorted(
			income_map.items(),
			key=lambda item: self._sort_sars_code(item[0]),
		):
			self.append(
				"income_details",
				{
					"income_code": code,
					"description": details["description"],
					"amount": details["amount"],
					"tax_year": self.tax_year,
					"period": self.reconciliation_period,
				},
			)

		for code, details in sorted(
			deduction_map.items(),
			key=lambda item: self._sort_sars_code(item[0]),
		):
			self.append(
				"deduction_details",
				{
					"deduction_code": code,
					"description": details["description"],
					"amount": details["amount"],
					"tax_year": self.tax_year,
					"period": self.reconciliation_period,
				},
			)

		for code, details in sorted(
			contribution_map.items(),
			key=lambda item: self._sort_sars_code(item[0]),
		):
			self.append(
				"company_contribution_details",
				{
					"contribution_code": code,
					"description": details["description"],
					"amount": details["amount"],
				},
			)

		self.gross_taxable_income = gross_taxable_income
		self.non_taxable_income = non_taxable_income
		self.medical_scheme_fees_tax_credit = medical_credits.get(
			MEDICAL_SCHEME_TAX_CREDIT_CODE,
			0.0,
		)
		self.additional_medical_expenses_tax_credit = medical_credits.get(
			ADDITIONAL_MEDICAL_EXPENSES_TAX_CREDIT_CODE,
			0.0,
		)
		return {
			"income_count": len(income_map),
			"deduction_count": len(deduction_map),
			"contribution_count": len(contribution_map),
		}

	def _get_salary_slips(self, employee, from_date, to_date):
		return frappe.get_all(
			"Salary Slip",
			filters={
				"employee": employee,
				"end_date": ["between", [getdate(from_date), getdate(to_date)]],
				"docstatus": 1,
			},
			fields=[
				"name",
				"start_date",
				"end_date",
				"payroll_frequency",
				"total_working_days",
				"payment_days",
			],
			order_by="start_date",
		)

	def _set_pay_period_snapshot(self, salary_slips):
		frequency = next(
			(slip.payroll_frequency for slip in salary_slips if slip.payroll_frequency),
			"Monthly",
		)
		if frequency == "Daily":
			fiscal_year = frappe.db.get_value(
				"Fiscal Year",
				self.tax_year,
				["year_start_date", "year_end_date"],
				as_dict=True,
			)
			self.periods_in_year = (
				(getdate(fiscal_year.year_end_date) - getdate(fiscal_year.year_start_date)).days + 1
				if fiscal_year
				else 365
			)
		else:
			self.periods_in_year = PAY_PERIODS_PER_YEAR.get(frequency, 12)

		period_fractions = {}
		for slip in salary_slips:
			end_date = getdate(slip.end_date)
			if frequency == "Monthly":
				period_key = (end_date.year, end_date.month)
			elif frequency == "Bimonthly":
				period_key = (end_date.year, end_date.month, 1 if end_date.day <= 15 else 2)
			else:
				period_key = slip.name

			total_days = flt(slip.total_working_days)
			payment_days = flt(slip.payment_days)
			fraction = min(1.0, max(0.0, payment_days / total_days)) if total_days else 1.0
			period_fractions[period_key] = max(period_fractions.get(period_key, 0.0), fraction)

		self.periods_worked = min(
			flt(self.periods_in_year),
			sum(period_fractions.values()),
		)

	def _get_sars_payroll_code(self, salary_component_name):
		cache = getattr(self, "_sars_code_cache", None)
		if cache is None:
			cache = self._sars_code_cache = {}
		if salary_component_name in cache:
			return cache[salary_component_name]

		component = (
			frappe.get_cached_value(
				"Salary Component",
				salary_component_name,
				["za_sars_payroll_code", "za_exclude_from_irp5"],
				as_dict=True,
			)
			or frappe._dict()
		)

		if component.get("za_exclude_from_irp5"):
			cache[salary_component_name] = None
			return None

		code = component.get("za_sars_payroll_code")
		if not code:
			self._unmapped_salary_components.append(
				f"Salary Component '{salary_component_name}' has no SARS Payroll Code"
			)
			cache[salary_component_name] = None
			return None
		try:
			code_doc = frappe.get_cached_doc("SARS Payroll Code", code)
		except frappe.DoesNotExistError:
			self._unmapped_salary_components.append(
				f"SARS Payroll Code '{code}' linked from Salary Component '{salary_component_name}' does not exist"
			)
			cache[salary_component_name] = None
			return None
		if not cint(code_doc.get("active", 1)):
			self._mapping_errors.append(
				f"Salary Component '{salary_component_name}' uses inactive SARS Payroll Code '{code}'"
			)
			cache[salary_component_name] = None
			return None

		cache[salary_component_name] = code_doc
		return code_doc

	def _resolve_employee_residential_address(self, employee):
		return self._resolve_address(
			employee.get("za_residential_address"),
			"Employee",
			employee.name,
			fallback_text=employee.get("current_address") or employee.get("permanent_address"),
		)

	def _resolve_employee_postal_address(self, employee):
		return self._resolve_address(
			employee.get("za_postal_address"),
			"Employee",
			employee.name,
			fallback_text=employee.get("current_address") or employee.get("permanent_address"),
		)

	def _resolve_business_address(self, employee, company):
		address_name = employee.get("za_business_address_override") or company.get("za_business_address")
		return self._resolve_address(address_name, "Company", company.name)

	def _resolve_address(
		self, explicit_address_name=None, link_doctype=None, link_name=None, fallback_text=None
	):
		if explicit_address_name and frappe.db.exists("Address", explicit_address_name):
			return {"type": "doc", "value": frappe.get_doc("Address", explicit_address_name)}

		if link_doctype and link_name:
			address_name = _get_primary_linked_address(link_doctype, link_name)
			if address_name:
				return {"type": "doc", "value": frappe.get_doc("Address", address_name)}

		if fallback_text:
			return {"type": "text", "value": fallback_text}
		return None

	def _set_address_snapshot(self, prefix, source):
		address = _build_address_snapshot(source)
		self.set(f"{prefix}_address_line_1", address["line_1"])
		self.set(f"{prefix}_address_line_2", address["line_2"])
		self.set(f"{prefix}_address_line_3", address["line_3"])
		self.set(f"{prefix}_address_line_4", address["line_4"])
		self.set(f"{prefix}_postal_code", address["postal_code"])

	def _resolve_bank_details(self, employee):
		bank_details = {
			"bank_name": employee.get("bank_name"),
			"bank_account_no": employee.get("bank_ac_no"),
			"bank_account_type": employee.get("za_bank_account_type"),
			"bank_account_holder_name": employee.get("za_bank_account_holder_name") or employee.employee_name,
			"bank_account_holder_relationship": employee.get("za_bank_account_holder_relationship")
			or "Employee",
			"not_paid_electronically": cint(employee.get("za_not_paid_electronically")),
		}

		bank_account_name = employee.get("za_payroll_payable_bank_account")
		if bank_account_name and frappe.db.exists("Bank Account", bank_account_name):
			bank_account = frappe.get_doc("Bank Account", bank_account_name)
			bank_details["bank_name"] = bank_details["bank_name"] or bank_account.get("bank")
			bank_details["bank_account_no"] = bank_details["bank_account_no"] or bank_account.get(
				"bank_account_no"
			)
			bank_details["bank_account_type"] = bank_details["bank_account_type"] or bank_account.get(
				"account_type"
			)
			bank_details["bank_account_holder_name"] = bank_details[
				"bank_account_holder_name"
			] or bank_account.get("account_name")

		return bank_details

	def _get_directive_numbers(self):
		if not frappe.db.exists("DocType", "Tax Directive"):
			return None

		directives = frappe.get_all(
			"Tax Directive",
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"effective_from": ["<=", self.to_date],
			},
			or_filters=[
				["effective_to", ">=", self.from_date],
				["effective_to", "is", "not set"],
			],
			fields=["directive_number"],
			order_by="effective_from asc",
		)
		numbers = [directive.directive_number for directive in directives if directive.directive_number]
		return ", ".join(numbers) if numbers else None

	def _sort_sars_code(self, code):
		meta = frappe.db.get_value(
			"SARS Payroll Code",
			code,
			["print_sequence"],
			as_dict=True,
		)
		return (cint(meta.print_sequence) if meta else 9999, code)

	def calculate_eti(self):
		"""ETI code 4118 is the theoretical ETI calculated for the employee's
		submitted salary slips for the period.

		The slip is the single source of truth: it already applied the statutory
		rate pack and every eligibility rule (age, employment months, SEZ,
		remuneration band, hours proration). EMP201 records the same generated value
		separately from ETI utilised against the employer's PAYE liability.
		"""
		if not self.employee or not self.from_date or not self.to_date:
			self.eti = 0
			return

		slips = self._get_salary_slips(self.employee, self.from_date, self.to_date)
		self.eti = sum(flt(frappe.db.get_value("Salary Slip", slip.name, "za_monthly_eti")) for slip in slips)

	@frappe.whitelist()
	def export_pdf(self):
		if self.status == "Draft":
			frappe.throw(_("Cannot export a draft certificate. Generate certificate data first."))
		self.validate_statutory_readiness(throw=True)
		pdf_content = self.generate_official_pdf()
		return save_file(
			f"{self.certificate_number or self.name}.pdf",
			pdf_content,
			"IRP5 Certificate",
			self.name,
			is_private=True,
		).file_url

	def generate_official_pdf(self):
		if not pdf_generation_available:
			frappe.throw(_("PDF generation libraries are not installed."))

		return self.generate_certificate_pdf()

	def generate_certificate_pdf(self):
		"""
		Generate a clean practitioner review certificate PDF.

		The bundled SARS PDF is a flat template with no AcroForm fields, so drawing
		against it by approximate coordinates produces overlapping output. This
		generator intentionally uses the IRP5 Certificate snapshot as the source of
		truth and creates a readable certificate PDF for review and filing support.
		"""
		from reportlab.lib.pagesizes import A4

		buffer = BytesIO()
		can = canvas.Canvas(buffer, pagesize=A4)
		width, height = A4
		margin = 42
		line_gap = 13
		bottom = 54

		_try_set_pdf_font(can)

		def clean(value):
			return "" if value in (None, "") else str(value)

		def money(value):
			return f"R {flt(value):,.2f}"

		def draw_header(page_title):
			can.setFillColor(black)
			can.setFont("Helvetica-Bold", 16)
			can.drawString(margin, height - 44, page_title)
			can.setFont("Helvetica", 9)
			can.drawRightString(width - margin, height - 36, clean(self.certificate_number or self.name))
			can.drawRightString(width - margin, height - 50, f"Tax Year: {clean(self.tax_year)}")
			can.line(margin, height - 62, width - margin, height - 62)

		def draw_section_title(title, y):
			can.setFont("Helvetica-Bold", 10)
			can.drawString(margin, y, title)
			can.line(margin, y - 3, width - margin, y - 3)
			return y - 16

		def draw_kv_block(items, x, y, label_width=118, value_width=165):
			for label, value in items:
				value = clean(value)
				can.setFont("Helvetica-Bold", 8.5)
				can.drawString(x, y, f"{label}:")
				can.setFont("Helvetica", 8.5)
				lines = _wrap_pdf_text(value, value_width, "Helvetica", 8.5)
				if not lines:
					lines = [""]
				for index, line in enumerate(lines):
					can.drawString(x + label_width, y - (index * line_gap), line)
				y -= max(1, len(lines)) * line_gap
			return y

		def draw_table(title, rows, columns, y):
			if y < bottom + 90:
				can.showPage()
				draw_header("IRP5 / IT3(a) Employee Tax Certificate")
				y = height - 86

			y = draw_section_title(title, y)
			can.setFont("Helvetica-Bold", 8)
			x = margin
			for label, _fieldname, col_width, align in columns:
				if align == "right":
					can.drawRightString(x + col_width, y, label)
				else:
					can.drawString(x, y, label)
				x += col_width
			y -= 8
			can.line(margin, y, width - margin, y)
			y -= 12

			can.setFont("Helvetica", 8)
			if not rows:
				can.drawString(margin, y, "No rows captured.")
				return y - line_gap

			for row in rows:
				if y < bottom:
					can.showPage()
					draw_header("IRP5 / IT3(a) Employee Tax Certificate")
					y = height - 86
				x = margin
				for _label, fieldname, col_width, align in columns:
					value = row.get(fieldname) if hasattr(row, "get") else getattr(row, fieldname, "")
					if fieldname == "amount":
						value = money(value)
					else:
						value = clean(value)
					if align == "right":
						can.drawRightString(x + col_width, y, value[:24])
					else:
						can.drawString(x, y, value[:42])
					x += col_width
				y -= line_gap
			return y - 10

		draw_header("IRP5 / IT3(a) Employee Tax Certificate")
		y = height - 86

		y = draw_section_title("Certificate Details", y)
		left_y = draw_kv_block(
			[
				("Certificate Type", self.certificate_type),
				("Certificate Number", self.certificate_number or self.name),
				("Year of Assessment", self.year_of_assessment),
				("Transaction Year", self.transaction_year),
				(
					"Reconciliation",
					f"{clean(self.reconciliation_period)} {clean(self.reconciliation_period_yyyymm)}",
				),
				("Period", f"{clean(self.from_date)} to {clean(self.to_date)}"),
				("Issue Date", self.issue_date),
				("Status", self.status),
			],
			margin,
			y,
			value_width=(width / 2) - margin - 126,
		)
		right_y = draw_kv_block(
			[
				("Company", self.company),
				("EMP501", self.emp501_reconciliation),
				("Generation Mode", self.generation_mode),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		y = draw_section_title("Employer Details", y)
		left_y = draw_kv_block(
			[
				("Legal Name", self.employer_legal_name),
				("Trading Name", self.employer_trading_name),
				("Employer Tax ID", self.employer_tax_id),
			],
			margin,
			y,
			value_width=(width / 2) - margin - 126,
		)
		right_y = draw_kv_block(
			[
				("PAYE Ref", self.employer_paye_reference_number),
				("SDL Ref", self.employer_sdl_reference_number),
				("UIF Ref", self.employer_uif_reference_number),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		y = draw_section_title("Employee Details", y)
		left_y = draw_kv_block(
			[
				("Employee", self.employee),
				("Employee Name", self.employee_name),
				("Surname", self.employee_surname),
				("First Names", self.employee_first_names),
				("Initials", self.employee_initials),
				("Gender", self.employee_gender),
			],
			margin,
			y,
			value_width=(width / 2) - margin - 126,
		)
		right_y = draw_kv_block(
			[
				("Identity Type", self.identity_type),
				("ID Number", self.employee_id_number),
				("Passport No", self.passport_number),
				("Passport Country", self.passport_country_of_issue),
				("Tax Ref", self.income_tax_reference_number),
				("Date of Birth", self.date_of_birth),
				("Nature of Person", self.nature_of_person),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		if y < 160:
			can.showPage()
			draw_header("IRP5 / IT3(a) Employee Tax Certificate")
			y = height - 86

		y = draw_section_title("Address, Employment and Bank Details", y)
		left_y = draw_kv_block(
			[
				("Residential", self.res_address_line_1),
				("Residential 2", self.res_address_line_2),
				("Residential 3", self.res_address_line_3),
				("Residential 4", self.res_address_line_4),
				("Residential Code", self.res_postal_code),
				("Postal", self.post_address_line_1),
				("Postal 2", self.post_address_line_2),
				("Postal 3", self.post_address_line_3),
				("Postal 4", self.post_address_line_4),
				("Postal Code", self.post_postal_code),
				("Business", self.biz_address_line_1),
				("Business 2", self.biz_address_line_2),
				("Business 3", self.biz_address_line_3),
				("Business 4", self.biz_address_line_4),
				("Business Code", self.biz_postal_code),
			],
			margin,
			y,
			value_width=(width / 2) - margin - 126,
		)
		right_y = draw_kv_block(
			[
				("Bank Name", self.bank_name),
				("Account No", self.bank_account_no),
				("Account Type", self.bank_account_type),
				("Account Holder", self.bank_account_holder_name),
				("Relationship", self.bank_account_holder_relationship),
				("Paid Electronically", "No" if self.not_paid_electronically else "Yes"),
				("Employed From", self.employed_from),
				("Employed To", self.employed_to),
				("Periods in Year", self.periods_in_year),
				("Periods Worked", self.periods_worked),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		y = draw_section_title("Certificate Totals", y)
		left_y = draw_kv_block(
			[
				("Gross Taxable Income", money(self.gross_taxable_income)),
				("Non-Taxable Income", money(self.non_taxable_income)),
				("Deductions & Contributions", money(self.total_deductions_contributions)),
				("Medical Tax Credit", money(self.medical_scheme_fees_tax_credit)),
				("Additional Medical Credit", money(self.additional_medical_expenses_tax_credit)),
			],
			margin,
			y,
			value_width=(width / 2) - margin - 126,
		)
		right_y = draw_kv_block(
			[
				("PAYE", money(self.paye)),
				("UIF", money(self.uif)),
				("SDL", money(self.sdl)),
				("Total Tax, SDL & UIF (4149)", money(self.total_tax_payable)),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		if self.directive_numbers or self.reason_for_non_deduction:
			y = draw_section_title("Directive and Non-Deduction Details", y)
			can.setFont("Helvetica", 8.5)
			if self.directive_numbers:
				can.drawString(margin, y, f"Directive Number(s): {clean(self.directive_numbers)[:90]}")
				y -= line_gap
			if self.reason_for_non_deduction:
				can.drawString(
					margin,
					y,
					f"Reason Code for IT3(a) (4150): {clean(self.reason_for_non_deduction)[:2]}",
				)

		can.showPage()
		draw_header("IRP5 / IT3(a) Employee Tax Certificate - SARS Code Detail")
		y = height - 86

		y = draw_table(
			"Income Lines",
			self.income_details,
			[
				("Code", "income_code", 55, "left"),
				("Description", "description", 330, "left"),
				("Amount", "amount", 125, "right"),
			],
			y,
		)
		y = draw_table(
			"Deductions and Tax Credits",
			self.deduction_details,
			[
				("Code", "deduction_code", 55, "left"),
				("Description", "description", 330, "left"),
				("Amount", "amount", 125, "right"),
			],
			y,
		)
		y = draw_table(
			"Employer Contributions",
			self.company_contribution_details,
			[
				("Code", "contribution_code", 55, "left"),
				("Description", "description", 330, "left"),
				("Amount", "amount", 125, "right"),
			],
			y,
		)

		if y < bottom + 40:
			can.showPage()
			draw_header("IRP5 / IT3(a) Employee Tax Certificate")
			y = height - 86
		can.setFont("Helvetica", 8)
		can.drawString(
			margin,
			y,
			"This PDF is generated from the ERPNext IRP5 Certificate snapshot for practitioner review.",
		)
		can.drawString(
			margin,
			y - line_gap,
			"It is not a direct SARS eFiling submission. Validate all statutory values before filing.",
		)

		can.save()
		buffer.seek(0)
		return buffer.getvalue()

	def _sum_child_table(self, rows, code_field, codes):
		return sum(flt(getattr(row, "amount", 0)) for row in rows if getattr(row, code_field, None) in codes)

	def generate_it3_pdf(self):
		"""Compatibility wrapper: the official SARS PDF path is now authoritative."""
		return self.generate_official_pdf()

	@frappe.whitelist()
	def get_it3_pdf(self):
		"""Compatibility wrapper retained for callers still expecting IT3 naming."""
		return self.get_official_pdf()

	@frappe.whitelist()
	def get_official_pdf(self):
		if self.status == "Draft":
			frappe.throw(_("Cannot export a draft certificate. Generate certificate data first."))
		self.validate_statutory_readiness(throw=True)
		return base64.b64encode(self.generate_official_pdf()).decode("utf-8")


def _build_address_snapshot(source):
	if not source:
		return {"line_1": "", "line_2": "", "line_3": "", "line_4": "", "postal_code": ""}

	if source["type"] == "text":
		lines = [line.strip() for line in source["value"].splitlines() if line.strip()]
		return {
			"line_1": lines[0] if len(lines) > 0 else "",
			"line_2": lines[1] if len(lines) > 1 else "",
			"line_3": lines[2] if len(lines) > 2 else "",
			"line_4": lines[3] if len(lines) > 3 else "",
			"postal_code": lines[4] if len(lines) > 4 else "",
		}

	address = source["value"]
	line_1 = " ".join(
		part for part in [address.get("za_unit_no"), address.get("za_complex_name")] if part
	).strip()
	if not line_1:
		line_1 = " ".join(
			part for part in [address.get("za_street_no"), address.get("address_line1")] if part
		).strip()

	line_2 = address.get("address_line2") or ""
	line_3 = ", ".join(
		part
		for part in [
			address.get("za_suburb_or_district"),
			address.get("city"),
			address.get("za_address_line_3"),
		]
		if part
	)
	line_4 = ", ".join(
		part
		for part in [address.get("za_address_line_4"), address.get("state"), address.get("country")]
		if part
	)
	return {
		"line_1": line_1,
		"line_2": line_2,
		"line_3": line_3,
		"line_4": line_4,
		"postal_code": address.get("pincode") or "",
	}


def _get_primary_linked_address(link_doctype, link_name):
	rows = frappe.db.sql(
		"""
		SELECT addr.name
		FROM `tabAddress` addr
		INNER JOIN `tabDynamic Link` dl
			ON dl.parent = addr.name
			AND dl.parenttype = 'Address'
		WHERE dl.link_doctype = %s
		  AND dl.link_name = %s
		ORDER BY IFNULL(addr.is_primary_address, 0) DESC, addr.modified DESC
		LIMIT 1
		""",
		(link_doctype, link_name),
		as_dict=True,
	)
	return rows[0].name if rows else None


def _make_initials(*parts):
	return "".join((part or "").strip()[:1].upper() for part in parts if part)


def _is_leap_year(year):
	return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _try_set_pdf_font(can):
	try:
		pdfmetrics.registerFont(TTFont("Arial", "Arial.ttf"))
		can.setFont("Arial", 9)
	except Exception:
		can.setFont("Helvetica", 9)


def _wrap_pdf_text(value, max_width, font_name="Helvetica", font_size=8.5):
	"""Wrap text to fit inside a ReportLab column, including long IDs without spaces."""
	value = str(value or "")
	if not value:
		return [""]

	lines = []
	for paragraph in value.splitlines() or [""]:
		words = paragraph.split(" ") if paragraph else [""]
		current = ""
		for word in words:
			candidate = f"{current} {word}".strip()
			if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
				current = candidate
				continue
			if current:
				lines.append(current)
			current = ""
			while word and pdfmetrics.stringWidth(word, font_name, font_size) > max_width:
				chunk = ""
				for char in word:
					if pdfmetrics.stringWidth(chunk + char, font_name, font_size) > max_width:
						break
					chunk += char
				lines.append(chunk)
				word = word[len(chunk) :]
			current = word
		if current:
			lines.append(current)
	return lines or [""]


@frappe.whitelist()
def get_it3_pdf(docname):
	"""Backward-compatible endpoint retained for existing buttons and integrations."""
	return get_official_pdf(docname)


@frappe.whitelist()
def get_official_pdf(docname):
	# check_permission=True is required: frappe.get_doc does NOT check permissions on
	# its own, and an IRP5 certificate carries the employee's ID number, tax number
	# and full earnings history.
	doc = frappe.get_doc("IRP5 Certificate", docname, check_permission=True)
	return doc.get_official_pdf()


@frappe.whitelist()
def bulk_generate_certificates(filters_json=None):
	# This creates/overwrites certificates for every employee matching the filters,
	# and saves with ignore_permissions below, so gate the whole endpoint first.
	# Permission-based rather than role-based so it tracks whatever roles the site
	# has actually granted on the DocType.
	require_certificate_generation_permissions()

	filters = json.loads(filters_json) if filters_json else {}
	company = filters.get("company")
	tax_year = filters.get("tax_year")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	reconciliation_period = filters.get("reconciliation_period")
	employee_list = filters.get("employee_list")
	department = filters.get("department")
	certificate_type = filters.get("certificate_type") or "IRP5"

	if not company or not tax_year or not from_date or not to_date or not reconciliation_period:
		return {"error": _("Company, Tax Year, From Date, To Date, and Reconciliation Period are required.")}

	employee_filters = {"company": company}
	if department:
		employee_filters["department"] = department
	if employee_list:
		employee_filters["name"] = ["in", employee_list]

	employees = frappe.get_all("Employee", filters=employee_filters, fields=["name"])
	if not employees:
		return {"error": _("No employees found for the given filters.")}

	created = []
	updated = []
	skipped = []

	for employee in employees:
		try:
			existing = get_active_certificate_names(
				{
					"employee": employee.name,
					"company": company,
					"tax_year": tax_year,
					"reconciliation_period": reconciliation_period,
				}
			)
			if len(existing) > 1:
				frappe.throw(
					_(
						"Multiple active certificates exist for employee {0}, tax year {1}, and {2} reconciliation. "
						"Cancel the duplicate before generating again."
					).format(employee.name, tax_year, reconciliation_period),
					title=_("Duplicate IRP5 Certificates"),
				)
			if existing:
				doc = frappe.get_doc("IRP5 Certificate", existing[0])
				action = updated
			else:
				doc = frappe.new_doc("IRP5 Certificate")
				action = created

			doc.certificate_type = certificate_type
			doc.employee = employee.name
			doc.company = company
			doc.tax_year = tax_year
			doc.from_date = from_date
			doc.to_date = to_date
			doc.reconciliation_period = reconciliation_period
			doc.generation_mode = "Individual"
			doc.generate_certificate_data()
			doc.save(ignore_permissions=True)
			action.append(doc.name)
		except Exception as exc:
			frappe.log_error(
				title=f"IRP5 bulk generation failed - {employee.name}",
				message=frappe.get_traceback(),
			)
			skipped.append({"employee": employee.name, "error": str(exc)})

	return {
		"created": created,
		"updated": updated,
		"errors": skipped,
		"message": _("Bulk certificate generation complete. Created: {0}, Updated: {1}, Skipped: {2}").format(
			len(created), len(updated), len(skipped)
		),
	}


def save_file(file_name, content, dt, dn, is_private=False):
	from frappe.utils.file_manager import save_file as _save_file

	return _save_file(file_name, content, dt, dn, is_private=is_private)
