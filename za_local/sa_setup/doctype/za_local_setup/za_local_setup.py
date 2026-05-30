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

	def on_update(self):
		"""Called after document is saved"""
		# Only run setup when the user explicitly moves the document into "In Progress".
		if (
			self.has_value_changed("setup_status")
			and self.setup_status == "In Progress"
			and not self.setup_completed_on
		):
			self.run_setup()

	def run_setup(self):
		"""Execute the za_local setup based on user selections"""
		from za_local.sa_setup.install import run_za_local_setup

		try:
			self._setup_result = run_za_local_setup(self)
		except Exception as e:
			frappe.log_error(f"Setup failed: {e!s}", "ZA Local Setup")
			self.db_set("setup_status", "Pending", update_modified=False)
			frappe.throw(_("Setup failed: {0}").format(str(e)))

	@frappe.whitelist()
	def start_setup(self):
		"""Explicit user action to apply the selected South African setup options."""
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

		self.setup_status = "In Progress"
		self.save()
		return getattr(self, "_setup_result", None) or {
			"title": _("ZA Local Setup Complete"),
			"indicator": "green",
			"message": _("South African localisation setup completed."),
			"status": self.setup_status,
			"setup_completed_on": self.setup_completed_on,
		}
