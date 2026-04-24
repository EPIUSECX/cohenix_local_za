import frappe

from za_local.sa_vat.setup import get_default_company

DOCTYPE = "South Africa VAT Settings"
CHILD_DOCTYPES = ("South Africa VAT Tax Account", "VAT201 Return Transaction")


def execute():
	reload_vat_docs()
	stabilize_vat_doctype_metadata()
	migrate_singleton_values()


def reload_vat_docs():
	frappe.reload_doc("sa_vat", "doctype", "south_africa_vat_tax_account")
	frappe.reload_doc("sa_vat", "doctype", "vat201_return_transaction")
	frappe.reload_doc("sa_vat", "doctype", "south_africa_vat_settings")


def stabilize_vat_doctype_metadata():
	for doctype in (DOCTYPE, *CHILD_DOCTYPES):
		if frappe.db.exists("DocType", doctype):
			frappe.db.set_value("DocType", doctype, {"module": "SA VAT", "custom": 0}, update_modified=False)


def migrate_singleton_values():
	single_values = {
		row.field: row.value
		for row in frappe.db.sql(
			"""
			SELECT field, value
			FROM `tabSingles`
			WHERE doctype = %s
			""",
			DOCTYPE,
			as_dict=True,
		)
	}
	if not single_values:
		return

	company = (
		single_values.get("company")
		or single_values.get("default_vat_report_company")
		or get_default_company()
	)
	if not company:
		return

	existing_name = frappe.db.get_value(DOCTYPE, {"company": company}, "name")
	doc = frappe.get_doc(DOCTYPE, existing_name) if existing_name else frappe.new_doc(DOCTYPE)
	meta = frappe.get_meta(DOCTYPE)

	if not existing_name:
		doc.company = company

	for field in meta.fields:
		if field.fieldname in {"amended_from"} or field.fieldtype in {
			"Section Break",
			"Column Break",
			"Tab Break",
			"HTML",
			"Button",
			"Fold",
		}:
			continue
		if field.fieldtype == "Table":
			set_child_rows(doc, field)
			continue
		if field.fieldname in single_values and single_values[field.fieldname] not in (None, ""):
			doc.set(field.fieldname, single_values[field.fieldname])

	apply_legacy_fallbacks(doc, company)

	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	if existing_name:
		doc.save(ignore_mandatory=True)
	else:
		doc.insert(ignore_mandatory=True)

	frappe.db.sql("DELETE FROM `tabSingles` WHERE doctype = %s", DOCTYPE)
	cleanup_legacy_singleton_child_rows(meta)
	frappe.clear_cache(doctype=DOCTYPE)


def set_child_rows(doc, field):
	child_meta = frappe.get_meta(field.options)
	rows = frappe.get_all(
		field.options,
		filters={
			"parent": DOCTYPE,
			"parenttype": DOCTYPE,
			"parentfield": field.fieldname,
		},
		fields=["name", "idx"] + [f.fieldname for f in child_meta.fields if f.fieldtype not in {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold"}],
		order_by="idx asc",
	)
	doc.set(field.fieldname, [])
	for row in rows:
		payload = {}
		for child_field in child_meta.fields:
			if child_field.fieldname in {"name", "parent", "parenttype", "parentfield", "idx"}:
				continue
			if child_field.fieldtype in {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold"}:
				continue
			payload[child_field.fieldname] = row.get(child_field.fieldname)
		if any(value not in (None, "") for value in payload.values()):
			doc.append(field.fieldname, payload)


def cleanup_legacy_singleton_child_rows(meta):
	for field in meta.fields:
		if field.fieldtype == "Table":
			frappe.db.delete(
				field.options,
				{
					"parent": DOCTYPE,
					"parenttype": DOCTYPE,
					"parentfield": field.fieldname,
				},
			)


def apply_legacy_fallbacks(doc, company):
	if not getattr(doc, "vat_vendor_type", None):
		doc.vat_vendor_type = get_default_vat_vendor_type()

	first_tracked_account = next((row.account for row in getattr(doc, "tax_accounts", []) if row.account), None)
	fallback_account = (
		getattr(doc, "output_vat_account", None)
		or getattr(doc, "input_vat_account", None)
		or first_tracked_account
		or find_vat_account(company)
	)
	if fallback_account:
		doc.output_vat_account = doc.output_vat_account or fallback_account
		doc.input_vat_account = doc.input_vat_account or fallback_account


def get_default_vat_vendor_type():
	return frappe.db.get_value("VAT Vendor Type", {}, "name", order_by="modified asc")


def find_vat_account(company):
	for pattern in ("%VAT%", "%Output Tax%", "%Input Tax%"):
		account = frappe.db.get_value("Account", {"company": company, "name": ["like", pattern]}, "name")
		if account:
			return account

	for fieldname in ("default_receivable_account", "default_payable_account"):
		account = frappe.db.get_value("Company", company, fieldname)
		if account:
			return account

	return None
