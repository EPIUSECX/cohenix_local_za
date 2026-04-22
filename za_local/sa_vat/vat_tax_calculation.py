"""
ZA VAT tax calculation: when the same account has multiple tax rows (e.g. 15% and 0%),
each row only gets amount from items whose rate matches that row. This is required for
SA legislation and VAT 201 reporting (standard_rated_supplies vs zero_rated_supplies).
"""
from frappe.utils import flt  # type: ignore

# Import the ERPNext class we extend (no patching of their code)
from erpnext.controllers.taxes_and_totals import (  # type: ignore
	calculate_taxes_and_totals as BaseCalculateTaxesAndTotals,
)


class ZACalculateTaxesAndTotals(BaseCalculateTaxesAndTotals):
	"""
	Subclass of ERPNext's calculate_taxes_and_totals used by ZA Sales/Purchase Invoice.
	Overrides _get_tax_rate so same-account multiple rows (15% and 0%) get correct per-row rate.
	"""

	def _get_tax_rate(self, tax, item_tax_map):
		if tax.account_head in item_tax_map:
			item_rate = flt(item_tax_map.get(tax.account_head), 2)
			tax_rate = flt(tax.rate, 2)
			# Same account has multiple rows (15% and 0%). Only apply this row's rate
			# when the item's rate matches; otherwise this row gets 0 for this item.
			if item_rate == tax_rate:
				return item_rate
			return 0
		return tax.rate
