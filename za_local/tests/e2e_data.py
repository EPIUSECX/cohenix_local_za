"""Deterministic end-to-end data for the isolated za_local test site."""

from calendar import month_name, monthrange

import frappe
from frappe import _
from frappe.utils import getdate, today

E2E_COMPANY = "Cohenix Localisation E2E"
E2E_COMPANY_ABBR = "CLE2E"
E2E_HOLIDAY_LIST = "ZA Local E2E Working Calendar 2026-2027"
E2E_EMPLOYEE_TYPE = "E2E Full-time"
E2E_PAYROLL_PAYABLE = f"Payroll Payable - {E2E_COMPANY_ABBR}"
E2E_SALARY_STRUCTURE = "ZA Local E2E Monthly Salary Structure"
E2E_TIMESHEET_STRUCTURE = "ZA Local E2E Timesheet Salary Structure"
E2E_MONTHLY_DEPARTMENT = f"Operations - {E2E_COMPANY_ABBR}"
E2E_TIMESHEET_DEPARTMENT = f"Research & Development - {E2E_COMPANY_ABBR}"
E2E_RECURRING_COMPONENT = "E2E Recurring Allowance"
E2E_BONUS_COMPONENT = "E2E Annual Bonus"
E2E_VAT_CUSTOMER = "ZA Local E2E VAT Customer"
E2E_VAT_SUPPLIER = "ZA Local E2E VAT Supplier"
E2E_VAT_ITEM = "ZA-LOCAL-E2E-SERVICE"


def stage_foundation():
	"""Run ERPNext's supported setup flow for a South African test company."""
	_require_isolated_test_site()

	if not frappe.db.exists("Company", E2E_COMPANY):
		from erpnext.setup.setup_wizard.setup_wizard import setup_complete

		setup_complete(
			frappe._dict(
				{
					"fy_start_date": "2026-03-01",
					"fy_end_date": "2027-02-28",
					"company_name": E2E_COMPANY,
					"company_abbr": E2E_COMPANY_ABBR,
					"currency": "ZAR",
					"country": "South Africa",
					"chart_of_accounts": "Standard",
					"domain": "Services",
					"bank_account": "E2E Bank",
				}
			)
		)

	from za_local.sa_setup.install import (
		repair_salary_component_accounts,
		seed_salary_component_classifications,
		seed_sars_payroll_codes,
		seed_statutory_rate_packs,
	)
	from za_local.sa_setup.statutory_setup import ensure_company_tax_configuration

	company_address = _ensure_address("ZA Local E2E Business Address", "Company", E2E_COMPANY)
	frappe.db.set_value(
		"Company",
		E2E_COMPANY,
		{
			"tax_id": "4123456789",
			"za_vat_number": "4123456789",
			"za_paye_reference_number": "7123456789",
			"za_sdl_reference_number": "L123456789",
			"za_uif_reference_number": "U123456789",
			"za_business_address": company_address,
		},
	)
	ensure_company_tax_configuration(E2E_COMPANY)
	frappe.db.set_single_value(
		"Payroll Settings", "za_eti_unregulated_minimum_monthly_wage", 2500
	)
	seed_statutory_rate_packs()
	seed_sars_payroll_codes()
	seed_salary_component_classifications()
	repair_salary_component_accounts(E2E_COMPANY)
	frappe.db.commit()

	return {
		"company": E2E_COMPANY,
		"payroll_periods": frappe.db.count("Payroll Period", {"company": E2E_COMPANY}),
		"income_tax_slabs": frappe.db.count("Income Tax Slab", {"company": E2E_COMPANY}),
		"travel_rates": frappe.db.count("Travel Allowance Rate", {"company": E2E_COMPANY}),
	}


