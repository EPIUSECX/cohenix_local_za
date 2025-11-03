"""
South African Payroll Entry Override

This module extends the standard HRMS Payroll Entry functionality to support
South African payroll requirements including frequency-based processing and
bank entry management.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
    PayrollEntry,
    get_employee_list
)

# Import ZA Local utilities
from za_local.utils.payroll_utils import (
    get_current_block_period,
    get_employee_frequency_map,
    is_payroll_processed
)


class ZAPayrollEntry(PayrollEntry):
    """
    South African Payroll Entry implementation.
    
    Extends the standard Payroll Entry with:
    - Frequency-based payroll processing (Quarterly, Half-Yearly, Yearly)
    - Bank account validation for employees
    - Employee type validation
    """
    
    def validate(self):
        """
        Validate payroll entry with SA-specific checks.
        """
        super().validate()
        
        # Validate employees have required SA fields
        self.validate_employee_requirements()
    
    def validate_employee_requirements(self):
        """
        Validate that all employees have required SA fields populated.
        
        Note: Bank account is only needed when creating bank entries (payments),
        not for creating salary slips. Employee type is always required.
        """
        employees_without_employee_type = []
        employees_without_bank_account = []
        
        for emp in self.employees:
            # Get employee type from Employee doctype (not stored on child table)
            # Employee type is required for tax calculations
            emp_type = frappe.db.get_value("Employee", emp.employee, "za_employee_type")
            if not emp_type:
                employees_without_employee_type.append(emp)
            
            # Get bank account from Employee doctype (not stored on child table)
            # Bank account is optional - only needed when creating payment entries
            bank_account = frappe.db.get_value(
                "Employee",
                emp.employee,
                "za_payroll_payable_bank_account"
            )
            if not bank_account:
                employees_without_bank_account.append(emp)
        
        # Employee type is always required (for tax calculations)
        if employees_without_employee_type:
            error_msg = "Employee Type not found for the following employees:<br><ul>"
            for emp in employees_without_employee_type:
                error_msg += f"<li><a href='/app/employee/{emp.employee}'>{emp.employee}: {emp.employee_name}</a></li>"
            error_msg += "</ul>"
            frappe.throw(error_msg, title=_("Missing Required Field"))
        
        # Bank account is optional - only show warning if missing
        # It will be required later when creating bank entries for payment
        if employees_without_bank_account:
            warning_msg = "Payroll Payable Bank Account not found for the following employees. "
            warning_msg += "This will be required when creating bank entries for payment:<br><ul>"
            for emp in employees_without_bank_account:
                warning_msg += f"<li><a href='/app/employee/{emp.employee}'>{emp.employee}: {emp.employee_name}</a></li>"
            warning_msg += "</ul>"
            frappe.msgprint(warning_msg, title=_("Bank Account Not Configured"), indicator="orange")
    
    @frappe.whitelist()
    def fill_employee_details(self):
        """
        Fill employee details with frequency-based filtering.
        """
        filters = self.make_filters()
        employees = get_employee_list(
            filters=filters,
            as_dict=True,
            ignore_match_conditions=True
        )
        
        self.set("employees", [])
        
        if not employees:
            error_msg = _(
                "No employees found for the mentioned criteria:<br>"
                "Company: {0}<br>Currency: {1}"
            ).format(
                frappe.bold(self.company),
                frappe.bold(self.currency),
            )
            if self.branch:
                error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
            if self.department:
                error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
            frappe.throw(error_msg, title=_("No employees found"))
        
        # Get frequency blocks and employee frequency mapping
        frequency = get_current_block_period(self)
        employee_frequency = get_employee_frequency_map()
        
        # Get payment timing setting
        pay_at = frappe.db.get_value(
            "Employee Payroll Frequency",
            "Employee Payroll Frequency",
            "pay_at"
        )
        
        # Filter employees based on frequency
        for emp in employees:
            if emp.employee in employee_frequency:
                emp_freq = employee_frequency[emp.employee]
                
                if pay_at == "Beginning of the period":
                    if str(frequency[emp_freq].start_date) != str(self.start_date):
                        continue
                elif pay_at == "End of the period":
                    if str(frequency[emp_freq].end_date) != str(self.end_date):
                        continue
            
            self.append("employees", emp)
        
        self.number_of_employees = len(self.employees)
        return self.get_employees_with_unmarked_attendance()

    @frappe.whitelist()
    def make_company_contribution_entry(self):
        """
        Create a consolidated Journal Entry for Company Contributions (UIF ER, SDL, etc.).
        - Debits: Salary Component Account totals by component
        - Credit: Payroll Payable Account
        Also marks `Payroll Employee Detail.za_is_company_contribution_created` for all rows.
        """
        self.check_permission("write")

        SalarySlip = frappe.qb.DocType("Salary Slip")
        Comp = frappe.qb.DocType("Company Contribution")

        slips = (
            frappe.qb.from_(SalarySlip)
            .select(SalarySlip.name)
            .where(
                (SalarySlip.docstatus == 1)
                & (SalarySlip.start_date >= self.start_date)
                & (SalarySlip.end_date <= self.end_date)
                & (SalarySlip.payroll_entry == self.name)
            )
        ).run(pluck=True)

        if not slips:
            frappe.throw("No submitted Salary Slips found for this Payroll Entry.")

        # Aggregate by component account
        totals_by_account = {}
        rows = (
            frappe.qb.from_(Comp)
            .select(Comp.parent, Comp.salary_component, Comp.amount)
            .where(Comp.parent.isin(slips))
        ).run(as_dict=True)

        for r in rows:
            account = frappe.db.get_value(
                "Salary Component Account",
                {"parent": r.salary_component, "company": self.company},
                "account",
            )
            if not account:
                frappe.throw(
                    frappe._("Please set account in Salary Component {0}").format(
                        frappe.get_desk_link("Salary Component", r.salary_component)
                    )
                )
            totals_by_account[account] = totals_by_account.get(account, 0) + float(r.amount or 0)

        if not totals_by_account:
            frappe.throw("No company contributions found on the salary slips.")

        # Build JE accounts
        precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
        accounts = []
        currencies = []
        company_currency = frappe.get_cached_value("Company", self.company, "default_currency")

        # Debits per component account
        for account, amount in totals_by_account.items():
            exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                account, amount, company_currency, currencies
            )
            if amt:
                accounts.append(
                    self.update_accounting_dimensions(
                        {
                            "account": account,
                            "debit_in_account_currency": round(amt, precision),
                            "exchange_rate": exchange_rate,
                            "cost_center": self.cost_center,
                        },
                        get_accounting_dimensions() if hasattr(self, "get_accounting_dimensions") else [],
                    )
                )

        # Single credit to payroll payable
        total_credit = sum(a["debit_in_account_currency"] for a in accounts)
        exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
            self.payroll_payable_account, total_credit, company_currency, currencies
        )
        accounts.append(
            self.update_accounting_dimensions(
                {
                    "account": self.payroll_payable_account,
                    "credit_in_account_currency": round(amt, precision),
                    "exchange_rate": exchange_rate,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                    "cost_center": self.cost_center,
                },
                get_accounting_dimensions() if hasattr(self, "get_accounting_dimensions") else [],
            )
        )

        # Create and submit JE
        je = self.make_journal_entry(
            accounts,
            currencies,
            payroll_payable_account=self.payroll_payable_account,
            voucher_type="Journal Entry",
            user_remark=_("Company Contribution for {0} to {1}").format(self.start_date, self.end_date),
            submit_journal_entry=True,
        )

        # Mark flags for employees in this payroll entry
        for ped in self.employees:
            frappe.db.set_value(
                "Payroll Employee Detail",
                {"parent": self.name, "employee": ped.employee},
                "za_is_company_contribution_created",
                1,
            )

        frappe.msgprint(_(f"Created Company Contribution Journal Entry: {je.name}"))
        return je.name
    
    @frappe.whitelist()
    def create_salary_slips(self):
        """
        Create salary slips with frequency-based filtering.
        """
        self.check_permission("write")
        
        employees = []
        frequency = get_current_block_period(self)
        employee_frequency = get_employee_frequency_map()
        
        # Filter out employees who already have salary slips for this frequency period
        for emp in self.employees:
            if emp.employee in employee_frequency:
                if is_payroll_processed(
                    emp.employee,
                    frequency[employee_frequency[emp.employee]]
                ):
                    continue
            employees.append(emp.employee)
        
        if employees:
            from hrms.payroll.doctype.payroll_entry.payroll_entry import create_salary_slips_for_employees
            
            args = frappe._dict({
                "salary_slip_based_on_timesheet": self.salary_slip_based_on_timesheet,
                "payroll_frequency": self.payroll_frequency,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "company": self.company,
                "posting_date": self.posting_date,
                "deduct_tax_for_unsubmitted_tax_exemption_proof": self.deduct_tax_for_unsubmitted_tax_exemption_proof,
                "payroll_entry": self.name,
                "exchange_rate": self.exchange_rate,
                "currency": self.currency,
            })
            
            if len(employees) > 30 or frappe.flags.enqueue_payroll_entry:
                # Enqueue for background processing
                frappe.enqueue(
                    create_salary_slips_for_employees,
                    timeout=600,
                    employees=employees,
                    args=args,
                    publish_progress=True
                )
                frappe.msgprint(
                    _("Salary slip creation has been enqueued. "
                      "It may take a few minutes to complete."),
                    alert=True
                )
            else:
                create_salary_slips_for_employees(employees, args, publish_progress=False)
                self.reload()
                
            return True
        
        return False


def get_payroll_entry_bank_entries(payroll_entry):
    """
    Get bank entries for payroll entry with SA-specific handling.
    
    This function is monkey-patched into HRMS to support:
    - Multiple bank accounts per payroll entry
    - Separate journal entries for employee payments and company contributions
    
    Args:
        payroll_entry: Payroll Entry document name
        
    Returns:
        list: List of journal entry dictionaries
        
    Raises:
        ValidationError: If any employee is missing bank account configuration
    """
    payroll_entry_doc = frappe.get_doc("Payroll Entry", payroll_entry)
    
    journal_entries = []
    
    # Group employees by bank account
    bank_account_groups = {}
    employees_without_bank_account = []
    
    for emp in payroll_entry_doc.employees:
        # Fetch bank account from Employee doctype (not stored on child table)
        bank_account = frappe.db.get_value(
            "Employee",
            emp.employee,
            "za_payroll_payable_bank_account"
        )
        if bank_account:
            if bank_account not in bank_account_groups:
                bank_account_groups[bank_account] = []
            bank_account_groups[bank_account].append(emp)
        else:
            employees_without_bank_account.append(emp)
    
    # Validate: Bank account is required when creating bank entries
    if employees_without_bank_account:
        error_msg = "Payroll Payable Bank Account is required for creating bank entries. "
        error_msg += "Please configure bank accounts for the following employees:<br><ul>"
        for emp in employees_without_bank_account:
            error_msg += f"<li><a href='/app/employee/{emp.employee}'>{emp.employee}: {emp.employee_name}</a></li>"
        error_msg += "</ul>"
        frappe.throw(error_msg, title=_("Bank Account Required"))
    
    # Create journal entry for each bank account group
    for bank_account, employees in bank_account_groups.items():
        # Calculate total for this bank account
        total_amount = sum(
            flt(frappe.db.get_value("Salary Slip", {"employee": emp.employee, "payroll_entry": payroll_entry}, "net_pay"))
            for emp in employees
        )
        
        journal_entry = {
            "bank_account": bank_account,
            "total_amount": total_amount,
            "employees": [emp.employee for emp in employees]
        }
        
        journal_entries.append(journal_entry)
    
    return journal_entries

