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

		The work is offloaded to a background job (``run_za_local_setup_job``) so it
		can't hit request timeouts on larger runs (chart of accounts, submittable
		statutory docs). The job publishes realtime progress and a completion event;
		this method returns immediately with a "queued" payload. ``run_za_local_setup``
		still persists status/selections and rolls back to "Pending" on error.
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
				"load_eti_slabs",
				"load_sars_payroll_codes",
				"load_salary_component_classifications",
				"load_retirement_funds",
			):
				self.set(fieldname, 0)

		self.setup_status = "In Progress"
		self.save()

		frappe.enqueue(
			"za_local.sa_setup.install.run_za_local_setup_job",
			queue="long",
			timeout=1500,
			setup_name=self.name,
			user=frappe.session.user,
			enqueue_after_commit=True,
		)

		return {
			"title": _("Setup Queued"),
			"indicator": "blue",
			"message": _(
				"South African localisation setup is running in the background. "
				"Progress is shown below; you'll be notified when it finishes."
			),
			"queued": True,
		}
