"""
South African Tax Utility Functions

This module provides utility functions for South African tax calculations including:
- PAYE (Pay As You Earn) calculations
- Tax rebates (primary, secondary, tertiary)
- Medical aid tax credits
- Retirement annuity deductions
"""

import calendar
from datetime import date

import frappe
from frappe.utils import date_diff, flt, getdate

from za_local.utils.statutory_rates import (
	get_retirement_annual_cap,
	get_retirement_deduction_percentage,
	get_sdl_rate,
	get_uif_employee_rate,
	get_uif_employer_rate,
	get_uif_monthly_cap,
)


def calculate_south_african_tax(
	annual_taxable_income,
	tax_slab=None,
	date_value=None,
	company=None,
):
	"""Calculate annual PAYE using the slab effective for the supplied date."""
	if flt(annual_taxable_income) <= 0:
		return 0

	if not tax_slab:
		tax_slab = get_current_tax_slab(date_value=date_value, company=company)
	elif isinstance(tax_slab, str):
		tax_slab = frappe.get_cached_doc("Income Tax Slab", tax_slab)

	if not tax_slab:
		frappe.throw(
			frappe._("No submitted Income Tax Slab is configured for {0}.").format(
				getdate(date_value or frappe.utils.today())
			),
			title=frappe._("Missing Income Tax Slab"),
		)

	from za_local.utils.hrms_detection import require_hrms, safe_import_hrms

	(calculate_tax_by_tax_slab,) = safe_import_hrms(
		"hrms.payroll.doctype.salary_slip.salary_slip",
		"calculate_tax_by_tax_slab",
	)
	if calculate_tax_by_tax_slab is None:
		require_hrms("Tax Calculation")

	tax_amount, _other_taxes_and_charges = calculate_tax_by_tax_slab(
		annual_taxable_income,
		tax_slab,
		eval_globals=None,
		eval_locals={},
	)
	return flt(tax_amount)


def get_current_tax_slab(date_value=None, company=None):
	"""Return the submitted slab effective on ``date_value`` for ``company``."""
	date_value = getdate(date_value or frappe.utils.today())
	base_filters = {
		"disabled": 0,
		"docstatus": 1,
		"effective_from": ["<=", date_value],
	}
	company_filters = [company, ["is", "not set"]] if company else [["is", "not set"]]
	for company_filter in company_filters:
		filters = {**base_filters, "company": company_filter}
		name = frappe.db.get_value(
			"Income Tax Slab",
			filters,
			"name",
			order_by="effective_from desc",
		)
		if name:
			return frappe.get_cached_doc("Income Tax Slab", name)
	return None


def _get_payroll_period_name(salary_slip):
	date_value = getdate(salary_slip.end_date)
	company = getattr(salary_slip, "company", None)
	if not company:
		frappe.throw(
			frappe._("Salary Slip company is required to resolve statutory tax rates."),
			title=frappe._("Missing Company"),
		)

	period = frappe.db.get_value(
		"Payroll Period",
		{
			"company": company,
			"start_date": ["<=", date_value],
			"end_date": [">=", date_value],
		},
		"name",
		order_by="start_date desc",
	)
	if not period:
		frappe.throw(
			frappe._("No Payroll Period covers {0} for company {1}.").format(date_value, company),
			title=frappe._("Missing Payroll Period"),
		)
	return period


def _get_statutory_rate_row(rows, payroll_period, rate_label):
	for row in rows or []:
		if row.get("payroll_period") == payroll_period:
			return row
	frappe.throw(
		frappe._("No {0} row is configured for Payroll Period {1}.").format(rate_label, payroll_period),
		title=frappe._("Missing Statutory Rate"),
	)


def get_tax_rebate(salary_slip, date_of_birth):
	"""
	Calculate tax rebates based on employee age.

	South African tax rebates (2024/2025):
	- Primary rebate: R17,235 (all taxpayers)
	- Secondary rebate: R9,444 (age 65+)
	- Tertiary rebate: R3,145 (age 75+)

	Args:
		salary_slip: Salary Slip document
		date_of_birth (date): Employee date of birth

	Returns:
		float: Total annual tax rebate
	"""
	if not date_of_birth:
		return 0

	# Get tax rebate settings
	rebate_settings = frappe.get_single("Tax Rebates and Medical Tax Credit")
	if not rebate_settings.tax_rebates_rate:
		frappe.throw(
			frappe._("Tax rebate rates are not configured."),
			title=frappe._("Missing Tax Rebate Rates"),
		)

	# Calculate age as of the end of the tax year
	dob = getdate(date_of_birth)
	_start_date, tax_year_end = get_tax_year_dates(getdate(salary_slip.end_date))
	year_end = getdate(tax_year_end)

	# Calculate age at end of tax year (Feb 28/29)
	age = year_end.year - dob.year
	if (year_end.month, year_end.day) < (dob.month, dob.day):
		age -= 1

	rebate = _get_statutory_rate_row(
		rebate_settings.tax_rebates_rate,
		_get_payroll_period_name(salary_slip),
		frappe._("tax rebate"),
	)
	total_rebate = flt(rebate.primary)
	if age >= 65:
		total_rebate += flt(rebate.secondary)
	if age >= 75:
		total_rebate += flt(rebate.tertiary)
	return total_rebate


