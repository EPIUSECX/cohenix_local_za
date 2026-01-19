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


def get_override_doctype_class():
	"""
	Get override doctype classes conditionally based on HRMS availability.
	
	Returns:
		dict: Dictionary mapping doctype names to override class paths
	"""
	overrides = {}
	if is_hrms_installed():
		overrides.update({
			"Salary Slip": "za_local.overrides.salary_slip.ZASalarySlip",
			"Payroll Entry": "za_local.overrides.payroll_entry.ZAPayrollEntry",
			"Additional Salary": "za_local.overrides.additional_salary.ZAAdditionalSalary",
			"Leave Application": "za_local.overrides.leave_application.ZALeaveApplication",
			"Employee Separation": "za_local.overrides.employee_separation.ZAEmployeeSeparation",
			"Salary Structure Assignment": "za_local.overrides.salary_structure_assignment.ZASalaryStructureAssignment"
		})
	return overrides
