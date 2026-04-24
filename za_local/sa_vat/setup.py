import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CLASSIFICATION_OPTIONS = "\n".join(
	[
		"",
		"Output - A Standard rate (excl capital goods)",
		"Output - B Standard rate (only capital goods)",
		"Output - C Zero Rated (excl goods exported)",
		"Output - D Zero Rated (only goods exported)",
		"Output - E Exempt",
		"Input - A Capital goods and/or services supplied to you (local)",
		"Input - B Capital goods imported",
		"Input - C Other goods supplied to you (excl capital goods)",
		"Input - D Other goods imported (excl capital goods)",
		"SARS Payment/Receipt",
	]
)

ITEM_VAT_CATEGORY_OPTIONS = "\n".join(
	[
		"",
		"Standard Rated",
		"Zero Rated",
		"Export Zero Rated",
		"Exempt",
		"Capital Goods",
		"Imported Capital Goods",
		"Imported Other Goods",
	]
)

VAT_RETURN_SETTING_FIELD_MAP = [
	{
		"field_name": "standard_rate_non_capital",
		"classification": "Output - A Standard rate (excl capital goods)",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "standard_rate_non_capital_2",
		"classification": "Output - A Standard rate (excl capital goods)",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "standard_rate_capital",
		"classification": "Output - B Standard rate (only capital goods)",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "zero_rate_non_exported",
		"classification": "Output - C Zero Rated (excl goods exported)",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "zero_rate_exported",
		"classification": "Output - D Zero Rated (only goods exported)",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "exempt",
		"classification": "Output - E Exempt",
		"reference_doctype": "Sales Invoice",
	},
	{
		"field_name": "input_capital_local",
		"classification": "Input - A Capital goods and/or services supplied to you (local)",
		"reference_doctype": "Purchase Invoice",
	},
	{
		"field_name": "input_capital_import",
		"classification": "Input - B Capital goods imported",
		"reference_doctype": "Purchase Invoice",
	},
	{
		"field_name": "input_goods_local",
		"classification": "Input - C Other goods supplied to you (excl capital goods)",
		"reference_doctype": "Purchase Invoice",
	},
	{
		"field_name": "input_goods_import",
		"classification": "Input - D Other goods imported (excl capital goods)",
		"reference_doctype": "Purchase Invoice",
	},
]

DEFAULT_TEMPLATE_SPECS = {
	"sales": [
		{"field_name": "standard_rate_non_capital", "title": "SA Standard Rated Sales 15%", "rate": 15},
		{
			"field_name": "standard_rate_non_capital_2",
			"title": "SA Standard Rated Sales 15% Additional",
			"rate": 15,
		},
		{"field_name": "standard_rate_capital", "title": "SA Capital Goods Sales 15%", "rate": 15},
		{"field_name": "zero_rate_non_exported", "title": "SA Zero Rated Sales 0%", "rate": 0},
		{"field_name": "zero_rate_exported", "title": "SA Export Zero Rated Sales 0%", "rate": 0},
		{"field_name": "exempt", "title": "SA Exempt Sales 0%", "rate": 0},
	],
	"purchase": [
		{"field_name": "input_capital_local", "title": "SA Capital Purchases 15%", "rate": 15},
		{"field_name": "input_capital_import", "title": "SA Capital Imports 15%", "rate": 15},
		{"field_name": "input_goods_local", "title": "SA Standard Rated Purchases 15%", "rate": 15},
		{"field_name": "input_goods_import", "title": "SA Other Imports 15%", "rate": 15},
	],
}

DEFAULT_VAT_VENDOR_TYPES = [
	{
		"vendor_type": "Standard",
		"description": "Standard South African VAT vendor filing through the normal VAT system.",
		"filing_frequency": "Bi-Monthly",
		"turnover_threshold": 2300000,
		"notes": "Default standard VAT registration profile.",
	},
	{
		"vendor_type": "Micro Business",
		"description": "Smaller VAT vendor profile that may prefer lighter filing cadence where applicable.",
		"filing_frequency": "Quarterly",
		"turnover_threshold": 2300000,
		"notes": "Use only if the practitioner confirms this filing treatment applies.",
	},
	{
		"vendor_type": "Small Business",
		"description": "Small business VAT vendor profile using the standard registration threshold.",
		"filing_frequency": "Bi-Monthly",
		"turnover_threshold": 2300000,
		"notes": "General-purpose small business VAT profile.",
	},
	{
		"vendor_type": "Voluntary",
		"description": "Voluntary VAT registration profile below the compulsory threshold.",
		"filing_frequency": "Bi-Monthly",
		"turnover_threshold": 120000,
		"notes": "Use when the company has voluntarily registered for VAT.",
	},
	{
		"vendor_type": "Foreign Supplier",
		"description": "Foreign electronic services or offshore supplier VAT profile.",
		"filing_frequency": "Bi-Monthly",
		"turnover_threshold": 2300000,
		"notes": "Use only where the practitioner confirms the supplier falls into the foreign supplier VAT regime.",
	},
]

