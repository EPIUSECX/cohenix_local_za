"""
API Functions

Whitelisted functions for client-side calls and app permission checks.
"""

import frappe


def check_app_permission():
	"""
	Check if user has permission to access the za_local app.

	The app should be visible for Administrator and System Users with the
	System Manager role. This mirrors the production support expectation for
	the setup/compliance workspace: it should not appear as a partial app to
	portal users or users without setup authority.

	This function is used by hooks.py in add_to_apps_screen to control
	app visibility in the app launcher.

	Returns:
		bool: True if user should see the app, False otherwise
	"""
	if frappe.session.user == "Administrator":
		return True

	user = frappe.session.user
	if not user or user == "Guest":
		return False

	try:
		if frappe.db.get_value("User", user, "user_type") != "System User":
			return False
	except Exception:
		return False

	return "System Manager" in frappe.get_roles(user)