def stage_payroll_masters():
	"""Create employees, working calendar, structures and assignments."""
	_require_isolated_test_site()
	stage_foundation()

	holiday_list = _ensure_working_calendar()
	frappe.db.set_value("Company", E2E_COMPANY, "default_holiday_list", holiday_list)
	_ensure_holiday_list_assignment(holiday_list)
	frappe.db.set_value("Account", E2E_PAYROLL_PAYABLE, "account_type", "Payable")
	frappe.db.set_value(
		"Company",
		E2E_COMPANY,
		"default_payroll_payable_account",
		E2E_PAYROLL_PAYABLE,
	)
	_ensure_company_bank_account()
	frappe.db.set_value("Salary Component", "Basic", "za_eti_wage_component", 1)
	for gender in ("Male", "Female"):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)

	if not frappe.db.exists("Employee Type", E2E_EMPLOYEE_TYPE):
		frappe.get_doc(
			{
				"doctype": "Employee Type",
				"employee_type": E2E_EMPLOYEE_TYPE,
				"payroll_payable_account": E2E_PAYROLL_PAYABLE,
			}
		).insert(ignore_permissions=True)

	employees = {
		"regular": _ensure_employee(
			"Regular", "1990-01-15", "e2e.regular@cohenix.test", 5000, E2E_MONTHLY_DEPARTMENT
		),
		"eti": _ensure_employee(
			"ETI", "2002-05-10", "e2e.eti@cohenix.test", 5001, E2E_MONTHLY_DEPARTMENT
		),
		"timesheet": _ensure_employee(
			"Timesheet",
			"1995-07-20",
			"e2e.timesheet@cohenix.test",
			5002,
			E2E_TIMESHEET_DEPARTMENT,
		),
	}

	_ensure_salary_structure(E2E_SALARY_STRUCTURE)
	_ensure_salary_structure(E2E_TIMESHEET_STRUCTURE, timesheet_based=True)
	_ensure_salary_structure_assignment(employees["regular"], E2E_SALARY_STRUCTURE, 30000)
	_ensure_salary_structure_assignment(employees["eti"], E2E_SALARY_STRUCTURE, 6000)
	_ensure_salary_structure_assignment(employees["timesheet"], E2E_TIMESHEET_STRUCTURE, 0)
	frappe.db.commit()
	return {
		"employees": employees,
		"holiday_list": holiday_list,
		"salary_structures": [E2E_SALARY_STRUCTURE, E2E_TIMESHEET_STRUCTURE],
	}


def stage_monthly_payroll():
	"""Run and submit the September 2026 monthly payroll scenario."""
	_require_isolated_test_site()
	masters = stage_payroll_masters()
	_ensure_payroll_additional_salaries(masters["employees"])
	return _stage_payroll_month(2026, 9)


def stage_payroll_year_to_date():
	"""Run chronological monthly payrolls from March through September 2026."""
	_require_isolated_test_site()
	masters = stage_payroll_masters()
	_ensure_payroll_additional_salaries(masters["employees"])
	payrolls = [_stage_payroll_month(2026, month) for month in range(3, 10)]
	return {
		"company": E2E_COMPANY,
		"payrolls": payrolls,
		"submitted_salary_slips": frappe.db.count(
			"Salary Slip",
			{
				"company": E2E_COMPANY,
				"start_date": [">=", "2026-03-01"],
				"end_date": ["<=", "2026-09-30"],
				"docstatus": 1,
			},
		),
	}


def stage_interim_statutory_reconciliation():
	"""Create submitted March-August EMP201s, IRP5s and the interim EMP501."""
	_require_isolated_test_site()
	stage_payroll_year_to_date()

	emp201_names = []
	for month in range(3, 9):
		emp201_names.append(_ensure_emp201(month_name[month]))

	existing = frappe.db.get_value(
		"EMP501 Reconciliation",
		{
			"company": E2E_COMPANY,
			"tax_year": "2026-2027",
			"reconciliation_period": "Interim",
			"docstatus": ["<", 2],
		},
		"name",
	)
	if existing:
		emp501 = frappe.get_doc("EMP501 Reconciliation", existing)
	else:
		emp501 = frappe.get_doc(
			{
				"doctype": "EMP501 Reconciliation",
				"company": E2E_COMPANY,
				"tax_year": "2026-2027",
				"reconciliation_period": "Interim",
				"submission_date": "2026-10-01",
			}
		)
		emp501.insert(ignore_permissions=True)

	if emp501.docstatus == 0:
		emp501.fetch_emp201_submissions()
		generation = emp501.generate_irp5_certificates()
		if generation.get("errors"):
			frappe.throw(
				_("IRP5 generation failed for the isolated E2E reconciliation: {0}").format(
					frappe.as_json(generation["errors"])
				)
			)

		for row in emp501.irp5_certificates:
			certificate = frappe.get_doc("IRP5 Certificate", row.irp5_certificate)
			if certificate.docstatus != 0:
				continue
			if not certificate.paye:
				certificate.reason_for_non_deduction = "02"
			certificate.save(ignore_permissions=True)
			certificate.submit()

		emp501.reload()
		emp501.submit()
	frappe.db.commit()
	return {
		"emp201_submissions": emp201_names,
		"emp501": emp501.name,
		"emp501_docstatus": emp501.docstatus,
		"certificates": frappe.get_all(
			"IRP5 Certificate",
			filters={"emp501_reconciliation": emp501.name},
			fields=["name", "employee", "certificate_type", "paye", "docstatus", "status"],
			order_by="employee asc",
		),
	}