ALLOWED_ITEM_TAX_ACCOUNT_TYPES = {
	"Tax",
	"Chargeable",
	"Income Account",
	"Expense Account",
	"Expenses Included In Valuation",
}


def get_vat_settings(company: str | None = None, create_if_missing: bool = False):
	company = company or get_default_company()
	if not company:
		frappe.throw(_("Select a company before continuing with South Africa VAT setup."))

	existing = frappe.db.get_value("South Africa VAT Settings", {"company": company}, "name")
	if existing:
		return frappe.get_doc("South Africa VAT Settings", existing)

	if not create_if_missing:
		frappe.throw(_("South Africa VAT Settings is not configured for company {0}.").format(company))

	doc = frappe.get_doc(
		{
			"doctype": "South Africa VAT Settings",
			"company": company,
			"default_vat_report_company": company,
		}
	)
	doc.flags.ignore_permissions = True
	return doc


def get_default_company():
	return frappe.db.get_default("company") or frappe.db.get_value("Company", {}, "name", order_by="creation asc")


def get_default_vat_vendor_type():
	return (
		frappe.db.get_value("VAT Vendor Type", "Standard", "name")
		or frappe.db.get_value("VAT Vendor Type", "Voluntary", "name")
		or frappe.db.get_value("VAT Vendor Type", {}, "name", order_by="creation asc")
	)


def seed_vat_vendor_types():
	created = 0
	updated = 0
	for spec in DEFAULT_VAT_VENDOR_TYPES:
		name = frappe.db.get_value("VAT Vendor Type", spec["vendor_type"], "name")
		if name:
			doc = frappe.get_doc("VAT Vendor Type", name)
			changed = False
			for fieldname, value in spec.items():
				if getattr(doc, fieldname) != value:
					setattr(doc, fieldname, value)
					changed = True
			if changed:
				doc.flags.ignore_permissions = True
				doc.save()
				updated += 1
			continue

		doc = frappe.get_doc({"doctype": "VAT Vendor Type", **spec})
		doc.flags.ignore_permissions = True
		doc.insert()
		created += 1

	return {"created": created, "updated": updated}


def ensure_vat_custom_fields():
	create_custom_fields(
		{
			"Account": [
				{
					"fieldname": "custom_sa_vat_compliance_section",
					"fieldtype": "Section Break",
					"label": "South Africa VAT Compliance",
					"insert_after": "include_in_gross",
					"description": "Used to classify manual journal entries for VAT201 reporting.",
				},
				{
					"fieldname": "custom_vat_return_debit_classification",
					"fieldtype": "Select",
					"label": "VAT201 Debit Classification",
					"insert_after": "custom_sa_vat_compliance_section",
					"options": CLASSIFICATION_OPTIONS,
				},
				{
					"fieldname": "custom_vat_return_credit_classification",
					"fieldtype": "Select",
					"label": "VAT201 Credit Classification",
					"insert_after": "custom_vat_return_debit_classification",
					"options": CLASSIFICATION_OPTIONS,
				},
			],
			"Item": [
				{
					"fieldname": "is_zero_rated",
					"fieldtype": "Check",
					"label": "Is Zero Rated",
					"insert_after": "item_group",
					"print_hide": 1,
				},
				{
					"fieldname": "custom_sa_vat_category",
					"fieldtype": "Select",
					"label": "South Africa VAT Category",
					"insert_after": "is_zero_rated",
					"options": ITEM_VAT_CATEGORY_OPTIONS,
					"description": "Used to support VAT201 classification and tax invoice checks.",
				}
			],
			"Sales Invoice Item": [
				{
					"fieldname": "is_zero_rated",
					"fieldtype": "Check",
					"label": "Is Zero Rated",
					"insert_after": "description",
					"fetch_from": "item_code.is_zero_rated",
					"read_only": 1,
					"print_hide": 1,
				},
				{
					"fieldname": "custom_sa_vat_category",
					"fieldtype": "Data",
					"label": "South Africa VAT Category",
					"insert_after": "is_zero_rated",
					"fetch_from": "item_code.custom_sa_vat_category",
					"read_only": 1,
					"print_hide": 1,
				}
			],
			"Purchase Invoice Item": [
				{
					"fieldname": "is_zero_rated",
					"fieldtype": "Check",
					"label": "Is Zero Rated",
					"insert_after": "description",
					"fetch_from": "item_code.is_zero_rated",
					"read_only": 1,
					"print_hide": 1,
				},
				{
					"fieldname": "custom_sa_vat_category",
					"fieldtype": "Data",
					"label": "South Africa VAT Category",
					"insert_after": "is_zero_rated",
					"fetch_from": "item_code.custom_sa_vat_category",
					"read_only": 1,
					"print_hide": 1,
				}
			],
		},
		update=True,
	)


def sync_vat_accounts(settings):
	tracked = []
	for account in [settings.output_vat_account, settings.input_vat_account]:
		if account and account not in tracked:
			tracked.append(account)

	if hasattr(settings, "vat_accounts"):
		settings.vat_accounts = []
	if hasattr(settings, "tax_accounts"):
		settings.tax_accounts = []
	for account in tracked:
		settings.append("vat_accounts", {"doctype": "South Africa VAT Account", "account": account})
	return tracked


