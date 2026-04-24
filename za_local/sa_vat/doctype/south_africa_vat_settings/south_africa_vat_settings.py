import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from za_local.sa_vat.setup import (
	bootstrap_company_vat_setup,
	ensure_default_tax_templates,
	get_default_company,
	get_default_vat_vendor_type,
	is_valid_item_tax_account,
	sync_vat_accounts,
)


class SouthAfricaVATSettings(Document):
	def load_from_db(self):
		super().load_from_db()
		self._set_vat_registration_number_from_company()
		self._ensure_default_vat_rates_on_load()
		self._set_mapping_doctype_defaults()

	def validate(self):
		self.ensure_company_default()
		self._set_mapping_doctype_defaults()
		self._set_vat_registration_number_from_company()
		self.validate_vat_rates()
		self.validate_vat_accounts()
		self.validate_company_vat_number()
		self.validate_threshold_configuration()
		sync_vat_accounts(self)

	def on_update(self):
		self.update_accounts_settings()
		self.update_tax_templates()
		sync_vat_accounts(self)

	def update_accounts_settings(self):
		accounts_settings = frappe.get_doc("Accounts Settings")
		if hasattr(accounts_settings, "standard_tax_rate") and accounts_settings.standard_tax_rate != self.standard_vat_rate:
			accounts_settings.standard_tax_rate = self.standard_vat_rate
			accounts_settings.save()

	def ensure_company_default(self):
		if not self.company:
			self.company = get_default_company()

		if self.company and not self.default_vat_report_company:
			self.default_vat_report_company = self.company

		if not self.vat_vendor_type:
			self.vat_vendor_type = get_default_vat_vendor_type()

		if not self.vat_filing_day:
			self.vat_filing_day = 25

	def _set_mapping_doctype_defaults(self):
		self.output_tax_doctype = "Sales Taxes and Charges Template"
		self.input_tax_doctype = "Purchase Taxes and Charges Template"

	def _set_vat_registration_number_from_company(self):
		company = self.default_vat_report_company or self.company
		if company:
			self.vat_registration_number = frappe.db.get_value("Company", company, "za_vat_number") or ""
		else:
			self.vat_registration_number = ""

	def _ensure_default_vat_rates_on_load(self):
		self._prune_blank_vat_rates()
		if self.vat_rates:
			return

		standard = getattr(self, "standard_vat_rate", None) or 15
		self.append(
			"vat_rates",
			{
				"rate_name": "Standard Rate",
				"rate": standard,
				"is_standard_rate": 1,
				"description": "Standard VAT rate for South Africa",
			},
		)
		if getattr(self, "enable_zero_rated_items", 1):
			self.append(
				"vat_rates",
				{
					"rate_name": "Zero Rate",
					"rate": 0,
					"is_zero_rated": 1,
					"description": "Zero-rated items (0% VAT)",
				},
			)
		if getattr(self, "enable_exempt_items", 1):
			self.append(
				"vat_rates",
				{
					"rate_name": "Exempt",
					"rate": 0,
					"is_exempt": 1,
					"description": "VAT exempt items",
				},
			)

	def _prune_blank_vat_rates(self):
		if not self.vat_rates:
			return

		clean_rows = []
		for row in self.vat_rates:
			has_content = any(
				[
					(row.rate_name or "").strip(),
					flt(row.rate),
					row.is_standard_rate,
					row.is_zero_rated,
					row.is_exempt,
					(row.description or "").strip(),
				]
			)
			if has_content:
				clean_rows.append(row.as_dict(no_default_fields=True))

		if len(clean_rows) != len(self.vat_rates):
			self.set("vat_rates", [])
			for row in clean_rows:
				self.append("vat_rates", row)

	def validate_vat_rates(self):
		self._ensure_default_vat_rates_on_load()

		rows_by_name = {(row.rate_name or "").strip().lower(): row for row in self.vat_rates if row.rate_name}

		standard_rate = rows_by_name.get("standard rate")
		if not standard_rate:
			self.append(
				"vat_rates",
				{
					"rate_name": "Standard Rate",
					"rate": self.standard_vat_rate,
					"is_standard_rate": 1,
					"description": "Standard VAT rate for South Africa",
				},
			)
		else:
			standard_rate.rate = self.standard_vat_rate
			standard_rate.is_standard_rate = 1

		if self.enable_zero_rated_items and "zero rate" not in rows_by_name:
			self.append(
				"vat_rates",
				{
					"rate_name": "Zero Rate",
					"rate": 0,
					"is_zero_rated": 1,
					"description": "Zero-rated items (0% VAT)",
				},
			)

		if self.enable_exempt_items and "exempt" not in rows_by_name:
			self.append(
				"vat_rates",
				{
					"rate_name": "Exempt",
					"rate": 0,
					"is_exempt": 1,
					"description": "VAT exempt items",
				},
			)

		for rate in self.vat_rates:
			rate.rate = flt(rate.rate)

	def validate_vat_accounts(self):
		if self.input_vat_account and self.input_vat_account == self.output_vat_account:
			frappe.msgprint(
				_(
					"Input VAT Account and Output VAT Account are the same. This legacy South African VAT control-account pattern is allowed, but confirm your VAT201 mappings and tax templates carefully."
				),
				indicator="yellow",
			)

		for account_field in ["input_vat_account", "output_vat_account"]:
			account = getattr(self, account_field)
			if account and not frappe.db.exists("Account", account):
				frappe.throw(_("Account {0} does not exist").format(account))

	def validate_company_vat_number(self):
		company = self.company or self.default_vat_report_company
		if not company:
			return

		vat_number = frappe.db.get_value("Company", company, "za_vat_number")
		if not vat_number:
			frappe.msgprint(
				_(
					"VAT Registration Number is not set on the selected company. Set it on the Company record to ensure VAT201 returns and tax invoices are correct."
				),
				indicator="yellow",
			)
			return

		if not re.match(r"^[0-9]{10}$", vat_number):
			frappe.throw(_("Company VAT Registration Number must be 10 digits."))

		if not vat_number.startswith("4"):
			frappe.msgprint(
				_("South African VAT Registration Numbers typically start with '4'."),
				indicator="yellow",
			)

	def validate_threshold_configuration(self):
		if self.vat_registration_threshold and self.vat_registration_threshold != 2300000:
			frappe.msgprint(
				_(
					"Current compulsory VAT registration threshold is R2,300,000 effective 1 April 2026. Update only if SARS changes it."
				),
				indicator="yellow",
			)
		if self.vat_voluntary_threshold and self.vat_voluntary_threshold != 120000:
			frappe.msgprint(
				_(
					"Current voluntary VAT registration threshold is R120,000 effective 1 April 2026. Update only if SARS changes it."
				),
				indicator="yellow",
			)

	def update_tax_templates(self):
		if not self.default_vat_report_company:
			frappe.msgprint(
				_(
					"Default VAT Report Company is not set. Skipping tax template creation until a company is selected."
				),
				indicator="yellow",
			)
			return

		self.create_or_update_legacy_tax_template("Sales", self.output_vat_account)
		self.create_or_update_legacy_tax_template("Purchase", self.input_vat_account)
		self.update_item_tax_templates()
		ensure_default_tax_templates(self)

	def create_or_update_legacy_tax_template(self, template_type, account):
		template_title = f"South Africa VAT {self.standard_vat_rate}% - {template_type}"
		doctype_name = f"{template_type} Taxes and Charges Template"

		existing_name = frappe.db.get_value(
			doctype_name,
			{"title": template_title, "company": self.default_vat_report_company},
			"name",
		)
		if existing_name:
			tax_template = frappe.get_doc(doctype_name, existing_name)
		else:
			tax_template = frappe.new_doc(doctype_name)
			tax_template.title = template_title
			tax_template.company = self.default_vat_report_company
			tax_template.is_default = 1

		tax_template.taxes = []
		for rate in self.vat_rates:
			if rate.is_exempt:
				continue
			tax_template.append(
				"taxes",
				{
					"charge_type": "On Net Total",
					"account_head": account,
					"description": rate.rate_name,
					"rate": rate.rate,
				},
			)
		tax_template.save()
		return tax_template.name

	def update_item_tax_templates(self):
		company = self.default_vat_report_company
		if not is_valid_item_tax_account(self.output_vat_account, company):
			frappe.msgprint(
				_(
					"Skipping automatic Item Tax Template updates because Output VAT Account {0} is not a valid Item Tax account for company {1}. Use an account of type Tax, Chargeable, Income, or Expense if you want item tax templates generated automatically."
				).format(frappe.bold(self.output_vat_account or _("(not set)")), frappe.bold(company or _("(not set)"))),
				indicator="yellow",
			)
			return

		for rate in self.vat_rates:
			rate_value = flt(rate.rate)
			title = f"South Africa VAT {rate.rate_name} ({rate_value:.2f}%)"
			existing_name = frappe.db.get_value("Item Tax Template", {"title": title, "company": company}, "name")
			if existing_name:
				doc = frappe.get_doc("Item Tax Template", existing_name)
				doc.taxes = []
			else:
				doc = frappe.new_doc("Item Tax Template")
				doc.title = title
				doc.company = company

			doc.append(
				"taxes",
				{
					"tax_type": self.output_vat_account,
					"tax_rate": rate_value,
				},
			)
			doc.flags.ignore_permissions = True
			if existing_name:
				doc.save()
			else:
				doc.insert()

	@frappe.whitelist()
	def bootstrap_defaults(self):
		return bootstrap_company_vat_setup(self.company or self.default_vat_report_company)

	@frappe.whitelist()
	def sync_vat_accounts(self):
		tracked = sync_vat_accounts(self)
		self.flags.ignore_permissions = True
		if self.is_new():
			self.insert()
		else:
			self.save()
		return {"tax_accounts": tracked}
