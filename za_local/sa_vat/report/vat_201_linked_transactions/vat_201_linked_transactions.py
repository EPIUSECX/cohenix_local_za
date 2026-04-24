import frappe
from frappe import _


def execute(filters=None):
	return get_columns(), get_data(filters or {})


def get_columns():
	return [
		{"fieldname": "parent", "label": _("VAT201 Return"), "fieldtype": "Link", "options": "VAT201 Return", "width": 180},
		{"fieldname": "gl_entry", "label": _("GL Entry"), "fieldtype": "Link", "options": "GL Entry", "width": 160},
		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 130},
		{"fieldname": "voucher_no", "label": _("Voucher No"), "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "taxes_and_charges", "label": _("Taxes and Charges Template"), "fieldtype": "Data", "width": 220},
		{"fieldname": "tax_account_debit", "label": _("Tax Debit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "tax_account_credit", "label": _("Tax Credit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "tax_amount", "label": _("Tax Amount"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "incl_tax_amount", "label": _("Incl Tax Amount"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "classification", "label": _("Classification"), "fieldtype": "Data", "width": 240},
		{"fieldname": "classification_status", "label": _("Status"), "fieldtype": "Data", "width": 120},
		{"fieldname": "classification_issue", "label": _("Issue"), "fieldtype": "Data", "width": 280},
		{"fieldname": "is_cancelled", "label": _("Cancelled"), "fieldtype": "Check", "width": 80},
	]


def get_data(filters):
	if not filters.get("vat_return"):
		return []

	return frappe.get_all(
		"VAT201 Return Transaction",
		filters={
			"parent": filters["vat_return"],
			**({"classification": filters["classification"]} if filters.get("classification") else {}),
			**({} if filters.get("include_cancelled") else {"is_cancelled": 0}),
		},
		fields=[
			"parent",
			"gl_entry",
			"voucher_type",
			"voucher_no",
			"posting_date",
			"taxes_and_charges",
			"tax_account_debit",
			"tax_account_credit",
			"tax_amount",
			"incl_tax_amount",
			"classification",
			"classification_status",
			"classification_issue",
			"is_cancelled",
		],
		order_by="posting_date asc, voucher_no asc",
	)
