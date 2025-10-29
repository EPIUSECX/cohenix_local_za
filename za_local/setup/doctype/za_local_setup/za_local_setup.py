# -*- coding: utf-8 -*-
# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class ZALocalSetup(Document):
	"""DocType to track za_local setup progress and store user selections"""
	
	def validate(self):
		"""Validate the setup document"""
		if not self.company:
			frappe.throw(_("Company is required"))
	
	def on_update(self):
		"""Called after document is saved"""
		# If status changed to Completed, run the setup
		if self.setup_status == "In Progress" and not self.setup_completed_on:
			self.run_setup()
	
	def run_setup(self):
		"""Execute the za_local setup based on user selections"""
		from za_local.setup.install import run_za_local_setup
		
		try:
			run_za_local_setup(self)
		except Exception as e:
			frappe.log_error(f"Setup failed: {str(e)}", "ZA Local Setup")
			self.setup_status = "Pending"
			self.save()
			frappe.throw(_("Setup failed: {0}").format(str(e)))