def get_medical_aid_credit(
	salary_slip,
	number_of_dependants,
	membership_start_date=None,
	membership_end_date=None,
):
	"""
	Calculate medical aid tax credits.

	South African medical aid tax credits are stored as monthly per-person
	rates for the main member, first dependant, and additional dependants.

	Medical Tax Credit Rate fields:
	- one_dependant: main member rate
	- two_dependant: first dependant rate
	- additional_dependant: each additional dependant rate

	Args:
		salary_slip: Salary Slip document
		number_of_dependants (int): Number of dependants on medical aid (excluding main member)

	Returns:
		float: Annual medical aid tax credit
	"""
	if number_of_dependants < 0:
		return 0

	# Get medical aid credit settings
	credit_settings = frappe.get_single("Tax Rebates and Medical Tax Credit")
	if not credit_settings.medical_tax_credit:
		frappe.throw(
			frappe._("Medical tax credit rates are not configured."),
			title=frappe._("Missing Medical Tax Credit Rates"),
		)

	credit = _get_statutory_rate_row(
		credit_settings.medical_tax_credit,
		_get_payroll_period_name(salary_slip),
		frappe._("medical tax credit"),
	)
	monthly_credit = flt(credit.one_dependant)
	if number_of_dependants >= 1:
		monthly_credit += flt(credit.two_dependant)
	if number_of_dependants >= 2:
		monthly_credit += flt(credit.additional_dependant) * (number_of_dependants - 1)

	tax_year_start, tax_year_end = get_tax_year_dates(getdate(salary_slip.end_date))
	credit_start = max(tax_year_start, getdate(membership_start_date or tax_year_start))
	credit_end = min(tax_year_end, getdate(membership_end_date or tax_year_end))
	if credit_end < credit_start:
		return 0
	qualifying_months = min(
		12,
		(credit_end.year - credit_start.year) * 12 + credit_end.month - credit_start.month + 1,
	)
	return monthly_credit * qualifying_months


def calculate_retirement_annuity_deduction(salary_slip, retirement_contribution):
	"""
	Calculate allowable retirement annuity deduction for tax purposes.

	South African rules:
	- Maximum deduction: 27.5% of taxable income
	- Subject to annual limit (currently R350,000)

	Args:
		salary_slip: Salary Slip document
		retirement_contribution (float): Annual retirement contribution

	Returns:
		float: Allowable deduction amount
	"""
	if not retirement_contribution or retirement_contribution <= 0:
		return 0

	date_value = getattr(salary_slip, "end_date", None)
	max_percentage = get_retirement_deduction_percentage(date_value)
	max_annual_limit = get_retirement_annual_cap(date_value)

	# Calculate maximum allowable deduction
	taxable_income = flt(salary_slip.total_taxable_earnings)
	max_by_percentage = taxable_income * max_percentage

	# Take the minimum of:
	# 1. Actual contribution
	# 2. 27.5% of taxable income
	# 3. Annual limit
	return min(retirement_contribution, max_by_percentage, max_annual_limit)


def calculate_uif_contribution(gross_pay, date_value=None):
	"""
	Calculate UIF (Unemployment Insurance Fund) contribution.

	UIF rates:
	- Employee: 1% of remuneration
	- Employer: 1% of remuneration
	- Maximum monthly remuneration: R17,712 (2024/2025)

	Args:
		gross_pay (float): Monthly gross pay

	Returns:
		tuple: (employee_uif, employer_uif)
	"""
	UIF_MAX_MONTHLY = get_uif_monthly_cap(date_value)
	employee_rate = get_uif_employee_rate(date_value)
	employer_rate = get_uif_employer_rate(date_value)

	# Cap gross pay at maximum
	capped_gross = min(flt(gross_pay), UIF_MAX_MONTHLY)

	# Calculate contributions
	employee_uif = capped_gross * employee_rate
	employer_uif = capped_gross * employer_rate

	return (employee_uif, employer_uif)


