"""
API Functions

Whitelisted functions for client-side calls and app permission checks.
"""

import frappe


def check_app_permission():
	"""
	Check if user has permission to access the za_local app.
	
	The app should be visible if the user has read permission on any
	of the core za_local doctypes (Company, Customer, or Employee if HRMS is installed).
	
	This function is used by hooks.py in add_to_apps_screen to control
	app visibility in the app launcher.
	
	Returns:
		bool: True if user should see the app, False otherwise
	"""
	if frappe.session.user == "Administrator":
		return True
	
	# Check if user has access to Company (core ERPNext doctype)
	# This is the most basic requirement for using za_local
	if frappe.has_permission("Company", ptype="read"):
		return True
	
	# Check if user has access to Customer (common doctype used by za_local)
	if frappe.has_permission("Customer", ptype="read"):
		return True
	
	# If HRMS is installed, check Employee permission
	try:
		from za_local.utils.hrms_detection import is_hrms_installed
		if is_hrms_installed() and frappe.has_permission("Employee", ptype="read"):
			return True
	except Exception:
		# If HRMS detection fails, continue without it
		pass
	
	return False

