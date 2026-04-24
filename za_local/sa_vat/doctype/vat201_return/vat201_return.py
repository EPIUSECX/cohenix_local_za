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
CLASSIFIED = "Classified"
NEEDS_REVIEW = "Needs Review"
EXCLUDED = "Excluded"
SALES_STANDARD_CLASSIFICATIONS = {OUTPUT_STANDARD_NON_CAPITAL, OUTPUT_STANDARD_CAPITAL}
PURCHASE_INPUT_CLASSIFICATIONS = {
	INPUT_CAPITAL_LOCAL,
	INPUT_CAPITAL_IMPORTED,
	INPUT_OTHER_LOCAL,
	INPUT_OTHER_IMPORTED,
}


class VAT201Return(Document):
	def validate(self):
		self.validate_dates()
		self.prevent_duplicate_open_return()
		self.ensure_period_dates()
		self.set_submission_period()
		self.set_vat_registration_number()
		self.calculate_totals()
		self.set_review_summary()

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
		transactions = [
			row
			for row in self.transactions
			if not row.is_cancelled and row.classification and row.classification_status == CLASSIFIED
		]

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

	def set_review_summary(self):
		review_rows = [
			row
			for row in self.transactions
			if not row.is_cancelled and getattr(row, "classification_status", None) == NEEDS_REVIEW
		]
		self.unresolved_transaction_count = len(review_rows)
		self.unresolved_issues_summary = "\n".join(
			f"{row.voucher_type} {row.voucher_no}: {row.classification_issue}"
			for row in review_rows[:10]
			if row.classification_issue
		)

	def on_submit(self):
		review_rows = [
			row
			for row in self.transactions
			if not row.is_cancelled and getattr(row, "classification_status", None) == NEEDS_REVIEW
		]
		if review_rows:
			frappe.throw(
				_("Please resolve the remaining {0} VAT201 review items before submitting.").format(
					len(review_rows)
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
					"classification_status": row.classification_status,
					"classification_issue": row.classification_issue,
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
		self.set_review_summary()
		self.set_submission_period()
		return {
			"transaction_count": len(rows),
			"unclassified_count": len(
				[
					row
					for row in rows
					if row.get("classification_status") == NEEDS_REVIEW and not row.get("is_cancelled")
				]
			),
		}

	def get_sales_invoice_rows(self, settings):
		rows = []
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
			item_groups = self.get_invoice_item_groups(
				invoice.name, "Sales Invoice Item", self.classify_sales_item_category, default_classification, sign
			)
			taxes = frappe.get_all(
				"Sales Taxes and Charges",
				filters={"parent": invoice.name, "account_head": settings.output_vat_account},
				fields=["name", "rate", "base_tax_amount as tax_amount", "total"],
				order_by="idx asc",
			)
			rows.extend(
				self.build_sales_invoice_rows(
					invoice=invoice,
					item_groups=item_groups,
					taxes=taxes,
					default_classification=default_classification,
					sign=sign,
				)
			)
		return rows

	def get_purchase_invoice_rows(self, settings):
		rows = []
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
			item_groups = self.get_invoice_item_groups(
				invoice.name, "Purchase Invoice Item", self.classify_purchase_item_category, default_classification, sign
			)
			taxes = frappe.get_all(
				"Purchase Taxes and Charges",
				filters={"parent": invoice.name, "account_head": settings.input_vat_account},
				fields=["name", "rate", "tax_amount", "total"],
				order_by="idx asc",
			)
			rows.extend(
				self.build_purchase_invoice_rows(
					invoice=invoice,
					item_groups=item_groups,
					taxes=taxes,
					default_classification=default_classification,
					sign=sign,
				)
			)
		return rows

	def get_journal_entry_rows(self, settings):
		rows = []
		vat_account_rows = getattr(settings, "vat_accounts", None) or getattr(settings, "tax_accounts", [])
		tax_accounts = {row.account for row in vat_account_rows if row.account}
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
						self.make_transaction_row(
							voucher_type="Journal Entry",
							voucher_no=voucher_no,
							posting_date=entry.posting_date,
							gl_entry=entry.name,
							tax_account_debit=flt(entry.debit),
							tax_account_credit=flt(entry.credit),
							tax_amount=tax_amount,
							incl_tax_amount=incl_tax_amount,
							classification=classification,
							classification_status=CLASSIFIED if classification else NEEDS_REVIEW,
							classification_issue=None if classification else _("No valid non-tax classification pair matched this VAT journal leg."),
							classification_debugging="\n".join(debug),
							is_cancelled=entry.is_cancelled,
						)
					)
			else:
				for entry in voucher_rows:
					side = "debit" if flt(entry.debit) > 0 else "credit"
					classification = self.get_account_classification(entry.account, side)
					if not classification:
						continue
					rows.append(
						self.make_transaction_row(
							voucher_type="Journal Entry",
							voucher_no=voucher_no,
							posting_date=entry.posting_date,
							gl_entry=entry.name,
							tax_account_debit=flt(entry.debit),
							tax_account_credit=flt(entry.credit),
							tax_amount=0,
							incl_tax_amount=flt(entry.debit) if side == "debit" else -flt(entry.credit),
							classification=classification,
							classification_status=CLASSIFIED,
							classification_debugging=f"Classified directly from account {entry.account}",
							is_cancelled=entry.is_cancelled,
						)
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

	def get_invoice_item_groups(self, parent, item_doctype, classifier, default_classification, sign):
		item_groups = {}
		for item in frappe.get_all(
			item_doctype,
			filters={"parent": parent},
			fields=["base_net_amount", "custom_sa_vat_category"],
		):
			classification = classifier(item.custom_sa_vat_category) or default_classification
			if not classification:
				continue
			item_groups.setdefault(classification, 0)
			item_groups[classification] += flt(item.base_net_amount) * sign
		return item_groups

	def build_sales_invoice_rows(self, invoice, item_groups, taxes, default_classification, sign):
		rows = []
		total_tax = sum(flt(tax.tax_amount) for tax in taxes) * sign
		total_amount = flt(invoice.base_net_total) * sign

		if taxes:
			if item_groups:
				invalid_item_classes = [
					classification
					for classification in item_groups
					if classification not in SALES_STANDARD_CLASSIFICATIONS
					and classification not in {OUTPUT_ZERO_LOCAL, OUTPUT_ZERO_EXPORTED, OUTPUT_EXEMPT}
				]
				if invalid_item_classes:
					return [
						self.make_transaction_row(
							voucher_type="Sales Invoice",
							voucher_no=invoice.name,
							posting_date=invoice.posting_date,
							taxes_and_charges=invoice.taxes_and_charges,
							tax_amount=total_tax,
							incl_tax_amount=total_amount,
							classification_status=NEEDS_REVIEW,
							classification_issue=_("Invoice item VAT categories produced unsupported sales classifications."),
							classification_debugging=", ".join(invalid_item_classes),
						)
					]

				standard_groups = {
					classification: amount
					for classification, amount in item_groups.items()
					if classification in SALES_STANDARD_CLASSIFICATIONS
				}
				zero_or_exempt_groups = {
					classification: amount
					for classification, amount in item_groups.items()
					if classification in {OUTPUT_ZERO_LOCAL, OUTPUT_ZERO_EXPORTED, OUTPUT_EXEMPT}
				}

				if total_tax and not standard_groups:
					return [
						self.make_transaction_row(
							voucher_type="Sales Invoice",
							voucher_no=invoice.name,
							posting_date=invoice.posting_date,
							taxes_and_charges=invoice.taxes_and_charges,
							tax_amount=total_tax,
							incl_tax_amount=total_amount,
							classification_status=NEEDS_REVIEW,
							classification_issue=_("Posted sales VAT exists, but no standard-rated classification could be derived from mappings or item categories."),
							classification_debugging=f"Template: {invoice.taxes_and_charges}",
						)
					]

				rows.extend(self.allocate_tax_by_group(invoice, standard_groups, total_tax, invoice.taxes_and_charges))
				for classification, amount in zero_or_exempt_groups.items():
					rows.append(
						self.make_transaction_row(
							voucher_type="Sales Invoice",
							voucher_no=invoice.name,
							posting_date=invoice.posting_date,
							taxes_and_charges=invoice.taxes_and_charges,
							tax_amount=0,
							incl_tax_amount=amount,
							classification=classification,
							classification_status=CLASSIFIED,
							classification_debugging="Classified from item VAT category with zero posted VAT.",
						)
					)
				return rows

			if default_classification:
				return [
					self.make_transaction_row(
						voucher_type="Sales Invoice",
						voucher_no=invoice.name,
						posting_date=invoice.posting_date,
						taxes_and_charges=invoice.taxes_and_charges,
						tax_amount=total_tax,
						incl_tax_amount=total_amount,
						classification=default_classification,
						classification_status=CLASSIFIED,
						classification_debugging=f"Classified from sales tax template {invoice.taxes_and_charges}",
					)
				]

			return [
				self.make_transaction_row(
					voucher_type="Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=total_tax,
					incl_tax_amount=total_amount,
					classification_status=NEEDS_REVIEW,
					classification_issue=_("Posted sales VAT exists, but no explicit VAT201 mapping or supported item VAT category was found."),
				)
			]

		if item_groups:
			return [
				self.make_transaction_row(
					voucher_type="Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=amount,
					classification=classification,
					classification_status=CLASSIFIED,
					classification_debugging="Classified from zero/exempt item VAT category with no posted VAT.",
				)
				for classification, amount in item_groups.items()
				if classification in {OUTPUT_ZERO_LOCAL, OUTPUT_ZERO_EXPORTED, OUTPUT_EXEMPT}
			] or [
				self.make_transaction_row(
					voucher_type="Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=total_amount,
					classification_status=NEEDS_REVIEW,
					classification_issue=_("Item VAT categories exist, but the invoice has no posted VAT rows and no zero-rated/exempt classification could be derived confidently."),
				)
			]

		if default_classification in {OUTPUT_ZERO_LOCAL, OUTPUT_ZERO_EXPORTED, OUTPUT_EXEMPT}:
			return [
				self.make_transaction_row(
					voucher_type="Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=total_amount,
					classification=default_classification,
					classification_status=CLASSIFIED,
					classification_debugging=f"Classified from explicit zero/exempt sales template {invoice.taxes_and_charges}",
				)
			]

		if default_classification in SALES_STANDARD_CLASSIFICATIONS:
			return [
				self.make_transaction_row(
					voucher_type="Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=total_amount,
					classification_status=NEEDS_REVIEW,
					classification_issue=_("Sales template maps to a standard-rated VAT201 box, but no posted VAT rows were found on the invoice."),
				)
			]

		return []

	def build_purchase_invoice_rows(self, invoice, item_groups, taxes, default_classification, sign):
		total_tax = sum(flt(tax.tax_amount) for tax in taxes) * sign
		total_amount = flt(invoice.base_net_total) * sign

		if taxes:
			if item_groups:
				input_groups = {
					classification: amount
					for classification, amount in item_groups.items()
					if classification in PURCHASE_INPUT_CLASSIFICATIONS
				}
				unsupported_groups = {
					classification: amount
					for classification, amount in item_groups.items()
					if classification not in PURCHASE_INPUT_CLASSIFICATIONS
				}
				if total_tax and not input_groups:
					return [
						self.make_transaction_row(
							voucher_type="Purchase Invoice",
							voucher_no=invoice.name,
							posting_date=invoice.posting_date,
							taxes_and_charges=invoice.taxes_and_charges,
							tax_amount=total_tax,
							incl_tax_amount=total_amount,
							classification_status=NEEDS_REVIEW,
							classification_issue=_("Posted purchase VAT exists, but no deductible input classification could be derived from mappings or item categories."),
							classification_debugging=f"Template: {invoice.taxes_and_charges}",
						)
					]

				rows = self.allocate_tax_by_group(
					invoice, input_groups, total_tax, invoice.taxes_and_charges, is_purchase=True
				)
				for classification, amount in unsupported_groups.items():
					rows.append(
						self.make_transaction_row(
							voucher_type="Purchase Invoice",
							voucher_no=invoice.name,
							posting_date=invoice.posting_date,
							taxes_and_charges=invoice.taxes_and_charges,
							tax_amount=0,
							incl_tax_amount=amount,
							classification_status=EXCLUDED,
							classification_issue=_("Purchase line is zero-rated/exempt or otherwise non-deductible and is excluded from VAT201 input tax totals."),
							classification_debugging=f"Excluded item category classification: {classification}",
						)
					)
				return rows

			if default_classification in PURCHASE_INPUT_CLASSIFICATIONS:
				return [
					self.make_transaction_row(
						voucher_type="Purchase Invoice",
						voucher_no=invoice.name,
						posting_date=invoice.posting_date,
						taxes_and_charges=invoice.taxes_and_charges,
						tax_amount=total_tax,
						incl_tax_amount=total_amount,
						classification=default_classification,
						classification_status=CLASSIFIED,
						classification_debugging=f"Classified from purchase tax template {invoice.taxes_and_charges}",
					)
				]

			return [
				self.make_transaction_row(
					voucher_type="Purchase Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=total_tax,
					incl_tax_amount=total_amount,
					classification_status=NEEDS_REVIEW,
					classification_issue=_("Posted purchase VAT exists, but no explicit deductible VAT201 mapping was found."),
				)
			]

		if item_groups:
			return [
				self.make_transaction_row(
					voucher_type="Purchase Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=amount,
					classification_status=EXCLUDED,
					classification_issue=_("Purchase line carries no posted deductible VAT and is excluded from VAT201 input totals."),
					classification_debugging=f"Excluded item category classification: {classification}",
				)
				for classification, amount in item_groups.items()
			]

		if default_classification in PURCHASE_INPUT_CLASSIFICATIONS:
			return [
				self.make_transaction_row(
					voucher_type="Purchase Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=invoice.taxes_and_charges,
					tax_amount=0,
					incl_tax_amount=total_amount,
					classification_status=NEEDS_REVIEW,
					classification_issue=_("Purchase template maps to a deductible VAT201 box, but no posted VAT rows were found on the invoice."),
				)
			]

		return []

	def allocate_tax_by_group(self, invoice, groups, total_tax, template, is_purchase=False):
		rows = []
		if not groups:
			return rows
		total_group_amount = sum(flt(amount) for amount in groups.values())
		allocated_tax = 0
		group_items = list(groups.items())
		for idx, (classification, amount) in enumerate(group_items, start=1):
			if idx == len(group_items):
				tax_amount = total_tax - allocated_tax
			else:
				tax_amount = flt(total_tax * (flt(amount) / total_group_amount)) if total_group_amount else 0
				allocated_tax += tax_amount
			rows.append(
				self.make_transaction_row(
					voucher_type="Purchase Invoice" if is_purchase else "Sales Invoice",
					voucher_no=invoice.name,
					posting_date=invoice.posting_date,
					taxes_and_charges=template,
					tax_account_debit=abs(tax_amount) if is_purchase and tax_amount > 0 else 0,
					tax_account_credit=abs(tax_amount) if (is_purchase and tax_amount < 0) or (not is_purchase and tax_amount > 0) else 0,
					tax_amount=tax_amount,
					incl_tax_amount=amount,
					classification=classification,
					classification_status=CLASSIFIED,
					classification_debugging="Allocated from posted tax evidence across mapped invoice item groups.",
				)
			)
		return rows

	def make_transaction_row(
		self,
		voucher_type,
		voucher_no,
		posting_date,
		taxes_and_charges="",
		gl_entry=None,
		tax_account_debit=0,
		tax_account_credit=0,
		tax_amount=0,
		incl_tax_amount=0,
		classification=None,
		classification_status=CLASSIFIED,
		classification_issue=None,
		classification_debugging="",
		is_cancelled=0,
	):
		return {
			"gl_entry": gl_entry,
			"voucher_type": voucher_type,
			"voucher_no": voucher_no,
			"posting_date": posting_date,
			"taxes_and_charges": taxes_and_charges,
			"tax_account_debit": flt(tax_account_debit),
			"tax_account_credit": flt(tax_account_credit),
			"tax_amount": flt(tax_amount),
			"incl_tax_amount": flt(incl_tax_amount),
			"classification": classification,
			"classification_status": classification_status,
			"classification_issue": classification_issue,
			"is_cancelled": is_cancelled,
			"classification_debugging": classification_debugging,
		}

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
		}.get(category)
