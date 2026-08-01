import frappe
from frappe import _
from frappe.model.document import Document

from za_local.utils.coida_utils import validate_industry_rates


class COIDASettings(Document):
	def validate(self):
		self.validate_industry_rates()

	def validate_industry_rates(self):
		"""Ensure industry rates are valid and unambiguous."""
		result = validate_industry_rates(self.industry_rates)
		if not result["valid"]:
			frappe.throw("<br>".join(result["errors"]), title=_("Invalid COIDA Industry Rates"))
