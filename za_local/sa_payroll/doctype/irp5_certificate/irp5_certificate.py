import base64
import json
from collections import defaultdict
from io import BytesIO

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, cint, flt, get_first_day, getdate, today

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


class IRP5Certificate(Document):
	def autoname(self):
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
		self.status = "Cancelled"
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
		self.paye = self._sum_child_table(self.deduction_details, "deduction_code", {"4102"})
		self.uif = self._sum_child_table(self.deduction_details, "deduction_code", {"4141"})
		self.sdl = self._sum_child_table(self.company_contribution_details, "contribution_code", {"4142"})

		if not self.gross_taxable_income:
			self.gross_taxable_income = sum(flt(row.amount) for row in self.income_details)
		if not self.non_taxable_income:
			self.non_taxable_income = 0

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
		self.total_deductions_contributions = (
			sum(flt(row.amount) for row in self.deduction_details)
			+ sum(flt(row.amount) for row in self.company_contribution_details)
		)
		self.total_tax_payable = self.paye + self.uif + self.sdl - flt(self.eti)

	@frappe.whitelist()
	def validate_statutory_readiness(self, throw=False):
		missing = []

		required_pairs = [
			("Employer PAYE Reference Number", self.employer_paye_reference_number),
			("Employer SDL Reference Number", self.employer_sdl_reference_number),
			("Employer UIF Reference Number", self.employer_uif_reference_number),
			("Employee identity type", self.identity_type),
			("Employee identity number", self.employee_id_number),
			("Employee income tax reference number", self.income_tax_reference_number),
			("Residential address", self.res_address_line_1),
			("Employment start date", self.employed_from),
			("Periods in year", self.periods_in_year),
			("Periods worked", self.periods_worked),
		]
		for label, value in required_pairs:
			if not value:
				missing.append(label)

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

		if not self.paye and flt(self.gross_taxable_income) > 0 and not (
			self.directive_numbers or self.reason_for_non_deduction
		):
			missing.append("Directive number or reason for non-deduction")

		self.missing_sars_data = "\n".join(f"- {item}" for item in missing)

		if throw and missing:
			frappe.throw(
				_(
					"Cannot generate or export this certificate until the following SARS fields are complete:<br><br>{0}"
				).format("<br>".join(f"• {frappe.bold(item)}" for item in missing)),
				title=_("Missing SARS Data"),
			)

		return missing

	@frappe.whitelist()
	def generate_certificate_data(self):
		if not self.employee:
			frappe.throw(_("Employee is required to generate certificate data."))
		if not self.company:
			frappe.throw(_("Company is required to generate certificate data."))
		if not self.tax_year or not self.from_date or not self.to_date or not self.reconciliation_period:
			frappe.throw(_("Tax Year, Reconciliation Period, From Date, and To Date are required."))

		self.validate_employee()
		if not self.certificate_number:
			self.set_certificate_number()

		self.issue_date = today()
		self._reset_snapshot()
		self._snapshot_master_data()
		counts = self._generate_certificate_lines()
		self.calculate_eti()
		self.calculate_totals()
		missing = self.validate_statutory_readiness(throw=False)
		if missing:
			frappe.throw(
				_(
					"IRP5 certificate data was not generated because required SARS data is missing:<br><br>{0}"
				).format("<br>".join(f"• {frappe.bold(item)}" for item in missing)),
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
			"reason_for_non_deduction",
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
		self.employee_first_names = " ".join(
			part
			for part in [employee.get("first_name"), employee.get("middle_name")]
			if part
		).strip() or employee.employee_name
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
		self.bank_account_holder_relationship = bank_details.get(
			"bank_account_holder_relationship"
		)
		self.not_paid_electronically = bank_details.get("not_paid_electronically", 0)

		self.employed_from = employee.get("date_of_joining") or self.from_date
		self.employed_to = employee.get("relieving_date") or self.to_date
		self.periods_in_year = self._estimate_periods_in_year()
		self.directive_numbers = self._get_directive_numbers()

	def _generate_certificate_lines(self):
		salary_slips = self._get_salary_slips(self.employee, self.from_date, self.to_date)
		if not salary_slips:
			frappe.throw(_("No salary slips found for this employee in the selected period."))

		full_year_salary_slips = self._get_salary_slips(
			self.employee,
			self.from_date,
			self._get_tax_year_end_date(),
		)
		self.periods_worked = len(salary_slips)
		self.periods_in_year = max(self.periods_in_year, len(full_year_salary_slips), len(salary_slips))

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
				if code_doc.tax_treatment == "Non-Taxable":
					non_taxable_income += flt(earning.amount)
				else:
					gross_taxable_income += flt(earning.amount)

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
		if not self.reason_for_non_deduction and not self.paye:
			self.reason_for_non_deduction = (
				_("No taxable remuneration in period")
				if gross_taxable_income <= 0
				else _("No PAYE deducted in payroll period - practitioner review required")
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
				"start_date": [">=", getdate(from_date)],
				"end_date": ["<=", getdate(to_date)],
				"docstatus": 1,
			},
			fields=["name", "start_date", "end_date"],
			order_by="start_date",
		)

	def _get_tax_year_end_date(self):
		return self.to_date

	def _estimate_periods_in_year(self):
		count = 0
		temp_from_date = getdate(self.from_date)
		loop_to_date = getdate(self.to_date)
		while temp_from_date <= loop_to_date:
			count += 1
			temp_from_date = get_first_day(add_months(temp_from_date, 1))
		return count

	def _get_sars_payroll_code(self, salary_component_name):
		component = frappe.db.get_value(
			"Salary Component",
			salary_component_name,
			["za_sars_payroll_code", "za_exclude_from_irp5"],
			as_dict=True,
		) or frappe._dict()

		if component.get("za_exclude_from_irp5"):
			return None

		code = component.get("za_sars_payroll_code")
		if not code:
			self._unmapped_salary_components.append(
				f"Salary Component '{salary_component_name}' has no SARS Payroll Code"
			)
			return None
		if not frappe.db.exists("SARS Payroll Code", code):
			self._unmapped_salary_components.append(
				f"SARS Payroll Code '{code}' linked from Salary Component '{salary_component_name}' does not exist"
			)
			return None
		return frappe.get_doc("SARS Payroll Code", code)

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

	def _resolve_address(self, explicit_address_name=None, link_doctype=None, link_name=None, fallback_text=None):
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
			"bank_account_holder_name": employee.get("za_bank_account_holder_name")
			or employee.employee_name,
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
			bank_details["bank_account_holder_name"] = (
				bank_details["bank_account_holder_name"] or bank_account.get("account_name")
			)

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
		disable_eti_globally = frappe.db.get_single_value(
			"Payroll Settings",
			"za_disable_eti_calculation",
		)
		if disable_eti_globally or not self.employee or not self.to_date:
			self.eti = 0
			return

		employee = frappe.get_doc("Employee", self.employee)
		if not employee.date_of_birth or not employee.date_of_joining:
			self.eti = 0
			return

		end_date = getdate(self.to_date)
		birth_date = getdate(employee.date_of_birth)
		age_years = end_date.year - birth_date.year - (
			(end_date.month, end_date.day) < (birth_date.month, birth_date.day)
		)
		if not (18 <= age_years <= 29) and not employee.get("za_special_economic_zone"):
			self.eti = 0
			return

		date_of_joining = getdate(employee.date_of_joining)
		if date_of_joining < getdate("2013-10-01"):
			self.eti = 0
			return

		employment_months = (
			(end_date.year - date_of_joining.year) * 12
			+ end_date.month
			- date_of_joining.month
			- (end_date.day < date_of_joining.day)
		)
		if employment_months >= 24:
			self.eti = 0
			return

		total_income = sum(flt(d.amount) for d in self.income_details if d.income_code in {"3601", "3802"})
		months_in_period = max(self.periods_worked or 0, 1)
		monthly_remuneration = total_income / months_in_period
		is_first_12_months = employment_months < 12
		self.eti = self.calculate_eti_amount(monthly_remuneration, is_first_12_months) * months_in_period

	def calculate_eti_amount(self, monthly_remuneration, is_first_12_months):
		max_eti_first_year = 1500
		max_eti_second_year = 750

		if is_first_12_months:
			if monthly_remuneration < 2500:
				return monthly_remuneration * 0.60
			if monthly_remuneration < 5500:
				return max_eti_first_year
			if monthly_remuneration < 7500:
				return max_eti_first_year - (0.75 * (monthly_remuneration - 5500))
			return 0

		if monthly_remuneration < 2500:
			return monthly_remuneration * 0.30
		if monthly_remuneration < 5500:
			return max_eti_second_year
		if monthly_remuneration < 7500:
			return max_eti_second_year - (0.375 * (monthly_remuneration - 5500))
		return 0

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
				("Reconciliation", f"{clean(self.reconciliation_period)} {clean(self.reconciliation_period_yyyymm)}"),
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
				("ETI", money(self.eti)),
				("Total Tax Payable", money(self.total_tax_payable)),
			],
			width / 2 + 12,
			y,
			value_width=width - margin - (width / 2 + 12) - 118,
		)
		y = min(left_y, right_y) - 10

		if self.reason_for_non_deduction:
			y = draw_section_title("Practitioner Review Notes", y)
			can.setFont("Helvetica", 8.5)
			can.drawString(margin, y, clean(self.reason_for_non_deduction)[:110])

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
		for part in [address.get("za_suburb_or_district"), address.get("city"), address.get("za_address_line_3")]
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
				word = word[len(chunk):]
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
	doc = frappe.get_doc("IRP5 Certificate", docname)
	return doc.get_official_pdf()


@frappe.whitelist()
def bulk_generate_certificates(filters_json=None):
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
			existing = frappe.get_all(
				"IRP5 Certificate",
				filters={
					"employee": employee.name,
					"tax_year": tax_year,
					"from_date": from_date,
					"to_date": to_date,
					"certificate_type": certificate_type,
				},
				fields=["name"],
				limit=1,
			)
			if existing:
				doc = frappe.get_doc("IRP5 Certificate", existing[0].name)
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
			skipped.append({"employee": employee.name, "error": str(exc)})

	return {
		"created": created,
		"updated": updated,
		"errors": skipped,
		"message": _(
			"Bulk certificate generation complete. Created: {0}, Updated: {1}, Skipped: {2}"
		).format(len(created), len(updated), len(skipped)),
	}


def save_file(file_name, content, dt, dn, is_private=False):
	from frappe.utils.file_manager import save_file as _save_file

	return _save_file(file_name, content, dt, dn, is_private=is_private)
