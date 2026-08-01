import frappe
from frappe import _
from frappe.utils import cint, flt

FULL_TAX_INVOICE_THRESHOLD = 5000
NO_TAX_INVOICE_THRESHOLD = 50


@frappe.whitelist(methods=["GET"])
def check_tax_invoice_readiness(sales_invoice: str):
	# check_permission=True is required: frappe.get_doc does NOT check permissions,
	# and the response exposes customer name, posting date and invoice totals.
	doc = frappe.get_doc("Sales Invoice", sales_invoice, check_permission=True)
	company_vat_number = get_company_vat_registration_number(doc.company) or getattr(doc, "company_tax_id", None)
	company_currency = get_company_currency(doc.company)
	recipient_vat_details = get_party_vat_details("Customer", getattr(doc, "customer", None))
	recipient_vat_number = getattr(doc, "tax_id", None) or recipient_vat_details.get("tax_id")
	profile = build_sales_invoice_print_profile(
		company=doc.company,
		base_grand_total=getattr(doc, "base_grand_total", None),
		grand_total=getattr(doc, "grand_total", None),
		is_pos=getattr(doc, "is_pos", 0),
		is_return=getattr(doc, "is_return", 0),
		company_currency=company_currency,
	)
	full_invoice = profile["invoice_type"] == "full_tax_invoice"
	tax_invoice_required = profile["invoice_type"] != "no_tax_invoice_required"

	checks = [
		check(
			"invoice_label",
			_("Invoice heading"),
			True,
			_("Use the recommended SA tax invoice or credit note print format."),
			required=tax_invoice_required,
		),
		check("supplier_name", _("Supplier name"), bool(doc.company), doc.company, required=tax_invoice_required),
		check(
			"supplier_address",
			_("Supplier address"),
			bool(getattr(doc, "company_address_display", None)),
			_("Missing company address"),
			required=tax_invoice_required,
		),
		check(
			"supplier_vat_number",
			_("Supplier VAT number"),
			bool(company_vat_number),
			company_vat_number or _("Missing company VAT number"),
			required=tax_invoice_required,
		),
		check(
			"customer_name",
			_("Recipient name"),
			bool(getattr(doc, "customer_name", None)),
			getattr(doc, "customer_name", None) or _("Missing recipient name"),
			required=full_invoice,
		),
		check(
			"customer_address",
			_("Recipient address"),
			bool(getattr(doc, "address_display", None)),
			getattr(doc, "address_display", None) or _("Missing recipient address"),
			required=full_invoice,
		),
		check(
			"recipient_vat_number",
			_("Recipient VAT number"),
			bool(recipient_vat_number),
			recipient_vat_number or _("Required on a full tax invoice when the recipient is a VAT vendor."),
			required=bool(full_invoice and recipient_vat_details.get("za_is_vat_vendor")),
		),
		check(
			"serial_number",
			_("Invoice number"),
			bool(doc.name),
			doc.name,
			required=tax_invoice_required,
		),
		check(
			"issue_date",
			_("Issue date"),
			bool(getattr(doc, "posting_date", None)),
			getattr(doc, "posting_date", None),
			required=tax_invoice_required,
		),
		check(
			"line_descriptions",
			_("Item descriptions"),
			bool(doc.items) and all(bool((item.description or "").strip()) for item in doc.items),
			_("One or more items are missing a description"),
			required=tax_invoice_required,
		),
		check(
			"quantities",
			_("Item quantities"),
			bool(doc.items) and all(abs(flt(item.qty)) > 0 for item in doc.items),
			_("One or more items are missing quantity information"),
			required=full_invoice,
		),
		check(
			"value_of_supply",
			_("Value of supply"),
			profile["consideration"] > 0,
			profile["consideration"],
			required=tax_invoice_required,
		),
		check(
			"tax_amount",
			_("Tax amount"),
			doc.total_taxes_and_charges is not None,
			doc.total_taxes_and_charges,
			required=tax_invoice_required,
		),
		check(
			"total_consideration",
			_("Total consideration"),
			getattr(doc, "grand_total", None) is not None,
			getattr(doc, "grand_total", None),
			required=tax_invoice_required,
		),
	]

	missing = [item["label"] for item in checks if item["required"] and not item["ok"]]
	return {
		"sales_invoice": doc.name,
		"status": (
			"not_required"
			if profile["invoice_type"] == "no_tax_invoice_required"
			else ("ready" if not missing else "attention")
		),
		"invoice_type": profile["invoice_type"],
		"recommended_print_format": profile["print_format"],
		"consideration": profile["consideration"],
		"checks": checks,
		"missing": missing,
		"threshold_guidance": {
			"full_tax_invoice_over": FULL_TAX_INVOICE_THRESHOLD,
			"no_tax_invoice_at_or_below": NO_TAX_INVOICE_THRESHOLD,
			"currency": "ZAR",
			"basis": profile["threshold_basis"],
		},
	}


