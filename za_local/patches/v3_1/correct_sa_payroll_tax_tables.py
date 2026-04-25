"""Correct South African PAYE marginal slabs and medical tax credits.

HRMS stores marginal tax brackets, while ZA Local applies SARS rebates as a
separate annual credit in the Salary Slip override. The fixtures must therefore
start the first PAYE bracket at 18% from the first rand rather than encoding the
tax-free threshold as a 0% bracket.
"""

from __future__ import annotations

import frappe


TAX_SLABS = {
	"South Africa 2024-2025": [
		(1, 237100.99, 18),
		(237101, 370500.99, 26),
		(370501, 512800.99, 31),
		(512801, 673000.99, 36),
		(673001, 857900.99, 39),
		(857901, 1817000.99, 41),
		(1817001, 999999999, 45),
	],
	"South Africa 2025-2026": [
		(1, 237100.99, 18),
		(237101, 370500.99, 26),
		(370501, 512800.99, 31),
		(512801, 673000.99, 36),
		(673001, 857900.99, 39),
		(857901, 1817000.99, 41),
		(1817001, 999999999, 45),
	],
	"South Africa 2026-2027": [
		(1, 245100.99, 18),
		(245101, 383100.99, 26),
		(383101, 530200.99, 31),
		(530201, 695800.99, 36),
		(695801, 887000.99, 39),
		(887001, 1878600.99, 41),
		(1878601, 999999999, 45),
	],
}


MEDICAL_CREDITS = {
	"2024-2025": {"one_dependant": 364, "two_dependant": 364, "additional_dependant": 246},
	"2025-2026": {"one_dependant": 364, "two_dependant": 364, "additional_dependant": 246},
	"2026-2027": {"one_dependant": 376, "two_dependant": 376, "additional_dependant": 254},
}

RETIREMENT_FUND_CODES = ("4001", "4003", "4006", "4007")


def execute():
	correct_income_tax_slabs()
	correct_medical_tax_credits()
	correct_retirement_fund_components()


def correct_income_tax_slabs():
	child_doctype = "Taxable Salary Slab"

	for slab_name, slabs in TAX_SLABS.items():
		if not frappe.db.exists("Income Tax Slab", slab_name):
			continue

		frappe.db.set_value(
			"Income Tax Slab",
			slab_name,
			{
				"allow_tax_exemption": 1,
				"standard_tax_exemption_amount": 0,
			},
		)
		frappe.db.delete(child_doctype, {"parent": slab_name, "parenttype": "Income Tax Slab"})

		for idx, (from_amount, to_amount, percent_deduction) in enumerate(slabs, start=1):
			row = frappe.get_doc(
				{
					"doctype": child_doctype,
					"parent": slab_name,
					"parentfield": "slabs",
					"parenttype": "Income Tax Slab",
					"idx": idx,
					"from_amount": from_amount,
					"to_amount": to_amount,
					"percent_deduction": percent_deduction,
				}
			)
			row.db_insert()


def correct_medical_tax_credits():
	if not frappe.db.exists("DocType", "Medical Tax Credit Rate"):
		return

	for payroll_period, values in MEDICAL_CREDITS.items():
		for fieldname, value in values.items():
			frappe.db.set_value(
				"Medical Tax Credit Rate",
				{"parent": "Tax Rebates and Medical Tax Credit", "payroll_period": payroll_period},
				fieldname,
				value,
			)


def correct_retirement_fund_components():
	if not frappe.db.table_exists("Salary Component"):
		return

	for component in frappe.get_all(
		"Salary Component",
		filters={"za_sars_payroll_code": ["in", RETIREMENT_FUND_CODES]},
		pluck="name",
	):
		frappe.db.set_value("Salary Component", component, "exempted_from_income_tax", 1)
