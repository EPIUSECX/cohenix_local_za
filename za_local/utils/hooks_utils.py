"""
Hooks Utility Functions

Utility functions for generating hooks configuration dynamically.
These functions are called by hooks.py to generate configuration.
"""

from za_local.utils.hrms_detection import is_hrms_installed


def get_hrms_doctype_js():
	"""
	Conditionally add HRMS-dependent doctype JS files.

	Returns:
		dict: Dictionary mapping doctype names to JS file paths
	"""
	hrms_js = {}
	if is_hrms_installed():
		hrms_js.update({
			"Employee": "public/js/employee.js",
			"Payroll Entry": "public/js/payroll_entry.js",
			"Employee Benefit Claim": "public/js/employee_benefit_claim.js",
			"Salary Structure": "public/js/salary_structure.js",
			"Salary Structure Assignment": "public/js/salary_structure_assignment.js",
		})
	return hrms_js