def is_valid_item_tax_account(account: str | None, company: str | None) -> bool:
	if not account or not company or not frappe.db.exists("Account", account):
		return False

	account_type, account_company = frappe.get_cached_value("Account", account, ["account_type", "company"])
	return account_company == company and account_type in ALLOWED_ITEM_TAX_ACCOUNT_TYPES


def ensure_default_tax_templates(settings):
	company = settings.company
	if not company:
		frappe.throw(_("Select a company before bootstrapping VAT templates."))

	created = {}
	for spec in DEFAULT_TEMPLATE_SPECS["sales"]:
		created[spec["field_name"]] = ensure_tax_template(
			doctype="Sales Taxes and Charges Template",
			title=f"{spec['title']} - {company}",
			company=company,
			account=settings.output_vat_account,
			rate=spec["rate"],
		)
	for spec in DEFAULT_TEMPLATE_SPECS["purchase"]:
		created[spec["field_name"]] = ensure_tax_template(
			doctype="Purchase Taxes and Charges Template",
			title=f"{spec['title']} - {company}",
			company=company,
			account=settings.input_vat_account,
			rate=spec["rate"],
		)

	for fieldname, template in created.items():
		if not getattr(settings, fieldname, None):
			setattr(settings, fieldname, template)

	ensure_item_tax_templates(settings, company)
	return created


def ensure_item_tax_templates(settings, company):
	item_tax_account = getattr(settings, "item_tax_template_account", None)
	if not item_tax_account:
		frappe.msgprint(
			_(
				"Automatic Item Tax Template creation is inactive because no Item Tax Template Account is set for company {0}. Select a valid tax, chargeable, income, or expense account if you want the templates generated automatically."
			).format(frappe.bold(company)),
			indicator="yellow",
		)
		return

	if not is_valid_item_tax_account(item_tax_account, company):
		frappe.msgprint(
			_(
				"Skipping automatic Item Tax Template creation because Item Tax Template Account {0} is not a valid Item Tax account for company {1}. Use an account of type Tax, Chargeable, Income, or Expense if you want item tax templates generated automatically."
			).format(frappe.bold(item_tax_account), frappe.bold(company)),
			indicator="yellow",
		)
		return

	for title, rate in [("SA Item Tax 15%", 15), ("SA Item Tax 0%", 0)]:
		existing_name = frappe.db.get_value(
			"Item Tax Template",
			{"title": f"{title} - {company}", "company": company},
			"name",
		)
		if existing_name:
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Item Tax Template",
				"title": f"{title} - {company}",
				"company": company,
				"taxes": [
					{
						"doctype": "Item Tax Template Detail",
						"tax_type": item_tax_account,
						"tax_rate": rate,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)


def ensure_tax_template(doctype, title, company, account, rate):
	existing_name = frappe.db.get_value(doctype, {"title": title, "company": company}, "name")
	if existing_name:
		doc = frappe.get_doc(doctype, existing_name)
	else:
		doc = frappe.new_doc(doctype)
		doc.title = title
		doc.company = company

	doc.taxes = []
	doc.append(
		"taxes",
		{
			"charge_type": "On Net Total",
			"account_head": account,
			"rate": rate,
			"description": title,
		},
	)
	doc.flags.ignore_permissions = True
	if existing_name:
		doc.save()
	else:
		doc.insert()
	return doc.name


@frappe.whitelist()
def bootstrap_company_vat_setup(company: str | None = None):
	settings = get_vat_settings(company, create_if_missing=True)
	company = company or settings.company
	if company and not settings.company:
		settings.company = company
	settings.default_vat_report_company = settings.company
	ensure_default_tax_templates(settings)
	sync_vat_accounts(settings)
	settings.flags.ignore_permissions = True
	if settings.is_new():
		settings.insert()
	else:
		settings.save()
	return {
		"settings": settings.name,
		"vat_accounts": [row.account for row in settings.vat_accounts],
		"tax_accounts": [row.account for row in settings.vat_accounts],
	}


def migrate_legacy_vat_account_rows():
	if not frappe.db.table_exists("South Africa VAT Tax Account"):
		return 0

	legacy_rows = frappe.get_all(
		"South Africa VAT Tax Account",
		fields=["parent", "parenttype", "account", "idx"],
		filters={"parenttype": "South Africa VAT Settings"},
		order_by="parent asc, idx asc",
	)

	migrated = 0
	for row in legacy_rows:
		exists = frappe.db.exists(
			"South Africa VAT Account",
			{
				"parent": row.parent,
				"parenttype": "South Africa VAT Settings",
				"parentfield": "vat_accounts",
				"account": row.account,
			},
		)
		if exists:
			continue

		frappe.get_doc(
			{
				"doctype": "South Africa VAT Account",
				"parent": row.parent,
				"parenttype": "South Africa VAT Settings",
				"parentfield": "vat_accounts",
				"account": row.account,
				"idx": row.idx,
			}
		).insert(ignore_permissions=True)
		migrated += 1

	return migrated
