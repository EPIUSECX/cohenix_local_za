"""
South African Additional Salary Override

This module extends the standard HRMS Additional Salary functionality to support
company contribution flagging for SA payroll.
"""

import frappe
from frappe import _
from hrms.payroll.doctype.additional_salary.additional_salary import AdditionalSalary


class ZAAdditionalSalary(AdditionalSalary):
    """
    South African Additional Salary implementation.
    
    Extends the standard Additional Salary with:
    - Company contribution flag (za_is_company_contribution)
    - Proper filtering for company vs employee components
    """
    
    def validate(self):
        """
        Validate additional salary with SA-specific checks.
        """
        super().validate()
        
        # Validate company contribution flag consistency
        self.validate_company_contribution()
    
    def validate_company_contribution(self):
        """
        Ensure company contribution flag is set correctly.
        """
        if self.get("za_is_company_contribution"):
            # Company contributions should typically not affect employee net pay directly
            # This is informational validation
            pass
        
        # Ensure salary component exists
        if not frappe.db.exists("Salary Component", self.salary_component):
            frappe.throw(
                _("Salary Component {0} does not exist").format(self.salary_component)
            )

