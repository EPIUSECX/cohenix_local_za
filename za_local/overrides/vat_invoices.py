# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt
"""
Override Sales Invoice and Purchase Invoice to use ZA VAT tax calculation.
This ensures 15% and 0% tax rows (same account) get correct amounts per item
for SA legislation and VAT 201 reporting, without patching ERPNext core.
"""

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class ZASalesInvoice(SalesInvoice):
	"""Sales Invoice using ZA VAT tax calculation (same-account multiple rates)."""

	def calculate_taxes_and_totals(self):
		from za_local.sa_vat.vat_tax_calculation import ZACalculateTaxesAndTotals

		ZACalculateTaxesAndTotals(self)

		if self.doctype in (
			"Sales Order",
			"Delivery Note",
			"Sales Invoice",
			"POS Invoice",
		):
			self.calculate_commission()
			self.calculate_contribution()


class ZAPurchaseInvoice(PurchaseInvoice):
	"""Purchase Invoice using ZA VAT tax calculation (same-account multiple rates)."""

	def calculate_taxes_and_totals(self):
		from za_local.sa_vat.vat_tax_calculation import ZACalculateTaxesAndTotals

		ZACalculateTaxesAndTotals(self)
