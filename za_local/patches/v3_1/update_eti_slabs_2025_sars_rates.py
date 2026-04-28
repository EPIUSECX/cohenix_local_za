"""Update ETI slabs to the SARS rates effective from 1 April 2025."""

from __future__ import annotations

import frappe

ETI_SLABS = [
	{
		"title": "ETI 2025-2026 First 12 Months",
		"start_date": "2025-04-01",
		"minimum_age": 18,
		"maximum_age": 29,
		"hours_in_a_month": 160,
		"details": [
			(0, 2499.99, 0, 60, "60% of monthly remuneration", ""),
			(2500, 5499.99, 1500, 0, "R1,500 fixed", ""),
			(5500, 7499.99, 1500, 75, "R1,500 - (75% x (Remuneration - R5,500))", ""),
			(7500, 999999999, 0, 0, "R0", ""),
		],
	},
	{
		"title": "ETI 2025-2026 Second 12 Months",
		"start_date": "2025-04-01",
		"minimum_age": 18,
		"maximum_age": 29,
		"hours_in_a_month": 160,
		"details": [
			(0, 2499.99, 0, 30, "", "30% of monthly remuneration"),
			(2500, 5499.99, 750, 0, "", "R750 fixed"),
			(5500, 7499.99, 750, 37.5, "", "R750 - (37.5% x (Remuneration - R5,500))"),
			(7500, 999999999, 0, 0, "", "R0"),
		],
	},
]


def execute():
	if not frappe.db.exists("DocType", "ETI Slab"):
		return

	# The SARS second-year taper uses 37.5%, so make sure the child field
	# has been widened from Int to Float before existing rows are refreshed.
	frappe.reload_doc("sa_payroll", "doctype", "eti_slab_details", force=True)
	frappe.reload_doc("sa_payroll", "doctype", "eti_slab", force=True)

	for slab in ETI_SLABS:
		upsert_eti_slab(slab)


def upsert_eti_slab(slab: dict):
	name = frappe.db.get_value("ETI Slab", {"title": slab["title"]}, "name")

	if name:
		docstatus = frappe.db.get_value("ETI Slab", name, "docstatus")
		if docstatus == 2:
			frappe.delete_doc("ETI Slab", name, force=True, ignore_permissions=True)
			name = None
		else:
			frappe.db.set_value(
				"ETI Slab",
				name,
				{
					"start_date": slab["start_date"],
					"minimum_age": slab["minimum_age"],
					"maximum_age": slab["maximum_age"],
					"hours_in_a_month": slab["hours_in_a_month"],
				},
			)
			replace_slab_details(name, slab["details"], docstatus)
			return

	doc = frappe.get_doc(
		{
			"doctype": "ETI Slab",
			"title": slab["title"],
			"start_date": slab["start_date"],
			"minimum_age": slab["minimum_age"],
			"maximum_age": slab["maximum_age"],
			"hours_in_a_month": slab["hours_in_a_month"],
			"eti_slab_details": [make_detail(row) for row in slab["details"]],
		}
	)
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	doc.submit()


def replace_slab_details(parent: str, details: list[tuple], docstatus: int):
	frappe.db.delete("ETI Slab Details", {"parent": parent, "parenttype": "ETI Slab"})
	for idx, detail in enumerate(details, start=1):
		row = frappe.get_doc(
			{
				"doctype": "ETI Slab Details",
				"parent": parent,
				"parentfield": "eti_slab_details",
				"parenttype": "ETI Slab",
				"idx": idx,
				"docstatus": docstatus,
				**make_detail(detail),
			}
		)
		row.db_insert()


def make_detail(detail: tuple):
	from_amount, to_amount, eti_amount, percentage, first_period, second_period = detail
	return {
		"from_amount": from_amount,
		"to_amount": to_amount,
		"eti_amount": eti_amount,
		"percentage": percentage,
		"first_qualifying_12_months": first_period,
		"second_qualifying_12_months": second_period,
	}
