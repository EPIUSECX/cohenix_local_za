"""Utilities for Compensation Fund assessment and claim reporting."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from za_local.utils.statutory_rates import get_coida_annual_earnings_cap

EXCLUDED_PAYROLL_TREATMENTS = {
	"Non-Taxable Reimbursement",
	"Reimbursive Travel",
	"Working Paper Only",
}


def calculate_coida_contribution(assessable_remuneration, industry_rate):
	"""Return the assessment amount for an assessable remuneration base."""
	if not assessable_remuneration or not industry_rate:
		return 0

	return flt(flt(assessable_remuneration) * flt(industry_rate) / 100, 2)


def get_company_industry_rate(company, industry_class=None):
	"""Resolve one authoritative assessment rate for a company and industry class.

	Legacy unscoped rows remain usable only when they produce one unambiguous match.
	"""
	settings = frappe.get_single("COIDA Settings")
	rows = list(settings.get("industry_rates") or [])
	if not rows:
		frappe.throw(_("Configure at least one industry rate in COIDA Settings."))

	def matches_class(row):
		return not industry_class or row.industry_class == industry_class

	company_rows = [row for row in rows if row.get("company") == company and matches_class(row)]
	legacy_rows = [row for row in rows if not row.get("company") and matches_class(row)]
	matching_rows = company_rows or legacy_rows

	if not industry_class and len(matching_rows) > 1:
		frappe.throw(
			_("Select an Industry Class because more than one COIDA rate is configured for {0}.").format(
				frappe.bold(company)
			)
		)
	if not matching_rows:
		frappe.throw(
			_("No COIDA assessment rate is configured for company {0} and industry class {1}.").format(
				frappe.bold(company), frappe.bold(industry_class or _("Not specified"))
			)
		)
	if len(matching_rows) > 1:
		frappe.throw(
			_("COIDA Settings contains duplicate rates for company {0} and industry class {1}.").format(
				frappe.bold(company), frappe.bold(industry_class)
			)
		)

	rate = flt(matching_rows[0].assessment_rate)
	if rate <= 0:
		frappe.throw(_("The configured COIDA assessment rate must be greater than zero."))
	return rate


def validate_industry_rates(industry_rates):
	"""Validate COIDA Settings child rows and return all configuration errors."""
	errors = []
	seen = set()

	if not industry_rates:
		return {"valid": False, "errors": [_('At least one industry rate must be configured')]}

	for row in industry_rates:
		if not row.industry_class:
			errors.append(_("Industry class is required"))

		rate = flt(row.assessment_rate)
		if rate <= 0:
			errors.append(
				_("Assessment rate for industry class {0} must be greater than zero").format(
					row.industry_class or _("Not specified")
				)
			)
		elif rate > 100:
			errors.append(
				_("Assessment rate for industry class {0} cannot exceed 100%").format(row.industry_class)
			)

		key = (row.get("company") or "", row.industry_class or "")
		if key in seen:
			errors.append(
				_("Duplicate COIDA rate for company {0} and industry class {1}").format(
					row.get("company") or _("All Companies"), row.industry_class or _("Not specified")
				)
			)
		seen.add(key)

	return {"valid": not errors, "errors": errors}


def get_coida_earnings_by_employee(company, from_date, to_date):
	"""Return gross and COIDA-applicable earnings for each employee.

	A persisted ``Salary Slip.za_coida_basis`` is preferred when present. Until
	that snapshot field is installed, submitted Salary Detail earning rows are
	aggregated from the component applicability metadata.
	"""
	frappe.has_permission("Salary Slip", "read", throw=True)
	salary_slip_meta = frappe.get_meta("Salary Slip")
	if salary_slip_meta.has_field("za_coida_basis"):
		basis_expression = "SUM(IFNULL(ss.za_coida_basis, 0))"
		basis_rows = frappe.db.sql(
			f"""
				SELECT ss.employee, {basis_expression} AS assessable_total
				FROM `tabSalary Slip` ss
				WHERE ss.company = %(company)s
					AND ss.start_date >= %(from_date)s
					AND ss.end_date <= %(to_date)s
					AND ss.docstatus = 1
				GROUP BY ss.employee
			""",
			{"company": company, "from_date": from_date, "to_date": to_date},
			as_dict=True,
		)
	else:
		component_meta = frappe.get_meta("Salary Component")
		if not component_meta.has_field("za_coida_applicable"):
			frappe.throw(
				_("Salary Component field za_coida_applicable is required before COIDA earnings can be calculated.")
			)

		component_conditions = ["IFNULL(sc.za_coida_applicable, 0) = 1"]
		if component_meta.has_field("za_is_reimbursement"):
			component_conditions.append("IFNULL(sc.za_is_reimbursement, 0) = 0")
		if component_meta.has_field("za_payroll_treatment"):
			component_conditions.append(
				"IFNULL(sc.za_payroll_treatment, '') NOT IN %(excluded_treatments)s"
			)

		salary_detail_meta = frappe.get_meta("Salary Detail")
		detail_conditions = []
		if salary_detail_meta.has_field("statistical_component"):
			detail_conditions.append("IFNULL(sd.statistical_component, 0) = 0")
		if salary_detail_meta.has_field("do_not_include_in_total"):
			detail_conditions.append("IFNULL(sd.do_not_include_in_total, 0) = 0")

		all_conditions = component_conditions + detail_conditions
		basis_rows = frappe.db.sql(
			f"""
				SELECT ss.employee, SUM(sd.amount) AS assessable_total
				FROM `tabSalary Slip` ss
				INNER JOIN `tabSalary Detail` sd
					ON sd.parent = ss.name
					AND sd.parenttype = 'Salary Slip'
					AND sd.parentfield = 'earnings'
				INNER JOIN `tabSalary Component` sc ON sc.name = sd.salary_component
				WHERE ss.company = %(company)s
					AND ss.start_date >= %(from_date)s
					AND ss.end_date <= %(to_date)s
					AND ss.docstatus = 1
					AND {" AND ".join(all_conditions)}
				GROUP BY ss.employee
			""",
			{
				"company": company,
				"from_date": from_date,
				"to_date": to_date,
				"excluded_treatments": tuple(EXCLUDED_PAYROLL_TREATMENTS),
			},
			as_dict=True,
		)

	gross_rows = frappe.db.sql(
		"""
			SELECT employee, SUM(gross_pay) AS gross_total
			FROM `tabSalary Slip`
			WHERE company = %(company)s
				AND start_date >= %(from_date)s
				AND end_date <= %(to_date)s
				AND docstatus = 1
			GROUP BY employee
		""",
		{"company": company, "from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	result = {
		row.employee: frappe._dict(gross_total=flt(row.gross_total), assessable_total=0)
		for row in gross_rows
	}
	for row in basis_rows:
		result.setdefault(row.employee, frappe._dict(gross_total=0, assessable_total=0))
		result[row.employee].assessable_total = flt(row.assessable_total)
	return result


def calculate_annual_coida(company, from_date, to_date, industry_class=None):
	"""Calculate capped COIDA assessable earnings and the assessment amount."""
	earnings = get_coida_earnings_by_employee(company, from_date, to_date)
	cap = get_coida_annual_earnings_cap(from_date)
	gross_remuneration = sum(row.gross_total for row in earnings.values())
	uncapped_assessable = sum(row.assessable_total for row in earnings.values())
	total_remuneration = sum(min(row.assessable_total, cap) for row in earnings.values())
	industry_rate = get_company_industry_rate(company, industry_class)

	return {
		"total_remuneration": flt(total_remuneration, 2),
		"uncapped_remuneration": flt(gross_remuneration, 2),
		"uncapped_assessable_remuneration": flt(uncapped_assessable, 2),
		"excluded_remuneration": flt(max(0, gross_remuneration - total_remuneration), 2),
		"total_coida": calculate_coida_contribution(total_remuneration, industry_rate),
		"employee_count": len(earnings),
		"earnings_cap": cap,
		"industry_rate": industry_rate,
	}


def get_workplace_injuries_for_period(company, from_date, to_date):
	"""Return permission-filtered, non-medical injury summary fields."""
	return frappe.get_list(
		"Workplace Injury",
		filters={"company": company, "injury_date": ["between", [from_date, to_date]]},
		fields=[
			"name",
			"employee",
			"employee_name",
			"company",
			"injury_date",
			"injury_type",
			"severity",
			"status",
			"oid_claim",
		],
		order_by="injury_date desc",
	)


def get_oid_claims_for_period(company, from_date, to_date, status=None):
	"""Return permission-filtered claim summary fields without medical details."""
	filters = {"company": company, "claim_date": ["between", [from_date, to_date]]}
	if status:
		filters["claim_status"] = status

	return frappe.get_list(
		"OID Claim",
		filters=filters,
		fields=[
			"name",
			"employee",
			"company",
			"workplace_injury",
			"claim_reference",
			"claim_date",
			"claim_status",
			"compensation_amount",
		],
		order_by="claim_date desc",
	)
