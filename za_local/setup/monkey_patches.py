"""
Monkey Patches for ZA Local

This module sets up all monkey patches required for South African localization.
Monkey patches are applied during app installation/migration, not at import time.
"""

from za_local.utils.hrms_detection import is_hrms_installed
from za_local.accounts.setup_chart import (
	extend_charts_for_country,
	extend_chart_loader,
	patch_financial_report_templates_sync
)


def setup_hrms_monkey_patches():
	"""
	Conditionally setup HRMS monkey patches.
	
	Only applies patches if HRMS is installed.
	"""
	if is_hrms_installed():
		try:
			from hrms.payroll.doctype.payroll_entry import payroll_entry as _payroll_entry  # type: ignore
			from za_local.overrides import payroll_entry as _za_payroll_entry
			_payroll_entry.get_payroll_entry_bank_entries = _za_payroll_entry.get_payroll_entry_bank_entries
		except ImportError:
			# HRMS not fully installed or version mismatch
			pass


def setup_all_monkey_patches():
	"""
	Setup all monkey patches for za_local.
	
	This function should be called from after_install and after_migrate hooks.
	It sets up:
	- HRMS-specific patches (if HRMS is installed)
	- Chart of Accounts extensions
	- Financial report template sync patches
	"""
	setup_hrms_monkey_patches()
	extend_charts_for_country()
	extend_chart_loader()
	patch_financial_report_templates_sync()
