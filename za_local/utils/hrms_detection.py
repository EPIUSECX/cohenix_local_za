"""
HRMS Detection Utility

Provides functions to detect if HRMS app is installed and available.
Used throughout za_local to conditionally enable HRMS-dependent features.
"""

import frappe


@frappe.whitelist()
def is_hrms_installed():
	"""
	Check if HRMS app is installed and available.
	
	Returns:
		bool: True if HRMS is installed, False otherwise
	"""
	try:
		# Method 1: Check installed apps
		installed_apps = frappe.get_installed_apps()
		if "hrms" in installed_apps:
			return True
		
		# Method 2: Try to import HRMS module
		import importlib.util
		spec = importlib.util.find_spec("hrms")
		if spec is not None:
			return True
		
		return False
	except Exception:
		# If any error occurs, assume HRMS is not installed
		return False


def require_hrms(feature_name="This feature"):
	"""
	Raise an error if HRMS is not installed.
	
	Args:
		feature_name (str): Name of the feature requiring HRMS
		
	Raises:
		frappe.exceptions.ValidationError: If HRMS is not installed
	"""
	if not is_hrms_installed():
		frappe.throw(
			f"{feature_name} requires HRMS app to be installed. "
			"Please install HRMS to use payroll and HR features.",
			title="HRMS Required"
		)


def get_hrms_doctype_class(doctype_path, class_name):
	"""
	Safely import an HRMS DocType class if HRMS is installed.
	
	Args:
		doctype_path (str): Full module path (e.g., "hrms.payroll.doctype.salary_slip.salary_slip")
		class_name (str): Class name to import
		
	Returns:
		class: The HRMS class if available, None otherwise
	"""
	if not is_hrms_installed():
		return None
	
	try:
		module = __import__(doctype_path, fromlist=[class_name])
		return getattr(module, class_name)
	except (ImportError, AttributeError):
		return None


def safe_import_hrms(module_path, *items):
	"""
	Safely import items from an HRMS module.
	
	Args:
		module_path (str): Full module path
		*items: Items to import from the module
		
	Returns:
		tuple: Tuple of imported items, or (None,) * len(items) if HRMS not available
	"""
	if not is_hrms_installed():
		return tuple([None] * len(items))
	
	try:
		module = __import__(module_path, fromlist=list(items))
		return tuple([getattr(module, item, None) for item in items])
	except ImportError:
		return tuple([None] * len(items))

