from __future__ import annotations

import frappe
from frappe.model.document import Document

from za_local.utils.csv_importer import import_csv_data


class BargainingCouncil(Document):
	def validate(self):
		"""Map the packaged legacy CSV header to the canonical field."""
		if self.sector and not self.industry_sector:
			self.industry_sector = self.sector


@frappe.whitelist()
def import_common_councils():
	"""Import only the app-owned bargaining-council data file."""
	frappe.only_for(("HR Manager", "System Manager"))
	return import_csv_data(
		"Bargaining Council",
		"bargaining_council_list.csv",
		update_existing=True,
	)
