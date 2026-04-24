import frappe
from frappe import _
from frappe.utils import cint, flt

FULL_TAX_INVOICE_THRESHOLD = 5000
NO_TAX_INVOICE_THRESHOLD = 50


@frappe.whitelist()
def check_tax_invoice_readiness(sales_invoice: str):
	doc = frappe.get_doc("Sales Invoice", sales_invoice)
	profile = build_sales_invoice_print_profile(
		company=doc.company,
		base_grand_total=getattr(doc, "base_grand_total", None),
		grand_total=getattr(doc, "grand_total", None),
		is_pos=getattr(doc, "is_pos", 0),
		is_return=getattr(doc, "is_return", 0),
	)

	checks = [
		check("invoice_label", _("Invoice heading"), True, _("Use the SA tax invoice print format.")),
		check("supplier_name", _("Supplier name"), bool(doc.company), doc.company),
		check(
			"supplier_address",
			_("Supplier address"),
			bool(doc.company_address_display),
			_("Missing company address"),
		),
		check(
			"supplier_vat_number",
			_("Supplier VAT number"),
			bool(doc.company_tax_id),
			_("Missing company VAT number"),
		),
		check("customer_name", _("Customer name"), bool(doc.customer_name), doc.customer_name),
		check(
			"customer_address",
			_("Customer address"),
			profile["invoice_type"] != "full_tax_invoice" or bool(doc.address_display),
			_("Customer address recommended for full tax invoices"),
		),
		check(
			"serial_number",
			_("Invoice number"),
			bool(doc.name),
			doc.name,
		),
		check("issue_date", _("Issue date"), bool(doc.posting_date), doc.posting_date),
		check(
			"line_descriptions",
			_("Item descriptions"),
			all(bool((item.description or "").strip()) for item in doc.items),
			_("One or more items are missing a description"),
		),
		check(
			"quantities",
			_("Item quantities"),
			all((item.qty or 0) > 0 for item in doc.items),
			_("One or more items are missing quantity information"),
		),
		check("value_of_supply", _("Value of supply"), profile["consideration"] > 0, profile["consideration"]),
		check(
			"tax_amount",
			_("Tax amount"),
			doc.total_taxes_and_charges is not None,
			doc.total_taxes_and_charges,
		),
		check("total_consideration", _("Total consideration"), bool(doc.grand_total), doc.grand_total),
	]

	missing = [item["label"] for item in checks if not item["ok"]]
	return {
		"sales_invoice": doc.name,
		"status": "ready" if not missing else "attention",
		"invoice_type": profile["invoice_type"],
		"recommended_print_format": profile["print_format"],
		"consideration": profile["consideration"],
		"checks": checks,
		"missing": missing,
		"threshold_guidance": {
			"full_tax_invoice_over": FULL_TAX_INVOICE_THRESHOLD,
			"no_tax_invoice_at_or_below": NO_TAX_INVOICE_THRESHOLD,
		},
	}


@frappe.whitelist()
def get_sales_invoice_print_profile(
	company: str | None = None,
	base_grand_total: float | None = None,
	grand_total: float | None = None,
	is_pos: int = 0,
	is_return: int = 0,
):
	return build_sales_invoice_print_profile(
		company=company,
		base_grand_total=base_grand_total,
		grand_total=grand_total,
		is_pos=is_pos,
		is_return=is_return,
	)


def build_sales_invoice_print_profile(
	company: str | None,
	base_grand_total: float | None = None,
	grand_total: float | None = None,
	is_pos: int = 0,
	is_return: int = 0,
):
	consideration = abs(flt(base_grand_total or grand_total or 0))
	invoice_type = get_invoice_type(consideration)
	recommended = get_recommended_print_format(invoice_type)
	is_sa_company = is_company_in_south_africa(company)
	preserve_existing = bool(cint(is_pos) or cint(is_return))
	return {
		"company": company,
		"consideration": consideration,
		"invoice_type": invoice_type,
		"is_south_africa_company": is_sa_company,
		"preserve_existing_default": preserve_existing,
		"override_default": bool(is_sa_company and not preserve_existing and recommended),
		"print_format": recommended if is_sa_company else None,
	}


def get_invoice_type(consideration):
	if consideration <= NO_TAX_INVOICE_THRESHOLD:
		return "no_tax_invoice_required"
	if consideration <= FULL_TAX_INVOICE_THRESHOLD:
		return "abridged_tax_invoice"
	return "full_tax_invoice"


def get_recommended_print_format(invoice_type):
	if invoice_type == "full_tax_invoice":
		return "SA Full Tax Invoice"
	if invoice_type == "abridged_tax_invoice":
		return "SA Abridged Tax Invoice"
	return None


def is_company_in_south_africa(company: str | None):
	if not company:
		return False
	return frappe.db.get_value("Company", company, "country", cache=True) == "South Africa"


def check(key, label, ok, detail=None):
	return {"key": key, "label": label, "ok": bool(ok), "detail": detail}
