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
			run_za_local_setup(self)
		except Exception as e:
			frappe.log_error(f"Setup failed: {e!s}", "ZA Local Setup")
			self.setup_status = "Pending"
			self.save()
			frappe.throw(_("Setup failed: {0}").format(str(e)))

	@frappe.whitelist()
	def start_setup(self):
		"""Explicit user action to apply the selected South African setup options."""
		if not self.company:
			frappe.throw(_("Company is required"))

		self.setup_status = "In Progress"
		self.save()
		return {
			"status": self.setup_status,
			"setup_completed_on": self.setup_completed_on,
		}