def stage_coida_assessment():
	"""Create a submitted COIDA annual return from the staged payroll evidence."""
	_require_isolated_test_site()
	stage_payroll_year_to_date()

	settings = frappe.get_single("COIDA Settings")
	settings.registration_number = "E2E-COIDA-001"
	settings.reference_number = "E2E-ROE-001"
	settings.assessment_year = "2026-2027"
	if not any(
		row.company == E2E_COMPANY and row.industry_class == "E2E Services"
		for row in settings.industry_rates
	):
		settings.append(
			"industry_rates",
			{
				"company": E2E_COMPANY,
				"industry_class": "E2E Services",
				"industry_description": "Isolated test-site professional services",
				"assessment_rate": 1.25,
			},
		)
	settings.save(ignore_permissions=True)

	name = f"COIDA-{E2E_COMPANY}-2026-2027"
	if frappe.db.exists("COIDA Annual Return", name):
		doc = frappe.get_doc("COIDA Annual Return", name)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "COIDA Annual Return",
				"company": E2E_COMPANY,
				"industry_class": "E2E Services",
				"fiscal_year": "2026-2027",
				"total_annual_earnings": 0,
				"total_employees": 0,
			}
		)
		doc.insert(ignore_permissions=True)

	if doc.docstatus == 0:
		doc.fetch_employee_data()
		doc.save(ignore_permissions=True)
		doc.submit()
	frappe.db.commit()
	return {
		"coida_return": doc.name,
		"docstatus": doc.docstatus,
		"employees": doc.total_employees,
		"assessable_earnings": doc.total_annual_earnings,
		"assessment_fee": doc.assessment_fee,
	}


def stage_vat_cycle():
	"""Post sales and purchase VAT evidence and submit a VAT201 working paper."""
	_require_isolated_test_site()
	stage_foundation()

	from za_local.sa_vat.setup import bootstrap_company_vat_setup, get_vat_settings

	settings = get_vat_settings(E2E_COMPANY, create_if_missing=True)
	settings.output_vat_account = _get_e2e_account("VAT Collected - Sales")
	settings.input_vat_account = _get_e2e_account("VAT Paid - Purchases")
	settings.standard_vat_rate = 15
	settings.flags.ignore_permissions = True
	if settings.is_new():
		settings.insert()
	else:
		settings.save()
	bootstrap_company_vat_setup(E2E_COMPANY)
	settings.reload()

	customer = _ensure_vat_customer()
	supplier = _ensure_vat_supplier()
	_ensure_vat_item()
	sales_invoice = _ensure_vat_invoice(
		"Sales Invoice",
		customer,
		settings.standard_rate_non_capital,
		1_000,
	)
	purchase_invoice = _ensure_vat_invoice(
		"Purchase Invoice",
		supplier,
		settings.input_goods_local,
		400,
	)

	existing = frappe.db.get_value(
		"VAT201 Return",
		{
			"company": E2E_COMPANY,
			"from_date": "2026-07-01",
			"to_date": "2026-07-31",
			"docstatus": ["<", 2],
		},
		"name",
	)
	if existing:
		vat_return = frappe.get_doc("VAT201 Return", existing)
	else:
		vat_return = frappe.get_doc(
			{
				"doctype": "VAT201 Return",
				"company": E2E_COMPANY,
				"tax_period": "Monthly",
				"from_date": "2026-07-01",
				"to_date": "2026-07-31",
				"submission_date": "2026-08-01",
				"status": "Draft",
			}
		)
		vat_return.insert(ignore_permissions=True)

	if vat_return.docstatus == 0:
		vat_return.get_vat_transactions()
		vat_return.save(ignore_permissions=True)
		if vat_return.unresolved_transaction_count:
			diagnostics = frappe.get_all(
				"Sales Taxes and Charges",
				filters={"parent": sales_invoice},
				fields=["account_head", "rate", "base_tax_amount"],
			)
			frappe.throw(
				_("VAT201 E2E transactions need review: {0}. Template: {1}. Sales tax rows: {2}").format(
					vat_return.unresolved_issues_summary,
					frappe.db.get_value("Sales Invoice", sales_invoice, "taxes_and_charges"),
					frappe.as_json(diagnostics),
				)
			)
		vat_return.submit()
	frappe.db.commit()
	return {
		"sales_invoice": sales_invoice,
		"purchase_invoice": purchase_invoice,
		"vat201_return": vat_return.name,
		"docstatus": vat_return.docstatus,
		"linked_transactions": len(vat_return.transactions),
		"output_tax": vat_return.total_output_tax,
		"input_tax": vat_return.total_input_tax,
		"vat_payable": vat_return.vat_payable,
	}


