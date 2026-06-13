# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ZALocalSetup(Document):
	"""DocType to track za_local setup progress and store user selections"""

	def validate(self):
		"""Validate the setup document"""
		if not self.company:
			frappe.throw(_("Company is required"))
		from za_local.sa_setup.install import validate_za_local_setup_hrms_options

		validate_za_local_setup_hrms_options(self)

	@frappe.whitelist()
	def start_setup(self):
		"""Explicit user action to apply the selected South African setup options.

		Setup is driven only by this explicit action (the "Apply Selected
		Configuration" button), never as a side effect of ``on_update``. The
		work is delegated to ``run_za_local_setup``, which persists the status
		and selections via ``setup_doc.save()``, rolls the status back to
		"Pending" on error, and returns the feedback payload.
		"""
		if not self.company:
			frappe.throw(_("Company is required"))

		from za_local.utils.hrms_detection import is_hrms_installed

		if not is_hrms_installed():
			for fieldname in (
				"load_salary_components",
				"load_earnings_components",
				"load_tax_slabs",
				"load_tax_rebates",
				"load_medical_credits",
			):
				self.set(fieldname, 0)

		from za_local.sa_setup.install import run_za_local_setup

		return run_za_local_setup(self) or {
			"title": _("ZA Local Setup Complete"),
			"indicator": "green",
			"message": _("South African localisation setup completed."),
			"status": self.setup_status,
			"setup_completed_on": self.setup_completed_on,
		}
