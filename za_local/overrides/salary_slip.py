"""
South African Salary Slip Override

This module extends the standard HRMS Salary Slip functionality to support
South African payroll requirements including PAYE, UIF, SDL, COIDA, and ETI.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from hrms.payroll.doctype.salary_slip.salary_slip import (
    SalarySlip,
    get_salary_component_data,
)
from hrms.payroll.doctype.payroll_period.payroll_period import get_period_factor

# Import ZA Local utilities
from za_local.utils.tax_utils import (
    calculate_south_african_tax,
    get_tax_rebate,
    get_medical_aid_credit,
    calculate_uif_contribution,
    calculate_sdl_contribution
)
from za_local.utils.eti_utils import (
    check_eti_eligibility,
    calculate_eti_amount,
    log_eti_calculation
)
from za_local.utils.payroll_utils import (
    get_current_block_period,
    get_employee_frequency_map,
    is_payroll_processed,
    get_additional_salaries
)


class ZASalarySlip(SalarySlip):
    """
    South African Salary Slip implementation.
    
    Extends the standard Salary Slip with:
    - SA tax calculations (PAYE with rebates and medical credits)
    - Employment Tax Incentive (ETI)
    - UIF, SDL, and COIDA contributions
    - Annual bonus handling
    - Company contributions
    """
    
    def validate(self):
        """
        Validate salary slip with SA-specific checks.
        """
        super().validate()
        
        # Prevent duplicate salary slips for payroll frequency
        self.validate_payroll_frequency()
        
        # Validate all components have accounts
        self.validate_component_accounts()
    
    def validate_payroll_frequency(self):
        """
        Validate that salary slip doesn't duplicate an existing one for the frequency period.
        """
        frequency = get_current_block_period(self)
        employee_frequency = get_employee_frequency_map()
        
        if self.employee in employee_frequency:
            if is_payroll_processed(
                self.employee, 
                frequency[employee_frequency[self.employee]]
            ):
                frappe.throw(
                    _("Salary Slip already created for current {0}").format(
                        employee_frequency[self.employee]
                    )
                )
    
    def validate_component_accounts(self):
        """
        Ensure all salary components have associated GL accounts.
        Required for accurate financial reporting.
        
        Collects all components missing accounts and provides links to configure them.
        """
        components_missing_accounts = []
        
        for component_type in ["earnings", "deductions"]:
            for row in self.get(component_type):
                if not frappe.db.exists(
                    "Salary Component Account",
                    {"parent": row.salary_component, "company": self.company}
                ):
                    components_missing_accounts.append(row.salary_component)
        
        if components_missing_accounts:
            # Remove duplicates while preserving order
            unique_components = []
            seen = set()
            for comp in components_missing_accounts:
                if comp not in seen:
                    unique_components.append(comp)
                    seen.add(comp)
            
            # Build error message with links to all components
            if len(unique_components) == 1:
                error_msg = _(
                    "Salary Component <a href='/app/salary-component/{0}'>{0}</a> is missing an account configuration. "
                    "Please set an account for this component in the Salary Component Account section for company {1}. "
                    "Accounts are required for SA payroll compliance."
                ).format(unique_components[0], self.company)
            else:
                component_links = ", ".join([
                    f"<a href='/app/salary-component/{comp}'>{comp}</a>"
                    for comp in unique_components
                ])
                error_msg = _(
                    "The following Salary Components are missing account configurations: {0}. "
                    "Please set accounts for these components in their respective Salary Component Account sections for company {1}. "
                    "All components must have associated accounts for SA payroll compliance."
                ).format(component_links, self.company)
            
            frappe.throw(error_msg, title=_("Missing Salary Component Accounts"))
    
    def compute_taxable_earnings_for_year(self):
        """
        Calculate annual taxable earnings including annual bonus.
        """
        super().compute_taxable_earnings_for_year()
        
        # Add annual bonus to taxable earnings
        self.annual_bonus = self.get_annual_bonus()
        self.total_taxable_earnings += self.annual_bonus
        
        # Track taxable earnings without full-tax additional components
        self.total_taxable_earnings_without_full_tax_addl_components = (
            self.total_taxable_earnings - 
            getattr(self, 'current_additional_earnings_with_full_tax', 0)
        )
    
    def get_annual_bonus(self):
        """
        Get annual bonus amount from Salary Structure Assignment.
        
        Returns:
            float: Annual bonus amount
        """
        annual_bonus = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee,
                "salary_structure": self.salary_structure,
                "docstatus": 1,
                "from_date": ("<=", self.end_date),
            },
            "za_annual_bonus",
            order_by="from_date desc",
        ) or 0
        
        if not annual_bonus:
            return 0
        
        # Check if bonus has already been paid
        bonus_component = frappe.get_all(
            "Salary Component",
            filters={"disabled": False, "za_is_annual_bonus": True},
            pluck="name"
        )
        
        if not bonus_component:
            return annual_bonus
        
        is_bonus_paid = frappe.db.exists(
            "Additional Salary",
            {
                "docstatus": 1,
                "employee": self.employee,
                "salary_component": ["in", bonus_component],
                "company": self.company,
                "payroll_date": ["between", [self.payroll_period.start_date, self.end_date]]
            }
        )
        
        return 0 if is_bonus_paid else annual_bonus
    
    def calculate_variable_based_on_taxable_salary(self, tax_component):
        """
        Calculate PAYE tax with SA-specific rebates and credits.
        
        Args:
            tax_component (str): Tax component name
            
        Returns:
            float: Monthly tax amount
        """
        if not self.payroll_period:
            return 0
        
        # Calculate annual tax
        annual_tax = calculate_south_african_tax(
            self.total_taxable_earnings,
            self.tax_slab
        )
        
        # Apply tax rebates
        tax_rebates = self.get_tax_rebates()
        annual_tax = max(0, annual_tax - tax_rebates)
        
        # Apply medical aid tax credits
        medical_credits = self.get_medical_aid_credits()
        annual_tax = max(0, annual_tax - medical_credits)
        
        # Calculate monthly tax
        monthly_tax = annual_tax / self.remaining_sub_periods
        
        # Store tax value for ETI calculation
        self.tax_value = monthly_tax
        
        return flt(monthly_tax, 2)
    
    def get_tax_rebates(self):
        """
        Calculate total tax rebates based on employee age.
        
        Returns:
            float: Annual tax rebate amount
        """
        dob = frappe.db.get_value("Employee", self.employee, "date_of_birth")
        if dob:
            return get_tax_rebate(self, dob)
        return 0
    
    def get_medical_aid_credits(self):
        """
        Calculate medical aid tax credits.
        
        Returns:
            float: Annual medical aid credit amount
        """
        # Get dependants from Employee Private Benefit
        dependants = frappe.db.get_value(
            "Employee Private Benefit",
            {
                "effective_from": ["<=", self.start_date],
                "disable": 0,
                "employee": self.employee,
            },
            "medical_aid_dependant",
        )
        
        if dependants:
            return get_medical_aid_credit(self, dependants)
        return 0
    
    def calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
        """
        Calculate net pay with ETI and company contributions.
        """
        # Standard net pay calculation
        super().calculate_net_pay(skip_tax_breakup_computation)
        
        # Calculate and apply ETI
        self.apply_eti()
        
        # Calculate company contributions
        self.calculate_company_contributions()
    
    def apply_eti(self):
        """
        Calculate and apply Employment Tax Incentive.
        """
        # Check ETI eligibility
        eligibility = check_eti_eligibility(self.employee, self)
        
        if not eligibility["eligible"]:
            self.za_monthly_eti = 0
            return
        
        # Calculate ETI amount
        eti_amount = calculate_eti_amount(
            self.employee,
            self,
            self.gross_pay
        )
        
        # Apply ETI to reduce PAYE
        self.za_monthly_eti = eti_amount
        
        # Log ETI calculation
        log_eti_calculation(
            self.employee,
            self,
            eti_amount,
            eligibility
        )
    
    def calculate_company_contributions(self):
        """
        Calculate company contributions (UIF employer, SDL, COIDA).
        """
        if not self.salary_structure:
            return
        
        salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)
        
        # Clear existing company contributions
        self.company_contribution = []
        
        # Get additional company contributions
        additional_contributions = get_additional_salaries(
            self.employee,
            self.start_date,
            self.end_date,
            "company_contributions"
        )
        
        contribution_dict = {}
        data = self.get_data_for_eval()
        
        if isinstance(data, tuple):
            data = data[0]
        
        # Process salary structure company contributions
        for component in salary_structure.company_contribution:
            component.name = None
            component.amount = self.eval_condition_and_formula(component, data)
            
            if component.amount <= 0:
                continue
            
            self.append("company_contribution", component)
            contribution_dict[component.salary_component] = len(self.company_contribution) - 1
        
        # Add additional company contributions
        for contrib in additional_contributions:
            if contrib.salary_component in contribution_dict:
                # Update existing
                idx = contribution_dict[contrib.salary_component]
                self.company_contribution[idx].amount += flt(contrib.amount)
            else:
                # Add new
                self.append("company_contribution", {
                    "salary_component": contrib.salary_component,
                    "amount": flt(contrib.amount)
                })
        # Rollup total
        self.total_company_contribution = sum(flt(row.amount) for row in self.get("company_contribution", []))
    
    def add_additional_salary_components(self, component_type):
        """
        Add additional salary components, filtering out company contributions.
        """
        additional_salaries = get_additional_salaries(
            self.employee,
            self.start_date,
            self.end_date,
            component_type
        )
        
        for additional_salary in additional_salaries:
            self.update_component_row(
                get_salary_component_data(additional_salary.salary_component),
                additional_salary.amount,
                component_type,
                additional_salary,
                is_recurring=additional_salary.is_recurring,
            )
    
    def on_submit(self):
        """
        Post-submission tasks.
        """
        super().on_submit()
        
        # Create loan repayment entries if applicable
        if self.get("loans"):
            self.make_loan_repayment_entries()
    
    def on_cancel(self):
        """
        Post-cancellation tasks.
        """
        super().on_cancel()
        
        # Cancel loan repayment entries if applicable
        if self.get("loans"):
            self.cancel_loan_repayment_entries()


def get_eti_deduction(salary_slip):
    """
    Wrapper function to calculate ETI for a salary slip.
    
    Args:
        salary_slip: Salary Slip document
        
    Returns:
        float: ETI amount
    """
    eligibility = check_eti_eligibility(salary_slip.employee, salary_slip)
    
    if not eligibility["eligible"]:
        return 0
    
    return calculate_eti_amount(
        salary_slip.employee,
        salary_slip,
        salary_slip.gross_pay
    )


def get_tax_rebate_value(salary_slip, date_of_birth):
    """
    Wrapper function to get tax rebates.
    
    Args:
        salary_slip: Salary Slip document
        date_of_birth (date): Employee date of birth
        
    Returns:
        float: Tax rebate amount
    """
    return get_tax_rebate(salary_slip, date_of_birth)


def get_medical_aid_value(salary_slip, dependants):
    """
    Wrapper function to get medical aid credits.
    
    Args:
        salary_slip: Salary Slip document
        dependants (int): Number of dependants
        
    Returns:
        float: Medical aid credit amount
    """
    return get_medical_aid_credit(salary_slip, dependants)