def stage_eft_payment_batch():
	"""Submit a payroll payment batch and generate its private FNB OBE CSV."""
	_require_isolated_test_site()
	payroll = stage_monthly_payroll()
	payroll_entry = payroll["payroll_entry"]
	bank_account = _ensure_company_bank_account()

	existing = frappe.db.get_value(
		"Payroll Payment Batch",
		{"payroll_entry": payroll_entry, "docstatus": ["<", 2]},
		"name",
	)
	if existing:
		batch = frappe.get_doc("Payroll Payment Batch", existing)
	else:
		batch = frappe.get_doc(
			{
				"doctype": "Payroll Payment Batch",
				"payroll_entry": payroll_entry,
				"company": E2E_COMPANY,
				"payment_date": today(),
				"bank_account": bank_account,
				"bank_format": "FNB OBE CSV",
			}
		)
		batch.insert(ignore_permissions=True)
	if batch.docstatus == 0:
		batch.submit()

	from za_local.utils.integrations.eft_file_generator import generate_eft_file

	result = generate_eft_file(payment_batch=batch.name)
	batch.reload()
	file_doc = frappe.db.get_value(
		"File",
		{
			"file_url": batch.eft_file_path,
			"attached_to_doctype": "Payroll Payment Batch",
			"attached_to_name": batch.name,
		},
		["name", "file_name", "file_url", "is_private"],
		as_dict=True,
	)
	frappe.db.commit()
	return {
		"payment_batch": batch.name,
		"docstatus": batch.docstatus,
		"employees": batch.total_employees,
		"amount": batch.total_amount,
		"source_hash": batch.eft_source_hash,
		"fnb_hash_total": batch.fnb_hash_total,
		"file": file_doc,
		"reused": result["reused"],
	}


def stage_timesheet_payroll():
	"""Submit an hourly timesheet and its mapped Salary Slip."""
	_require_isolated_test_site()
	employee = stage_payroll_masters()["employees"]["timesheet"]
	activity_type = "ZA Local E2E Payroll Work"
	if not frappe.db.exists("Activity Type", activity_type):
		frappe.get_doc(
			{
				"doctype": "Activity Type",
				"activity_type": activity_type,
				"costing_rate": 0,
				"billing_rate": 0,
			}
		).insert(ignore_permissions=True)

	timesheet_name = frappe.db.get_value(
		"Timesheet",
		{
			"employee": employee,
			"start_date": "2026-09-15",
			"end_date": "2026-09-15",
			"docstatus": ["<", 2],
		},
		"name",
	)
	if timesheet_name:
		timesheet = frappe.get_doc("Timesheet", timesheet_name)
	else:
		timesheet = frappe.get_doc(
			{
				"doctype": "Timesheet",
				"employee": employee,
				"company": E2E_COMPANY,
				"time_logs": [
					{
						"activity_type": activity_type,
						"from_time": "2026-09-15 08:00:00",
						"to_time": "2026-09-15 16:00:00",
						"hours": 8,
					}
				],
			}
		)
		timesheet.insert(ignore_permissions=True)
		timesheet.submit()

	slip_name = frappe.db.get_value(
		"Salary Slip",
		{
			"employee": employee,
			"start_date": "2026-09-15",
			"end_date": "2026-09-15",
			"salary_slip_based_on_timesheet": 1,
			"docstatus": ["<", 2],
		},
		"name",
	)
	if slip_name:
		slip = frappe.get_doc("Salary Slip", slip_name)
	else:
		from hrms.payroll.doctype.salary_slip.salary_slip import make_salary_slip_from_timesheet

		slip = make_salary_slip_from_timesheet(timesheet.name)
		slip.insert(ignore_permissions=True)
		slip.submit()
	frappe.db.commit()
	return {
		"timesheet": timesheet.name,
		"salary_slip": slip.name,
		"hours": slip.total_working_hours,
		"hour_rate": slip.hour_rate,
		"gross_pay": slip.gross_pay,
		"docstatus": slip.docstatus,
	}