@frappe.whitelist(methods=["GET"])
def get_sales_invoice_print_profile(
	company: str | None = None,
	base_grand_total: float | None = None,
	grand_total: float | None = None,
	is_pos: int = 0,
	is_return: int = 0,
):
	frappe.has_permission("Sales Invoice", "read", throw=True)
	if company:
		frappe.has_permission("Company", "read", company, throw=True)
	return build_sales_invoice_print_profile(
		company=company,
		base_grand_total=base_grand_total,
		grand_total=grand_total,
		is_pos=is_pos,
		is_return=is_return,
		company_currency=get_company_currency(company),
	)


def build_sales_invoice_print_profile(
	company: str | None,
	base_grand_total: float | None = None,
	grand_total: float | None = None,
	is_pos: int = 0,
	is_return: int = 0,
	company_currency: str | None = None,
):
	consideration = abs(flt(base_grand_total or grand_total or 0))
	threshold_basis = "base_grand_total_zar"
	if cint(is_return):
		invoice_type = "credit_note"
	elif company_currency and company_currency != "ZAR":
		# The statutory thresholds are rand amounts. Without a ZAR company-currency
		# amount, use the stricter format instead of understating invoice requirements.
		invoice_type = "full_tax_invoice"
		threshold_basis = "conservative_non_zar_company_currency"
	else:
		invoice_type = get_invoice_type(consideration)
	recommended = get_recommended_print_format(invoice_type)
	is_sa_company = is_company_in_south_africa(company)
	preserve_existing = bool(cint(is_pos))
	return {
		"company": company,
		"consideration": consideration,
		"invoice_type": invoice_type,
		"threshold_basis": threshold_basis,
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
	if invoice_type == "credit_note":
		return "SA Credit Note"
	if invoice_type == "full_tax_invoice":
		return "SA Full Tax Invoice"
	if invoice_type == "abridged_tax_invoice":
		return "SA Abridged Tax Invoice"
	return None


def is_company_in_south_africa(company: str | None):
	if not company:
		return False
	return frappe.db.get_value("Company", company, "country", cache=True) == "South Africa"


def get_company_vat_registration_number(company: str | None):
	if not company:
		return None
	values = frappe.db.get_value("Company", company, ["za_vat_number", "tax_id"], as_dict=True)
	if isinstance(values, dict):
		return values.get("za_vat_number") or values.get("tax_id")
	if isinstance(values, list | tuple):
		return next((value for value in values if value), None)
	return values


def get_company_currency(company: str | None):
	if not company:
		return None
	return frappe.db.get_value("Company", company, "default_currency", cache=True)


def get_party_vat_details(doctype: str, name: str | None):
	if not name:
		return frappe._dict()
	return frappe.db.get_value(doctype, name, ["tax_id", "za_is_vat_vendor"], as_dict=True) or frappe._dict()


def check(key, label, ok, detail=None, required=True):
	return {"key": key, "label": label, "ok": bool(ok), "detail": detail, "required": bool(required)}
