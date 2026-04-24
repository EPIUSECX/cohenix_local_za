# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, formatdate, getdate, today

from za_local.sa_vat.setup import VAT_RETURN_SETTING_FIELD_MAP, get_vat_settings

OUTPUT_STANDARD_NON_CAPITAL = "Output - A Standard rate (excl capital goods)"
OUTPUT_STANDARD_CAPITAL = "Output - B Standard rate (only capital goods)"
OUTPUT_ZERO_LOCAL = "Output - C Zero Rated (excl goods exported)"
OUTPUT_ZERO_EXPORTED = "Output - D Zero Rated (only goods exported)"
OUTPUT_EXEMPT = "Output - E Exempt"
INPUT_CAPITAL_LOCAL = "Input - A Capital goods and/or services supplied to you (local)"
INPUT_CAPITAL_IMPORTED = "Input - B Capital goods imported"
INPUT_OTHER_LOCAL = "Input - C Other goods supplied to you (excl capital goods)"
INPUT_OTHER_IMPORTED = "Input - D Other goods imported (excl capital goods)"
SARS_PAYMENT_RECEIPT = "SARS Payment/Receipt"


class VAT201Return(Document):
	def validate(self):
		self.validate_dates()
		self.prevent_duplicate_open_return()
		self.ensure_period_dates()
		self.set_submission_period()
		self.set_vat_registration_number()
		self.calculate_totals()

	def validate_dates(self):
		if getdate(self.submission_date) > getdate(today()):
			frappe.throw(_("Submission Date cannot be in the future."))
		if self.from_date and self.to_date and getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date cannot be after To Date."))

	def prevent_duplicate_open_return(self):
		if not (self.company and self.from_date and self.to_date):
			return

		existing = frappe.get_all(
			"VAT201 Return",
			filters={
				"company": self.company,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"docstatus": ["!=", 2],
				"name": ["!=", self.name or ""],
			},
			fields=["name", "status", "docstatus"],
			limit=1,
		)
		if existing:
			frappe.throw(
				_(
					"VAT201 Return {0} already exists for company {1} and period {2} to {3}. Cancel or amend the existing working paper before creating another."
				).format(existing[0].name, self.company, self.from_date, self.to_date)
			)

	def ensure_period_dates(self):
		if not hasattr(self, "from_date"):
			self.from_date = None
		if not hasattr(self, "to_date"):
			self.to_date = None

	def set_submission_period(self):
		if self.from_date and self.to_date:
			self.submission_period = f"{formatdate(getdate(self.from_date))} to {formatdate(getdate(self.to_date))}"
		else:
			self.submission_period = None

	def set_vat_registration_number(self):
		if self.company:
			self.vat_registration_number = frappe.db.get_value("Company", self.company, "za_vat_number") or ""

	def calculate_totals(self):
		transactions = [row for row in self.transactions if not row.is_cancelled]

		self.standard_rated_supplies_non_capital = sum(
			flt(row.incl_tax_amount) for row in transactions if row.classification == OUTPUT_STANDARD_NON_CAPITAL
		)
		self.standard_rated_supplies_capital = sum(
			flt(row.incl_tax_amount) for row in transactions if row.classification == OUTPUT_STANDARD_CAPITAL
		)
		self.zero_rated_supplies_local = sum(
			flt(row.incl_tax_amount) for row in transactions if row.classification == OUTPUT_ZERO_LOCAL
		)
		self.zero_rated_supplies_exported = sum(
			flt(row.incl_tax_amount) for row in transactions if row.classification == OUTPUT_ZERO_EXPORTED
		)
		self.standard_rated_output_non_capital = sum(
			flt(row.tax_amount) for row in transactions if row.classification == OUTPUT_STANDARD_NON_CAPITAL
		)
		self.standard_rated_output_capital = sum(
			flt(row.tax_amount) for row in transactions if row.classification == OUTPUT_STANDARD_CAPITAL
		)
		self.capital_goods_input_local = sum(
			flt(row.tax_amount) for row in transactions if row.classification == INPUT_CAPITAL_LOCAL
		)
		self.capital_goods_input_imported = sum(
			flt(row.tax_amount) for row in transactions if row.classification == INPUT_CAPITAL_IMPORTED
		)
		self.other_goods_services_input_local = sum(
			flt(row.tax_amount) for row in transactions if row.classification == INPUT_OTHER_LOCAL
		)
		self.other_goods_services_input_imported = sum(
			flt(row.tax_amount) for row in transactions if row.classification == INPUT_OTHER_IMPORTED
		)
		self.exempt_supplies = sum(flt(row.incl_tax_amount) for row in transactions if row.classification == OUTPUT_EXEMPT)

		self.standard_rated_supplies = flt(self.standard_rated_supplies_non_capital) + flt(
			self.standard_rated_supplies_capital
		)
		self.zero_rated_supplies = flt(self.zero_rated_supplies_local) + flt(self.zero_rated_supplies_exported)
		self.total_supplies = (
			flt(self.standard_rated_supplies) + flt(self.zero_rated_supplies) + flt(self.exempt_supplies)
		)
		self.standard_rated_output = flt(self.standard_rated_output_non_capital) + flt(
			self.standard_rated_output_capital
		)
		self.capital_goods_input = flt(self.capital_goods_input_local) + flt(self.capital_goods_input_imported)
		self.other_goods_services_input = flt(self.other_goods_services_input_local) + flt(
			self.other_goods_services_input_imported
		)

		self.total_output_tax = (
			flt(self.standard_rated_output)
			+ flt(self.change_in_use_output)
			+ flt(self.bad_debts_output)
			+ flt(self.other_output)
		)
		self.total_input_tax = (
			flt(self.capital_goods_input)
			+ flt(self.other_goods_services_input)
			+ flt(self.change_in_use_input)
			+ flt(self.bad_debts_input)
		)
		if self.total_output_tax > self.total_input_tax:
			self.vat_payable = self.total_output_tax - self.total_input_tax
			self.vat_refundable = 0
		else:
			self.vat_refundable = self.total_input_tax - self.total_output_tax
			self.vat_payable = 0

		if self.vat_payable > 0:
			self.total_amount_payable = self.vat_payable - flt(self.diesel_refund)
			if self.total_amount_payable < 0:
				self.vat_refundable = abs(self.total_amount_payable)
				self.total_amount_payable = 0
		else:
			self.total_amount_payable = 0
			self.vat_refundable = self.vat_refundable + flt(self.diesel_refund)

	def on_submit(self):
		unclassified = [row for row in self.transactions if not row.classification and not row.is_cancelled]
		if unclassified:
			frappe.throw(
				_("Please classify the remaining {0} unclassified transactions before submitting.").format(
					len(unclassified)
				)
			)
		if self.status == "Draft":
			self.status = "Prepared"
		if not self.submission_reference:
			self.submission_reference = f"VAT201-{self.name}-{frappe.utils.random_string(8)}"
		self.db_update()

	@frappe.whitelist()
	def submit_to_sars(self):
		frappe.throw(
			_(
				"Direct SARS electronic submission is not supported in this release. Export your VAT201 working papers and complete filing manually through SARS eFiling."
			)
		)

	@frappe.whitelist()
	def get_summary_rows(self):
		return [
			{"box": "1", "label": "Standard rated supplies (non-capital)", "amount": self.standard_rated_supplies_non_capital},
			{"box": "1A", "label": "Standard rated supplies (capital goods)", "amount": self.standard_rated_supplies_capital},
			{"box": "2", "label": "Zero rated supplies (local)", "amount": self.zero_rated_supplies_local},
			{"box": "2A", "label": "Zero rated supplies (exports)", "amount": self.zero_rated_supplies_exported},
			{"box": "3", "label": "Exempt supplies", "amount": self.exempt_supplies},
			{"box": "4", "label": "Output tax on standard rated supplies", "amount": self.standard_rated_output_non_capital},
			{"box": "4A", "label": "Output tax on capital goods", "amount": self.standard_rated_output_capital},
			{"box": "14", "label": "Input tax on capital goods (local)", "amount": self.capital_goods_input_local},
			{"box": "14A", "label": "Input tax on capital goods (imported)", "amount": self.capital_goods_input_imported},
			{"box": "15", "label": "Input tax on other goods and services (local)", "amount": self.other_goods_services_input_local},
			{"box": "15A", "label": "Input tax on other goods and services (imported)", "amount": self.other_goods_services_input_imported},
			{"box": "A", "label": "Total output tax", "amount": self.total_output_tax},
			{"box": "B", "label": "Total input tax", "amount": self.total_input_tax},
			{"box": "PAYABLE", "label": "VAT payable", "amount": self.vat_payable},
			{"box": "REFUND", "label": "VAT refundable", "amount": self.vat_refundable},
		]

	@frappe.whitelist()
	def get_linked_transaction_rows(self):
		rows = []
		for row in self.transactions:
			rows.append(
				{
					"gl_entry": row.gl_entry,
					"voucher_type": row.voucher_type,
					"voucher_no": row.voucher_no,
					"posting_date": row.posting_date,
					"taxes_and_charges": row.taxes_and_charges,
					"tax_account_debit": row.tax_account_debit,
					"tax_account_credit": row.tax_account_credit,
					"tax_amount": row.tax_amount,
					"incl_tax_amount": row.incl_tax_amount,
					"classification": row.classification,
					"is_cancelled": row.is_cancelled,
				}
			)
		return rows

	@frappe.whitelist()
	def get_vat_transactions(self):
		if not self.company or not self.from_date or not self.to_date:
			frappe.throw(_("Company, From Date, and To Date are required."))
		if self.docstatus != 0 or self.status != "Draft":
			frappe.throw(_("Only draft VAT201 working papers can refresh linked transactions."))

		settings = get_vat_settings(self.company)
		if not settings.output_vat_account or not settings.input_vat_account:
			frappe.throw(_("VAT accounts are not configured in South Africa VAT Settings for company {0}.").format(self.company))

		rows = []
		rows.extend(self.get_sales_invoice_rows(settings))
		rows.extend(self.get_purchase_invoice_rows(settings))
		rows.extend(self.get_journal_entry_rows(settings))

		self.transactions = []
		for row in rows:
			self.append("transactions", row)

		self.calculate_totals()
		self.set_submission_period()
		return {
			"transaction_count": len(rows),
			"unclassified_count": len([row for row in rows if not row.get("classification") and not row.get("is_cancelled")]),
		}

	def get_sales_invoice_rows(self, settings):
		rows = []
		standard_rate = flt(settings.standard_vat_rate or 15) / 100
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={
				"company": self.company,
				"docstatus": 1,
				"posting_date": ["between", [self.from_date, self.to_date]],
			},
			fields=["name", "posting_date", "taxes_and_charges", "base_net_total", "is_return"],
		)
		for invoice in invoices:
			sign = -1 if cint(invoice.is_return) else 1
			default_classification = self.get_template_classification(
				settings, invoice.taxes_and_charges, "Sales Invoice"
			)
			item_groups = {}
			for item in frappe.get_all(
				"Sales Invoice Item",
				filters={"parent": invoice.name},
				fields=["base_net_amount", "custom_sa_vat_category"],
			):
				classification = self.classify_sales_item_category(item.custom_sa_vat_category) or default_classification
				if not classification:
					continue
				item_groups.setdefault(classification, 0)
				item_groups[classification] += flt(item.base_net_amount) * sign

			taxes = frappe.get_all(
				"Sales Taxes and Charges",
				filters={"parent": invoice.name, "account_head": settings.output_vat_account},
				fields=["name", "rate", "base_tax_amount as tax_amount", "total"],
				order_by="idx asc",
			)
			if item_groups:
				for classification, amount in item_groups.items():
					tax_amount = amount * standard_rate if classification in (
						OUTPUT_STANDARD_NON_CAPITAL,
						OUTPUT_STANDARD_CAPITAL,
					) else 0
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Sales Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": 0,
							"tax_account_credit": abs(flt(tax_amount)) if tax_amount > 0 else 0,
							"tax_amount": flt(tax_amount),
							"incl_tax_amount": flt(amount),
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": f"Grouped from item VAT categories; template {invoice.taxes_and_charges}",
						}
					)
			elif taxes:
				for tax in taxes:
					classification = default_classification
					if not classification and flt(tax.tax_amount) == 0:
						classification = OUTPUT_ZERO_LOCAL
					elif not classification:
						classification = OUTPUT_STANDARD_NON_CAPITAL
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Sales Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": 0,
							"tax_account_credit": abs(flt(tax.tax_amount) * sign) if flt(tax.tax_amount) * sign > 0 else 0,
							"tax_amount": flt(tax.tax_amount) * sign,
							"incl_tax_amount": flt(tax.total or invoice.base_net_total) * sign,
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": f"Fallback template classification: {invoice.taxes_and_charges}",
						}
					)
			else:
				classification = self.classify_sales_invoice_without_tax(invoice)
				if classification:
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Sales Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": 0,
							"tax_account_credit": 0,
							"tax_amount": 0,
							"incl_tax_amount": flt(invoice.base_net_total) * sign,
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": "Classified from item VAT categories",
						}
					)
		return rows

	def get_purchase_invoice_rows(self, settings):
		rows = []
		standard_rate = flt(settings.standard_vat_rate or 15) / 100
		invoices = frappe.get_all(
			"Purchase Invoice",
			filters={
				"company": self.company,
				"docstatus": 1,
				"posting_date": ["between", [self.from_date, self.to_date]],
			},
			fields=["name", "posting_date", "taxes_and_charges", "base_net_total", "is_return"],
		)
		for invoice in invoices:
			sign = -1 if cint(invoice.is_return) else 1
			default_classification = self.get_template_classification(
				settings, invoice.taxes_and_charges, "Purchase Invoice"
			)
			item_groups = {}
			for item in frappe.get_all(
				"Purchase Invoice Item",
				filters={"parent": invoice.name},
				fields=["base_net_amount", "custom_sa_vat_category"],
			):
				classification = self.classify_purchase_item_category(item.custom_sa_vat_category) or default_classification
				if not classification:
					continue
				item_groups.setdefault(classification, 0)
				item_groups[classification] += flt(item.base_net_amount) * sign

			taxes = frappe.get_all(
				"Purchase Taxes and Charges",
				filters={"parent": invoice.name, "account_head": settings.input_vat_account},
				fields=["name", "rate", "tax_amount", "total"],
				order_by="idx asc",
			)
			if item_groups:
				for classification, amount in item_groups.items():
					tax_amount = amount * standard_rate if classification in (
						INPUT_CAPITAL_LOCAL,
						INPUT_CAPITAL_IMPORTED,
						INPUT_OTHER_LOCAL,
						INPUT_OTHER_IMPORTED,
					) else 0
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Purchase Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": abs(flt(tax_amount)) if tax_amount > 0 else 0,
							"tax_account_credit": abs(flt(tax_amount)) if tax_amount < 0 else 0,
							"tax_amount": flt(tax_amount),
							"incl_tax_amount": flt(amount),
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": f"Grouped from item VAT categories; template {invoice.taxes_and_charges}",
						}
					)
			elif taxes:
				for tax in taxes:
					classification = default_classification or INPUT_OTHER_LOCAL
					signed_tax = flt(tax.tax_amount) * sign
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Purchase Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": abs(signed_tax) if signed_tax > 0 else 0,
							"tax_account_credit": abs(signed_tax) if signed_tax < 0 else 0,
							"tax_amount": signed_tax,
							"incl_tax_amount": flt(tax.total or invoice.base_net_total) * sign,
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": f"Fallback template classification: {invoice.taxes_and_charges}",
						}
					)
			else:
				classification = self.classify_purchase_invoice_without_tax(invoice)
				if classification:
					rows.append(
						{
							"gl_entry": None,
							"voucher_type": "Purchase Invoice",
							"voucher_no": invoice.name,
							"posting_date": invoice.posting_date,
							"taxes_and_charges": invoice.taxes_and_charges,
							"tax_account_debit": 0,
							"tax_account_credit": 0,
							"tax_amount": 0,
							"incl_tax_amount": flt(invoice.base_net_total) * sign,
							"classification": classification,
							"is_cancelled": 0,
							"classification_debugging": "Classified from item VAT categories",
						}
					)
		return rows

	def get_journal_entry_rows(self, settings):
		rows = []
		tax_accounts = {row.account for row in settings.tax_accounts if row.account}
		classified_accounts = set(
			frappe.get_all(
				"Account",
				filters={"company": self.company},
				or_filters=[
					["custom_vat_return_debit_classification", "not in", ["", None]],
					["custom_vat_return_credit_classification", "not in", ["", None]],
				],
				pluck="name",
			)
		)
		gl_rows = frappe.get_all(
			"GL Entry",
			filters={
				"company": self.company,
				"voucher_type": "Journal Entry",
				"posting_date": ["between", [self.from_date, self.to_date]],
				"account": ["in", list(tax_accounts | classified_accounts)],
				"is_cancelled": ["in", [0, 1]],
			},
			fields=["name", "voucher_no", "posting_date", "account", "debit", "credit", "is_cancelled"],
			order_by="posting_date asc, creation asc",
		)

		by_voucher = {}
		for row in gl_rows:
			by_voucher.setdefault(row.voucher_no, []).append(row)

		for voucher_no, voucher_rows in by_voucher.items():
			jea_rows = frappe.get_all(
				"Journal Entry Account",
				filters={"parent": voucher_no},
				fields=["account", "debit_in_account_currency as debit", "credit_in_account_currency as credit", "idx"],
				order_by="idx asc",
			)
			tax_entries = [row for row in voucher_rows if row.account in tax_accounts]
			if tax_entries:
				available_non_tax = [row for row in jea_rows if row.account not in tax_accounts]
				for entry in tax_entries:
					classification = None
					debug = []
					tax_amount = flt(entry.debit) or -flt(entry.credit)
					tax_side = "debit" if flt(entry.debit) > 0 else "credit"
					candidate = self.find_matching_non_tax_leg(available_non_tax, tax_side)
					if candidate:
						available_non_tax.remove(candidate)
						classification = self.get_account_classification(candidate.account, tax_side)
						debug.append(f"Matched non-tax leg {candidate.account}")
						incl_tax_amount = (
							(flt(candidate.debit) if tax_side == "debit" else -flt(candidate.credit)) + tax_amount
						)
					else:
						incl_tax_amount = tax_amount
						if self.is_sars_settlement_entry(jea_rows, tax_accounts):
							classification = SARS_PAYMENT_RECEIPT
							debug.append("Matched bank/cash settlement pattern")

					rows.append(
						{
							"gl_entry": entry.name,
							"voucher_type": "Journal Entry",
							"voucher_no": voucher_no,
							"posting_date": entry.posting_date,
							"taxes_and_charges": "",
							"tax_account_debit": flt(entry.debit),
							"tax_account_credit": flt(entry.credit),
							"tax_amount": tax_amount,
							"incl_tax_amount": incl_tax_amount,
							"classification": classification,
							"is_cancelled": entry.is_cancelled,
							"classification_debugging": "\n".join(debug),
						}
					)
			else:
				for entry in voucher_rows:
					side = "debit" if flt(entry.debit) > 0 else "credit"
					classification = self.get_account_classification(entry.account, side)
					if not classification:
						continue
					rows.append(
						{
							"gl_entry": entry.name,
							"voucher_type": "Journal Entry",
							"voucher_no": voucher_no,
							"posting_date": entry.posting_date,
							"taxes_and_charges": "",
							"tax_account_debit": flt(entry.debit),
							"tax_account_credit": flt(entry.credit),
							"tax_amount": 0,
							"incl_tax_amount": flt(entry.debit) if side == "debit" else -flt(entry.credit),
							"classification": classification,
							"is_cancelled": entry.is_cancelled,
							"classification_debugging": f"Classified directly from account {entry.account}",
						}
					)

		return rows

	def find_matching_non_tax_leg(self, rows, tax_side):
		candidates = []
		for row in rows:
			if tax_side == "debit" and flt(row.debit) > 0:
				if self.get_account_classification(row.account, "debit"):
					candidates.append(row)
			elif tax_side == "credit" and flt(row.credit) > 0:
				if self.get_account_classification(row.account, "credit"):
					candidates.append(row)
		candidates.sort(key=lambda row: flt(row.debit or row.credit), reverse=True)
		return candidates[0] if candidates else None

	def is_sars_settlement_entry(self, rows, tax_accounts):
		non_tax_rows = [row for row in rows if row.account not in tax_accounts]
		if len(non_tax_rows) != 1:
			return False
		account_type = frappe.get_cached_value("Account", non_tax_rows[0].account, "account_type")
		return account_type in {"Bank", "Cash"}

	def get_account_classification(self, account, side):
		fieldname = (
			"custom_vat_return_debit_classification" if side == "debit" else "custom_vat_return_credit_classification"
		)
		return frappe.db.get_value("Account", account, fieldname)

	def get_template_classification(self, settings, template, reference_doctype):
		for entry in VAT_RETURN_SETTING_FIELD_MAP:
			if entry["reference_doctype"] != reference_doctype:
				continue
			if getattr(settings, entry["field_name"], None) == template:
				return entry["classification"]
		return None

	def classify_sales_invoice_without_tax(self, invoice):
		categories = set(
			value
			for value in frappe.get_all(
				"Sales Invoice Item",
				filters={"parent": invoice.name},
				pluck="custom_sa_vat_category",
			)
			if value
		)
		if "Exempt" in categories:
			return OUTPUT_EXEMPT
		if "Export Zero Rated" in categories:
			return OUTPUT_ZERO_EXPORTED
		if "Zero Rated" in categories:
			return OUTPUT_ZERO_LOCAL
		return None

	def classify_sales_item_category(self, category):
		return {
			"Export Zero Rated": OUTPUT_ZERO_EXPORTED,
			"Zero Rated": OUTPUT_ZERO_LOCAL,
			"Exempt": OUTPUT_EXEMPT,
			"Capital Goods": OUTPUT_STANDARD_CAPITAL,
			"Standard Rated": OUTPUT_STANDARD_NON_CAPITAL,
		}.get(category)

	def classify_purchase_invoice_without_tax(self, invoice):
		categories = set(
			value
			for value in frappe.get_all(
				"Purchase Invoice Item",
				filters={"parent": invoice.name},
				pluck="custom_sa_vat_category",
			)
			if value
		)
		if "Imported Capital Goods" in categories:
			return INPUT_CAPITAL_IMPORTED
		if "Capital Goods" in categories:
			return INPUT_CAPITAL_LOCAL
		if "Imported Other Goods" in categories:
			return INPUT_OTHER_IMPORTED
		if categories:
			return INPUT_OTHER_LOCAL
		return None

	def classify_purchase_item_category(self, category):
		return {
			"Capital Goods": INPUT_CAPITAL_LOCAL,
			"Imported Capital Goods": INPUT_CAPITAL_IMPORTED,
			"Imported Other Goods": INPUT_OTHER_IMPORTED,
			"Standard Rated": INPUT_OTHER_LOCAL,
			"Zero Rated": INPUT_OTHER_LOCAL,
			"Exempt": INPUT_OTHER_LOCAL,
		}.get(category)