def _ensure_emp201(month):
	existing = frappe.db.get_value(
		"EMP201 Submission",
		{
			"company": E2E_COMPANY,
			"fiscal_year": "2026-2027",
			"month": month,
			"docstatus": ["<", 2],
		},
		"name",
	)
	if existing:
		doc = frappe.get_doc("EMP201 Submission", existing)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "EMP201 Submission",
				"company": E2E_COMPANY,
				"fiscal_year": "2026-2027",
				"month": month,
				"posting_date": "2026-09-30",
			}
		)
		doc.insert(ignore_permissions=True)

	if doc.docstatus == 0:
		values = doc.fetch_emp201_data()
		if not values:
			frappe.throw(_("No payroll data was available for the {0} EMP201.").format(month))
		doc.update(values)
		doc.save(ignore_permissions=True)
		doc.submit()
	frappe.db.commit()
	return doc.name


def _ensure_payroll_additional_salaries(employees):
	_ensure_test_salary_component(E2E_RECURRING_COMPONENT, "E2ERA", "3702")
	_ensure_test_salary_component(E2E_BONUS_COMPONENT, "E2EB", "3605", annual_bonus=True)
	_ensure_additional_salary(
		employees["regular"],
		E2E_RECURRING_COMPONENT,
		1500,
		is_recurring=True,
	)
	_ensure_additional_salary(
		employees["regular"],
		"Basic",
		35000,
		payroll_date="2026-09-30",
		overwrite=True,
	)
	_ensure_additional_salary(
		employees["regular"],
		E2E_BONUS_COMPONENT,
		10000,
		payroll_date="2026-09-30",
		full_tax=True,
	)


def _stage_payroll_month(year, month):
	last_day = monthrange(year, month)[1]
	start_date = f"{year:04d}-{month:02d}-01"
	end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

	existing = frappe.db.get_value(
		"Payroll Entry",
		{
			"company": E2E_COMPANY,
			"start_date": start_date,
			"end_date": end_date,
			"department": E2E_MONTHLY_DEPARTMENT,
			"docstatus": ["<", 2],
		},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Payroll Entry", existing)
		if doc.docstatus == 0:
			doc.submit()
			doc.reload()
		if doc.docstatus == 1:
			slip_count = frappe.db.count(
				"Salary Slip", {"payroll_entry": doc.name, "docstatus": ["<", 2]}
			)
			if not slip_count:
				doc.create_salary_slips()
				doc.reload()
			draft_slips = frappe.db.count(
				"Salary Slip", {"payroll_entry": doc.name, "docstatus": 0}
			)
			if draft_slips:
				doc.submit_salary_slips()
		frappe.db.commit()
		return _payroll_summary(existing)

	doc = frappe.new_doc("Payroll Entry")
	doc.company = E2E_COMPANY
	doc.posting_date = end_date
	doc.start_date = start_date
	doc.end_date = end_date
	doc.payroll_frequency = "Monthly"
	doc.department = E2E_MONTHLY_DEPARTMENT
	doc.payroll_payable_account = E2E_PAYROLL_PAYABLE
	doc.payment_account = f"E2E Bank - {E2E_COMPANY_ABBR}"
	doc.currency = "ZAR"
	doc.exchange_rate = 1
	doc.cost_center = frappe.db.get_value(
		"Cost Center", {"company": E2E_COMPANY, "is_group": 0}, "name", order_by="lft asc"
	)
	doc.fill_employee_details()
	doc.insert(ignore_permissions=True)
	# Match the normal Desk workflow, where a draft Payroll Entry is committed
	# before the user submits it in a later request. HRMS deliberately rolls back
	# salary-slip creation failures, which would otherwise also remove this draft.
	frappe.db.commit()
	doc.submit()
	doc.submit_salary_slips()
	frappe.db.commit()
	return _payroll_summary(doc.name)


def _payroll_summary(payroll_entry):
	return {
		"payroll_entry": payroll_entry,
		"salary_slips": frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": payroll_entry},
			fields=["name", "employee", "gross_pay", "total_deduction", "net_pay", "docstatus"],
			order_by="employee asc",
		),
	}


