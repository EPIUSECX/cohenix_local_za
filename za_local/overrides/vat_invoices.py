"""Extend invoice controllers to use ZA VAT tax calculation."""


class ZASalesInvoice:
	"""Sales Invoice extension using ZA VAT tax calculation."""

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


class ZAPurchaseInvoice:
	"""Purchase Invoice extension using ZA VAT tax calculation."""

	def calculate_taxes_and_totals(self):
		from za_local.sa_vat.vat_tax_calculation import ZACalculateTaxesAndTotals

		ZACalculateTaxesAndTotals(self)
