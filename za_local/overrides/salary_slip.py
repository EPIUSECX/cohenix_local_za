"""
South African Salary Slip Override

This module extends the standard HRMS Salary Slip functionality to support
South African payroll requirements including PAYE, UIF, SDL, COIDA, and ETI.

Note: This module only works when HRMS is installed.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from math import ceil

from za_local.utils.hrms_detection import get_hrms_doctype_class, require_hrms, safe_import_hrms

# Conditionally import HRMS classes
SalarySlip = get_hrms_doctype_class(
    "hrms.payroll.doctype.salary_slip.salary_slip",
    "SalarySlip"
)

if SalarySlip is None:
    # HRMS not available - create a dummy class to prevent import errors
    class SalarySlip:
        pass

# Try to import other HRMS functions
get_salary_component_data, = safe_import_hrms(
    "hrms.payroll.doctype.salary_slip.salary_slip",
    "get_salary_component_data"
)

get_period_factor, = safe_import_hrms(
    "hrms.payroll.doctype.payroll_period.payroll_period",
    "get_period_factor"
)

if get_salary_component_data is None:
    def get_salary_component_data(*args, **kwargs):
        require_hrms("Salary Slip")
        return {}

if get_period_factor is None:
    def get_period_factor(*args, **kwargs):
        require_hrms("Salary Slip")
        return 1.0

# Import ZA Local utilities
from za_local.utils.eti_utils import calculate_eti_amount, check_eti_eligibility, log_eti_calculation
from za_local.utils.payroll_utils import (
    get_additional_salaries,
    get_current_block_period,
    get_employee_frequency_map,
    is_payroll_processed,
)
from za_local.utils.tax_utils import (
    calculate_sdl_contribution,
    calculate_uif_contribution,
    get_medical_aid_credit,
    get_tax_rebate,
)

RETIREMENT_FUND_DEDUCTION_CODES = {"4001", "4003", "4006", "4007"}


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

    def __init__(self, *args, **kwargs):
        """Ensure HRMS is available before initialization"""
        if SalarySlip is None:
            require_hrms("Salary Slip")
        super().__init__(*args, **kwargs)

    def validate(self):
        """
        Validate salary slip with SA-specific checks.
        """
        require_hrms("Salary Slip")
        self.apply_sa_component_classification_defaults()
        super().validate()

        # Prevent duplicate salary slips for payroll frequency
        self.validate_payroll_frequency()

    def apply_sa_component_classification_defaults(self):
        """Apply SA payroll treatment that must be in place before HRMS tax runs."""
        for deduction in self.get("deductions") or []:
            if self.is_retirement_fund_component(deduction.salary_component):
                deduction.exempted_from_income_tax = 1

    def before_submit(self):
        """
        Validate before submitting salary slip.
        """
        # Note: Parent class (SalarySlip) doesn't have before_submit, so we don't call super()
        # Validate all components have accounts before allowing submission
        self.validate_component_accounts()

    def validate_payroll_frequency(self):
        """
        Validate that salary slip doesn't duplicate an existing one for the frequency period.
        """
        try:
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
        except Exception as e:
            # Log error but don't block creation if frequency validation fails
            frappe.log_error(
                f"Error validating payroll frequency for employee {self.employee}: {e!s}",
                "Salary Slip Frequency Validation"
            )
            # Don't throw - allow creation to proceed

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

        self.apply_retirement_fund_deduction_cap()

        # Track taxable earnings without full-tax additional components
        self.total_taxable_earnings_without_full_tax_addl_components = (
            self.total_taxable_earnings -
            getattr(self, 'current_additional_earnings_with_full_tax', 0)
        )

    def apply_retirement_fund_deduction_cap(self):
        """Add back retirement fund deductions above the SARS annual cap.

        HRMS reduces taxable earnings by deduction rows marked
        ``exempted_from_income_tax``. For South Africa, pension/provident/RA
        deductions must still be capped to the lower of actual contributions,
        27.5% of remuneration/taxable base, and the annual statutory cap.
        """
        if not getattr(self, "tax_slab", None) or not self.tax_slab.allow_tax_exemption:
            return

        annual_contribution = self.get_annual_retirement_fund_contribution()
        if annual_contribution <= 0:
            return

        base_before_retirement_deduction = flt(self.total_taxable_earnings) + annual_contribution
        max_by_percentage = base_before_retirement_deduction * 0.275
        allowed_deduction = min(annual_contribution, max_by_percentage, 350000)
        disallowed_deduction = max(0, annual_contribution - allowed_deduction)

        if disallowed_deduction:
            self.total_taxable_earnings += disallowed_deduction
            self.za_retirement_fund_taxable_excess = disallowed_deduction

    def get_annual_retirement_fund_contribution(self):
        """Annualise retirement-fund deduction rows used before PAYE."""
        current_contribution = 0
        for deduction in self.get("deductions") or []:
            if not deduction.get("exempted_from_income_tax"):
                continue
            if self.is_retirement_fund_component(deduction.salary_component):
                current_contribution += flt(deduction.amount)

        if not current_contribution:
            return 0

        previous_contribution = self.get_previous_retirement_fund_contribution()
        future_periods = max(ceil(flt(getattr(self, "remaining_sub_periods", 1))) - 1, 0)
        return previous_contribution + current_contribution + (current_contribution * future_periods)

    def get_previous_retirement_fund_contribution(self):
        if not self.payroll_period:
            return 0

        previous_slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": self.employee,
                "company": self.company,
                "docstatus": 1,
                "start_date": [">=", self.payroll_period.start_date],
                "end_date": ["<", self.start_date],
            },
            pluck="name",
        )
        if not previous_slips:
            return 0

        total = 0
        for row in frappe.get_all(
            "Salary Detail",
            filters={
                "parent": ["in", previous_slips],
                "parentfield": "deductions",
                "exempted_from_income_tax": 1,
            },
            fields=["salary_component", "amount"],
        ):
            if self.is_retirement_fund_component(row.salary_component):
                total += flt(row.amount)

        return total

    def is_retirement_fund_component(self, salary_component):
        code = frappe.db.get_value("Salary Component", salary_component, "za_sars_payroll_code")
        if code in RETIREMENT_FUND_DEDUCTION_CODES:
            return True

        component_name = (salary_component or "").lower()
        return any(
            token in component_name
            for token in ("pension", "provident", "retirement annuity", "retirement fund")
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
        Validate prerequisites, then calculate tax using SA-specific logic with rebates/credits.

        Follows standard HRMS pattern: validates payroll_period, then calls calculate_variable_tax.
        """
        # Validate required attributes (standard HRMS validation)
        if not self.payroll_period:
            frappe.msgprint(
                _("Start and end dates not in a valid Payroll Period, cannot calculate {0}.").format(
                    tax_component
                )
            )
            return

        # Call our overridden calculate_variable_tax (uses SA tax calculation)
        # This populates all the standard HRMS dictionary fields
        self.calculate_variable_tax(tax_component)

        # Apply SA-specific rebates and medical credits as an adjustment
        if tax_component in self._component_based_variable_tax:
            tax_rebates = self.get_tax_rebates()
            medical_credits = self.get_medical_aid_credits()

            # Calculate annual tax after rebates/credits
            annual_tax_after_rebates = max(0,
                self._component_based_variable_tax[tax_component]["total_structured_tax_amount"]
                - tax_rebates - medical_credits
            )

            # Recalculate current tax amount (monthly after rebates/credits)
            previous_total_paid_taxes = self._component_based_variable_tax[tax_component]["previous_total_paid_taxes"]
            current_tax_amount = max(0, (
                annual_tax_after_rebates - previous_total_paid_taxes
            ) / self.remaining_sub_periods)

            # Update the dictionary with adjusted tax amount
            self._component_based_variable_tax[tax_component]["current_tax_amount"] = current_tax_amount

            # Store tax value for ETI calculation
            self.tax_value = current_tax_amount

    def calculate_variable_tax(self, tax_component, has_additional_salary_tax_component=False):
        """
        Override to use tax slab values (same as HRMS), but with SA-specific eval_locals handling.

        This uses the same tax slab calculation as standard HRMS, just avoids NoneType errors.
        """
        # Get previous tax paid in period (standard HRMS logic)
        self.previous_total_paid_taxes = self.get_tax_paid_in_period(
            self.payroll_period.start_date, self.start_date, tax_component
        )

        # Calculate total structured tax amount using tax slab (same as HRMS)
        # Uses the same calculate_tax_by_tax_slab as standard HRMS, just ensures eval_locals is not None
        eval_locals, _default_data = self.get_data_for_eval()
        require_hrms("Salary Slip - Tax Calculation")
        try:
            from hrms.payroll.doctype.salary_slip.salary_slip import calculate_tax_by_tax_slab

            self.total_structured_tax_amount, __ = calculate_tax_by_tax_slab(
                self.total_taxable_earnings_without_full_tax_addl_components,
                self.tax_slab,
                self.whitelisted_globals,
                eval_locals if eval_locals is not None else {},  # Ensure not None
            )

            # Calculate current structured tax amount (standard HRMS logic)
            if has_additional_salary_tax_component:
                self.current_structured_tax_amount = self.additional_salary_amount
            else:
                self.current_structured_tax_amount = (
                    self.total_structured_tax_amount - self.previous_total_paid_taxes
                ) / self.remaining_sub_periods

            # Handle additional earnings with full tax (standard HRMS logic)
            self.full_tax_on_additional_earnings = 0.0
            if self.current_additional_earnings_with_full_tax:
                self.total_tax_amount, __ = calculate_tax_by_tax_slab(
                    self.total_taxable_earnings,
                    self.tax_slab,
                    self.whitelisted_globals,
                    eval_locals if eval_locals is not None else {},  # Ensure not None
                )
                self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount
        except ImportError:
            frappe.throw(_("HRMS is required for tax calculations. Please install HRMS app."))

        # Calculate current tax amount (standard HRMS logic)
        self.current_tax_amount = max(
            0,
            flt(
                self.current_structured_tax_amount
                if has_additional_salary_tax_component
                else (self.current_structured_tax_amount + self.full_tax_on_additional_earnings)
            ),
        )

        # Populate dictionary (standard HRMS pattern)
        self._component_based_variable_tax.setdefault(tax_component, {})
        self._component_based_variable_tax[tax_component].update(
            {
                "previous_total_paid_taxes": self.previous_total_paid_taxes,
                "total_structured_tax_amount": self.total_structured_tax_amount,
                "current_structured_tax_amount": self.current_structured_tax_amount,
                "full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
                "current_tax_amount": self.current_tax_amount,
            }
        )

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
        # Get active medical aid details from Employee Private Benefit. A main
        # member with zero dependants still qualifies for the main-member credit.
        benefit = frappe.db.get_value(
            "Employee Private Benefit",
            {
                "effective_from": ["<=", self.start_date],
                "disable": 0,
                "employee": self.employee,
            },
            ["private_medical_aid", "medical_aid_dependant"],
            as_dict=True,
            order_by="effective_from desc",
        )

        if benefit and (benefit.get("private_medical_aid") or benefit.get("medical_aid_dependant") is not None):
            return get_medical_aid_credit(self, benefit.get("medical_aid_dependant") or 0)
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