def _ensure_test_salary_component(name, abbreviation, sars_code, annual_bonus=False):
	if frappe.db.exists("Salary Component", name):
		return name
	doc = frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": name,
			"salary_component_abbr": abbreviation,
			"type": "Earning",
			"is_tax_applicable": 1,
			"depends_on_payment_days": 0,
			"za_sars_payroll_code": sars_code,
			"za_payroll_treatment": "Regular Remuneration",
			"za_paye_inclusion_percentage": 100,
			"za_uif_applicable": 1,
			"za_sdl_applicable": 1,
			"za_coida_applicable": 1,
			"za_is_annual_bonus": int(annual_bonus),
		}
	)
	salary_expense_account = frappe.db.get_value(
		"Account",
		{
			"company": E2E_COMPANY,
			"root_type": "Expense",
			"is_group": 0,
			"account_name": ["in", ["Salary", "Salaries and Wages"]],
		},
		"name",
	)
	if not salary_expense_account:
		frappe.throw(_("The E2E company requires a leaf Salary expense account."))
	doc.append(
		"accounts",
		{"company": E2E_COMPANY, "account": salary_expense_account},
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_additional_salary(
	employee,
	component,
	amount,
	*,
	is_recurring=False,
	payroll_date=None,
	overwrite=False,
	full_tax=False,
):
	filters = {
		"employee": employee,
		"salary_component": component,
		"amount": amount,
		"docstatus": 1,
	}
	if is_recurring:
		filters["is_recurring"] = 1
	else:
		filters["payroll_date"] = payroll_date
	existing = frappe.db.get_value("Additional Salary", filters, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": E2E_COMPANY,
			"salary_component": component,
			"amount": amount,
			"is_recurring": int(is_recurring),
			"from_date": "2026-03-01" if is_recurring else None,
			"to_date": "2027-02-28" if is_recurring else None,
			"payroll_date": payroll_date,
			"overwrite_salary_structure_amount": int(overwrite),
			"deduct_full_tax_on_selected_payroll_date": int(full_tax),
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _ensure_working_calendar():
	if frappe.db.exists("Holiday List", E2E_HOLIDAY_LIST):
		return E2E_HOLIDAY_LIST

	doc = frappe.new_doc("Holiday List")
	doc.holiday_list_name = E2E_HOLIDAY_LIST
	doc.from_date = "2026-03-01"
	doc.to_date = "2027-02-28"
	doc.weekly_off = "Sunday"
	for reference_name in ("South Africa 2026", "South Africa 2027"):
		for row in frappe.get_doc("Holiday List", reference_name).holidays:
			if getdate(doc.from_date) <= getdate(row.holiday_date) <= getdate(doc.to_date):
				doc.append(
					"holidays",
					{
						"holiday_date": row.holiday_date,
						"description": row.description,
						"weekly_off": 0,
					},
				)
	doc.get_weekly_off_dates()
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_holiday_list_assignment(holiday_list):
	existing = frappe.db.get_value(
		"Holiday List Assignment",
		{
			"assigned_to": E2E_COMPANY,
			"from_date": "2026-03-01",
			"docstatus": 1,
		},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Holiday List Assignment",
			"applicable_for": "Company",
			"assigned_to": E2E_COMPANY,
			"holiday_list": holiday_list,
			"from_date": "2026-03-01",
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _ensure_employee(label, date_of_birth, email, gender_sequence, department):
	existing = frappe.db.get_value("Employee", {"personal_email": email}, "name")
	if existing:
		frappe.db.set_value("Employee", existing, "department", department)
		employee = existing
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "E2E",
				"last_name": label,
				"gender": "Male",
				"date_of_birth": date_of_birth,
				"date_of_joining": "2026-03-01",
				"company": E2E_COMPANY,
				"department": department,
				"status": "Active",
				"personal_email": email,
				"holiday_list": E2E_HOLIDAY_LIST,
				"za_employee_type": E2E_EMPLOYEE_TYPE,
				"za_id_number": _make_sa_id(date_of_birth, gender_sequence),
				"za_income_tax_reference_number": f"9{gender_sequence:09d}"[-10:],
				"za_hours_per_month": 160,
			}
		)
		doc.insert(ignore_permissions=True)
		employee = doc.name

	address = _ensure_address(f"ZA Local E2E {label} Residential", "Employee", employee)
	bank_account = _ensure_employee_bank_account(employee, label, gender_sequence)
	frappe.db.set_value(
		"Employee",
		employee,
		{
			"bank_name": "ZA Local E2E Test Bank",
			"bank_ac_no": f"62{gender_sequence:09d}"[-11:],
			"za_residential_address": address,
			"za_postal_address": address,
			"za_payroll_payable_bank_account": bank_account,
			"za_bank_account_type": "Current",
			"za_bank_account_holder_name": f"E2E {label}",
			"za_bank_account_holder_relationship": "Employee",
			"za_not_paid_electronically": 0,
			"za_eti_minimum_wage_basis": "No Regulating Measure or NMW Exempt",
		},
	)
	return employee


def _ensure_address(title, link_doctype, link_name):
	existing = frappe.db.get_value("Address", {"address_title": title}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": title,
			"address_type": "Billing",
			"address_line1": "1 Test Street",
			"city": "Johannesburg",
			"state": "Gauteng",
			"country": "South Africa",
			"pincode": "2001",
			"links": [{"link_doctype": link_doctype, "link_name": link_name}],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_employee_bank_account(employee, label, sequence):
	bank_name = "ZA Local E2E Test Bank"
	if not frappe.db.exists("Bank", bank_name):
		frappe.get_doc({"doctype": "Bank", "bank_name": bank_name}).insert(ignore_permissions=True)
	if not frappe.db.exists("Bank Account Type", "Current"):
		frappe.get_doc(
			{"doctype": "Bank Account Type", "account_type": "Current"}
		).insert(ignore_permissions=True)

	account_name = f"E2E {label} Payroll"
	existing = frappe.db.get_value(
		"Bank Account",
		{"account_name": account_name, "bank": bank_name},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Bank Account",
			"account_name": account_name,
			"bank": bank_name,
			"account_type": "Current",
			"party_type": "Employee",
			"party": employee,
			"bank_account_no": f"62{sequence:09d}"[-11:],
			"branch_code": "250655",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_company_bank_account():
	bank_name = "ZA Local E2E Test Bank"
	if not frappe.db.exists("Bank", bank_name):
		frappe.get_doc({"doctype": "Bank", "bank_name": bank_name}).insert(ignore_permissions=True)
	if not frappe.db.exists("Bank Account Type", "Current"):
		frappe.get_doc(
			{"doctype": "Bank Account Type", "account_type": "Current"}
		).insert(ignore_permissions=True)

	gl_account = f"E2E Bank - {E2E_COMPANY_ABBR}"
	existing = frappe.db.get_value("Bank Account", {"account": gl_account}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Bank Account",
			"account_name": "ZA Local E2E Company Payroll",
			"bank": bank_name,
			"account_type": "Current",
			"is_company_account": 1,
			"company": E2E_COMPANY,
			"account": gl_account,
			"bank_account_no": "62000031451",
			"branch_code": "250655",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _make_sa_id(date_of_birth, gender_sequence):
	dob = getdate(date_of_birth)
	prefix = f"{dob:%y%m%d}{gender_sequence:04d}08"
	total = 0
	for index, digit in enumerate(prefix):
		number = int(digit)
		if index % 2:
			number *= 2
			number = number if number <= 9 else number - 9
		total += number
	return f"{prefix}{(10 - total % 10) % 10}"


def _ensure_salary_structure(name, timesheet_based=False):
	if frappe.db.exists("Salary Structure", name):
		return name

	doc = frappe.get_doc(
		{
			"doctype": "Salary Structure",
			"name": name,
			"company": E2E_COMPANY,
			"currency": "ZAR",
			"payroll_frequency": "Monthly",
			"payment_account": E2E_PAYROLL_PAYABLE,
			"salary_slip_based_on_timesheet": int(timesheet_based),
			"salary_component": "Basic" if timesheet_based else None,
			"hour_rate": 500 if timesheet_based else 0,
		}
	)
	if not timesheet_based:
		doc.append(
			"earnings",
			{
				"salary_component": "Basic",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
		)
	for component in ("PAYE", "UIF Employee Contribution"):
		doc.append("deductions", {"salary_component": component})
	for component in ("UIF Employer Contribution", "SDL Contribution"):
		doc.append("company_contribution", {"salary_component": component})
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _ensure_salary_structure_assignment(employee, salary_structure, base):
	existing = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "salary_structure": salary_structure, "docstatus": 1},
		"name",
	)
	if existing:
		return existing

	income_tax_slab = frappe.db.get_value(
		"Income Tax Slab",
		{"company": E2E_COMPANY, "effective_from": ["<=", "2026-03-01"], "docstatus": 1},
		"name",
		order_by="effective_from desc",
	)
	doc = frappe.get_doc(
		{
			"doctype": "Salary Structure Assignment",
			"employee": employee,
			"salary_structure": salary_structure,
			"from_date": "2026-03-01",
			"company": E2E_COMPANY,
			"base": base,
			"income_tax_slab": income_tax_slab,
			"payroll_payable_account": E2E_PAYROLL_PAYABLE,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _get_e2e_account(account_name):
	account = frappe.db.get_value(
		"Account",
		{"company": E2E_COMPANY, "account_name": account_name, "is_group": 0},
		"name",
	)
	if not account:
		frappe.throw(_("E2E account {0} is not configured.").format(account_name))
	return account


def _ensure_vat_customer():
	if frappe.db.exists("Customer", E2E_VAT_CUSTOMER):
		return E2E_VAT_CUSTOMER

	customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name", order_by="name asc")
	territory = frappe.db.get_value("Territory", {"is_group": 0}, "name", order_by="name asc")
	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": E2E_VAT_CUSTOMER,
			"customer_type": "Company",
			"customer_group": customer_group,
			"territory": territory,
			"tax_id": "4987654321",
			"za_is_vat_vendor": 1,
		}
	).insert(ignore_permissions=True)
	_ensure_address("ZA Local E2E Customer Address", "Customer", E2E_VAT_CUSTOMER)
	return E2E_VAT_CUSTOMER


def _ensure_vat_supplier():
	if frappe.db.exists("Supplier", E2E_VAT_SUPPLIER):
		return E2E_VAT_SUPPLIER

	supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name", order_by="name asc")
	frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": E2E_VAT_SUPPLIER,
			"supplier_group": supplier_group,
			"supplier_type": "Company",
			"country": "South Africa",
			"tax_id": "4876543210",
		}
	).insert(ignore_permissions=True)
	_ensure_address("ZA Local E2E Supplier Address", "Supplier", E2E_VAT_SUPPLIER)
	return E2E_VAT_SUPPLIER


def _ensure_vat_item():
	if frappe.db.exists("Item", E2E_VAT_ITEM):
		return E2E_VAT_ITEM

	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": E2E_VAT_ITEM,
			"item_name": "ZA Local E2E Professional Service",
			"item_group": "Services",
			"stock_uom": "Unit",
			"is_stock_item": 0,
			"custom_sa_vat_category": "Standard Rated",
		}
	).insert(ignore_permissions=True)
	return E2E_VAT_ITEM


