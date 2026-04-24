import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("VAT201 Return"), "fieldname": "vat_return", "fieldtype": "Link", "options": "VAT201 Return", "width": 180},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"label": _("Document Type"), "fieldname": "document_type", "fieldtype": "Data", "width": 120},
		{"label": _("Document"), "fieldname": "document", "fieldtype": "Dynamic Link", "options": "document_type", "width": 180},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 95},
		{"label": _("Classification"), "fieldname": "classification", "fieldtype": "Data", "width": 240},
		{"label": _("Net / Incl Amount"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("VAT Amount"), "fieldname": "vat_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("VAT Account Debit"), "fieldname": "vat_account_debit", "fieldtype": "Currency", "width": 130},
		{"label": _("VAT Account Credit"), "fieldname": "vat_account_credit", "fieldtype": "Currency", "width": 130},
		{"label": _("Cancelled"), "fieldname": "is_cancelled", "fieldtype": "Check", "width": 80},
	]


def get_data(filters):
	return_doc = frappe.qb.DocType("VAT201 Return")
	row = frappe.qb.DocType("VAT201 Return Transaction")

	query = (
		frappe.qb.from_(row)
		.join(return_doc)
		.on(row.parent == return_doc.name)
		.select(
			row.parent.as_("vat_return"),
			return_doc.company,
			row.voucher_type.as_("document_type"),
			row.voucher_no.as_("document"),
			row.posting_date.as_("date"),
			row.classification,
			row.incl_tax_amount.as_("net_amount"),
			row.tax_amount.as_("vat_amount"),
			row.tax_account_debit,
			row.tax_account_credit,
			row.is_cancelled,
		)
		.orderby(row.posting_date)
		.orderby(row.voucher_no)
	)

	if filters.get("company"):
		query = query.where(return_doc.company == filters.company)
	if filters.get("vat_return"):
		query = query.where(row.parent == filters.vat_return)
	if filters.get("from_date"):
		query = query.where(row.posting_date >= filters.from_date)
	if filters.get("to_date"):
		query = query.where(row.posting_date <= filters.to_date)
	if filters.get("classification"):
		query = query.where(row.classification == filters.classification)
	if not filters.get("include_cancelled"):
		query = query.where(row.is_cancelled == 0)

	return query.run(as_dict=True)
