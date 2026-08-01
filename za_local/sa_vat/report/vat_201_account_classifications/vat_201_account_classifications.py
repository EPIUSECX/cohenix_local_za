import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		frappe.throw(_("Company is required."))
	frappe.has_permission("Account", "read", throw=True)

	return get_columns(), frappe.get_list(
		"Account",
		filters={"company": filters.company},
		fields=[
			"company",
			"name",
			"account_type",
			"custom_vat_return_debit_classification",
			"custom_vat_return_credit_classification",
		],
		order_by="name asc",
		limit_page_length=0,
	)


def get_columns():
	return [
		{"fieldname": "company", "label": _("Company"), "fieldtype": "Link", "options": "Company", "width": 150},
		{"fieldname": "name", "label": _("Account Name"), "fieldtype": "Link", "options": "Account", "width": 300},
		{"fieldname": "account_type", "label": _("Account Type"), "fieldtype": "Data", "width": 140},
		{
			"fieldname": "custom_vat_return_debit_classification",
			"label": _("Debit Classification"),
			"fieldtype": "Data",
			"width": 280,
		},
		{
			"fieldname": "custom_vat_return_credit_classification",
			"label": _("Credit Classification"),
			"fieldtype": "Data",
			"width": 280,
		},
	]