def _ensure_vat_invoice(doctype, party, tax_template, amount):
	party_field = "customer" if doctype == "Sales Invoice" else "supplier"
	existing = frappe.db.get_value(
		doctype,
		{
			"company": E2E_COMPANY,
			party_field: party,
			"posting_date": "2026-07-15",
			"docstatus": 1,
		},
		"name",
	)
	if existing:
		return existing

	company = frappe.db.get_value(
		"Company",
		E2E_COMPANY,
		["default_income_account", "default_expense_account", "cost_center"],
		as_dict=True,
	)
	values = {
		"doctype": doctype,
		"company": E2E_COMPANY,
		party_field: party,
		"posting_date": "2026-07-15",
		"set_posting_time": 1,
		"taxes_and_charges": tax_template,
		"items": [
			{
				"item_code": E2E_VAT_ITEM,
				"qty": 1,
				"rate": amount,
				"cost_center": company.cost_center,
			}
		],
	}
	if doctype == "Sales Invoice":
		values["due_date"] = "2026-07-31"
		values["items"][0]["income_account"] = company.default_income_account
	else:
		values.update({"bill_no": "E2E-VAT-BILL-001", "bill_date": "2026-07-15", "due_date": "2026-07-31"})
		values["items"][0]["expense_account"] = company.default_expense_account

	doc = frappe.get_doc(values)
	doc.append_taxes_from_master()
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _require_isolated_test_site():
	site = frappe.local.site or ""
	if not frappe.conf.developer_mode or "e2e" not in site.lower():
		frappe.throw(
			_("E2E data may only be staged on a developer-mode site whose name contains 'e2e'."),
			title=_("Isolated Test Site Required"),
		)