def calculate_sdl_contribution(gross_pay, date_value=None):
	"""
	Calculate SDL (Skills Development Levy) contribution.

	SDL rate: 1% of total payroll (employer pays)

	Args:
		gross_pay (float): Monthly gross pay

	Returns:
		float: SDL amount
	"""
	SDL_RATE = get_sdl_rate(date_value)

	sdl_amount = flt(gross_pay) * SDL_RATE

	return sdl_amount


def validate_south_african_id_number(id_number):
	"""
	Validate South African ID number using Luhn algorithm.

	Format: YYMMDD SSSS CAZ
	- YYMMDD: Date of birth
	- SSSS: Gender (0000-4999 Female, 5000-9999 Male)
	- C: Citizenship (0 SA citizen, 1 Permanent resident)
	- A: Usually 8 or 9
	- Z: Checksum digit

	Args:
		id_number (str): 13-digit ID number

	Returns:
		dict: {valid: bool, gender: str, dob: date, citizenship: str} or None
	"""
	if not id_number or len(id_number) != 13 or not id_number.isdigit():
		return None

	# Extract components
	yy = int(id_number[0:2])
	mm = int(id_number[2:4])
	dd = int(id_number[4:6])
	gender_code = int(id_number[6:10])
	citizenship_code = int(id_number[10])
	checksum = int(id_number[12])

	# Validate date
	if mm < 1 or mm > 12 or dd < 1 or dd > 31:
		return None

	# Determine century
	current_year = date.today().year % 100
	century = 1900 if yy > current_year else 2000
	year = century + yy

	try:
		dob = date(year, mm, dd)
	except ValueError:
		return None

	# Validate checksum using Luhn algorithm
	total = 0
	for i, digit in enumerate(id_number[:-1]):
		num = int(digit)
		if i % 2 == 0:
			total += num
		else:
			doubled = num * 2
			total += doubled if doubled <= 9 else doubled - 9

	calculated_checksum = (10 - (total % 10)) % 10

	if calculated_checksum != checksum:
		return None

	# Determine gender and citizenship
	gender = "Female" if gender_code < 5000 else "Male"
	citizenship = "SA Citizen" if citizenship_code == 0 else "Permanent Resident"

	return {
		"valid": True,
		"gender": gender,
		"date_of_birth": dob,
		"citizenship": citizenship
	}


def validate_south_african_id(id_number):
	"""
	Validate South African ID number format and checksum.

	This is a simpler boolean validation function that uses basic checks.
	For detailed validation with gender, DOB, and citizenship info, use
	validate_south_african_id_number() instead.

	Format: YYMMDD SSSS CAZ
	- YYMMDD: Date of birth
	- SSSS: Gender (Females: 0000-4999, Males: 5000-9999)
	- C: Citizenship (0: SA, 1: Permanent resident)
	- A: Usually 8 or 9 (historical)
	- Z: Checksum digit (Luhn algorithm)

	Args:
		id_number (str): South African ID number to validate

	Returns:
		bool: True if valid, False otherwise
	"""
	if not id_number or not id_number.isdigit() or len(id_number) != 13:
		return False

	# Birth date validation
	month = int(id_number[2:4])
	day = int(id_number[4:6])

	if month < 1 or month > 12 or day < 1 or day > 31:
		return False

	# Calculate checksum using Luhn algorithm
	checksum = 0
	for i, digit in enumerate(id_number[:-1]):
		num = int(digit)
		if i % 2 == 0:
			checksum += num
		else:
			checksum += (num * 2 if num * 2 <= 9 else num * 2 - 9)

	check_digit = (10 - (checksum % 10)) % 10
	return check_digit == int(id_number[-1])


def get_tax_year_dates(date_in_year=None):
	"""
	Get the South African tax year dates (March 1 to Feb 28/29).

	Args:
		date_in_year (date): Date within the tax year

	Returns:
		tuple: (start_date, end_date) of tax year
	"""
	if not date_in_year:
		date_in_year = date.today()
	else:
		date_in_year = getdate(date_in_year)

	year = date_in_year.year

	# Tax year runs from March 1 to Feb 28/29
	if date_in_year.month < 3:
		# Before March, so previous tax year
		start_date = date(year - 1, 3, 1)
		end_date = date(year, 2, 29 if calendar.isleap(year) else 28)
	else:
		# March or later, current tax year
		start_date = date(year, 3, 1)
		next_year = year + 1
		end_date = date(next_year, 2, 29 if calendar.isleap(next_year) else 28)

	return (start_date, end_date)
