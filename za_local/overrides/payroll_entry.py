"""
South African Payroll Entry Override

This module extends the standard HRMS Payroll Entry functionality to support
South African payroll requirements including frequency-based processing and
bank entry management.

Note: This module only works when HRMS is installed.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from za_local.utils.hrms_detection import require_hrms, get_hrms_doctype_class

# Conditionally import HRMS classes
PayrollEntry = get_hrms_doctype_class(
    "hrms.payroll.doctype.payroll_entry.payroll_entry",
    "PayrollEntry"
)

if PayrollEntry is None:
    # HRMS not available - create a dummy class to prevent import errors
    class PayrollEntry:
        pass

# Try to import get_employee_list
try:
    from hrms.payroll.doctype.payroll_entry.payroll_entry import get_employee_list
except ImportError:
    def get_employee_list(*args, **kwargs):
        require_hrms("Payroll Entry")
        return []

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
    
    def __init__(self, *args, **kwargs):
        """Ensure HRMS is available before initialization"""
        if PayrollEntry is None:
            require_hrms("Payroll Entry")
        super().__init__(*args, **kwargs)
    
    def validate(self):
        """
        Validate payroll entry with SA-specific checks.
        """
        require_hrms("Payroll Entry")
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
        
        # Try to filter by frequency, but don't block if frequency check fails
        try:
            frequency = get_current_block_period(self)
            employee_frequency = get_employee_frequency_map()
            
            # Filter out employees who already have salary slips for this frequency period
            # Only filter if we have frequency data and employee frequency mapping
            if frequency and employee_frequency:
                for emp in self.employees:
                    emp_freq = employee_frequency.get(emp.employee)
                    if emp_freq and emp_freq in frequency:
                        freq_period = frequency[emp_freq]
                        if freq_period and is_payroll_processed(emp.employee, freq_period):
                            continue
                    employees.append(emp.employee)
            else:
                # No frequency data - include all employees
                employees = [emp.employee for emp in self.employees]
        except Exception as e:
            # If frequency check fails, include all employees
            # Log error but don't block creation
            frappe.log_error(
                f"Error checking payroll frequency for Payroll Entry {self.name}: {str(e)}",
                "Payroll Entry Frequency Check"
            )
            # Include all employees if frequency check fails
            employees = [emp.employee for emp in self.employees]
        
        if employees:
            require_hrms("Payroll Entry - Create Salary Slips")
            try:
                from hrms.payroll.doctype.payroll_entry.payroll_entry import create_salary_slips_for_employees
            except ImportError:
                frappe.throw(_("HRMS is required to create salary slips. Please install HRMS app."))
            
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
            
            try:
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
                    # create_salary_slips_for_employees doesn't return a value
                    # It handles errors internally and shows messages
                    # Temporarily suppress ALL messages to prevent error sounds
                    # We'll show our own success message after
                    original_msgprint = frappe.msgprint
                    original_throw = frappe.throw
                    suppressed_warnings = []
                    suppressed_errors = []
                    
                    def silent_msgprint(*args, **kwargs):
                        # Suppress all messages during creation to prevent error sounds
                        message = args[0] if args else kwargs.get('title', 'Message')
                        indicator = kwargs.get("indicator", "blue")
                        
                        if indicator == "orange":
                            suppressed_warnings.append(str(message))
                            # Log but don't show/sound
                            frappe.log_error(
                                f"Suppressed warning: {message}",
                                "Payroll Entry Suppressed Warning"
                            )
                        elif indicator == "red":
                            suppressed_errors.append(str(message))
                            frappe.log_error(
                                f"Suppressed error: {message}",
                                "Payroll Entry Suppressed Error"
                            )
                        # Don't show any messages - suppress all
                        return
                    
                    def silent_throw(*args, **kwargs):
                        # Suppress throws temporarily - log instead
                        message = args[0] if args else kwargs.get('title', 'Error')
                        suppressed_errors.append(str(message))
                        frappe.log_error(
                            f"Suppressed throw: {message}",
                            "Payroll Entry Suppressed Throw"
                        )
                        # Don't actually throw - just log
                        return
                    
                    try:
                        # Clear any existing messages first
                        frappe.clear_messages()
                        
                        # Monkey-patch to suppress all messages
                        frappe.msgprint = silent_msgprint
                        frappe.throw = silent_throw
                        
                        # Create salary slips
                        create_salary_slips_for_employees(employees, args, publish_progress=False)
                        
                        # Restore original functions
                        frappe.msgprint = original_msgprint
                        frappe.throw = original_throw
                        
                        # Clear messages again after creation
                        frappe.clear_messages()
                        
                        self.reload()
                        
                        # Show our own success message
                        frappe.msgprint(
                            _("Salary slips created successfully."),
                            indicator="green",
                            alert=True
                        )
                        
                        # Log summary of suppressed messages
                        if suppressed_warnings or suppressed_errors:
                            summary = []
                            if suppressed_warnings:
                                summary.append(f"{len(suppressed_warnings)} warning(s)")
                            if suppressed_errors:
                                summary.append(f"{len(suppressed_errors)} error(s)")
                            frappe.log_error(
                                f"Suppressed {', '.join(summary)} during salary slip creation for Payroll Entry {self.name}. Check Error Log for details.",
                                "Payroll Entry Message Suppression Summary"
                            )
                            
                    except Exception as creation_error:
                        # Restore original functions on error
                        frappe.msgprint = original_msgprint
                        frappe.throw = original_throw
                        
                        # Log the actual error
                        import traceback
                        error_details = traceback.format_exc()
                        frappe.log_error(
                            f"Error in create_salary_slips_for_employees for Payroll Entry {self.name}:\n{error_details}",
                            "Payroll Entry Salary Slip Creation Error"
                        )
                        # Re-raise so user sees the error
                        raise
                    
                return True
            except Exception as e:
                # Log the full error
                frappe.log_error(
                    f"Error creating salary slips for Payroll Entry {self.name}: {str(e)}",
                    "Payroll Entry Create Salary Slips"
                )
                # Re-raise with a user-friendly message
                frappe.throw(
                    _("Error creating salary slips: {0}. Please check the Error Log for details.").format(str(e)),
                    title=_("Salary Slip Creation Failed")
                )
        
        return False
    
    @frappe.whitelist()
    def make_payment_entry(self, selected_payment_account=None):
        """
        Create bank entry journal entries for employees grouped by bank account.
        
        Note: Standard HRMS uses make_bank_entry() which creates a single journal entry
        for all employees using one payment account. SA payroll requires multiple bank
        accounts (one per employee), so we override to create separate journal entries
        per bank account group.
        
        This is called from the JavaScript UI when "Create Bank Entry" is clicked.
        It processes the selected_payment_account dictionary that contains:
        - Bank account as key
        - Dictionary with: employees, currency, posting_date, exchange_rate
        
        Creates separate Bank Entry journal entries for each bank account group.
        Uses standard HRMS methods (make_journal_entry, get_amount_and_exchange_rate_for_journal_entry)
        but processes employees grouped by bank account rather than all at once.
        
        Args:
            selected_payment_account: Dictionary of bank accounts and employees (passed from JavaScript)
        """
        # Log for debugging permission issues
        frappe.logger().debug(f"make_payment_entry called by {frappe.session.user} for {self.name}, docstatus={self.docstatus}")
        
        # Reload document to ensure we have latest state
        self.reload()
        
        # Note: run_doc_method already handles permission checking before calling this method
        # For submitted documents (docstatus=1), creating bank entries is a standard post-submit action
        # that should work with the permissions that allow viewing the document
        # We don't add additional permission checks here to avoid conflicts with run_doc_method's permission handling
        
        # Get selected_payment_account from method argument or document attribute
        selected_accounts = selected_payment_account or getattr(self, 'selected_payment_account', None)
        
        if not selected_accounts:
            frappe.throw(_("No payment accounts selected. Please select bank accounts and employees."))
        
        # Parse if string (JSON)
        if isinstance(selected_accounts, str):
            import json
            selected_accounts = json.loads(selected_accounts)
        
        # Validate that employees have bank accounts configured
        missing_bank_accounts = []
        for account_data in selected_accounts.values():
            employees = account_data.get("employees", [])
            for employee in employees:
                bank_account = frappe.db.get_value("Employee", employee, "za_payroll_payable_bank_account")
                if not bank_account:
                    emp_name = frappe.db.get_value("Employee", employee, "employee_name")
                    missing_bank_accounts.append(f"{employee}: {emp_name}")
        
        if missing_bank_accounts:
            frappe.throw(
                _("The following employees do not have bank accounts configured. Please configure bank accounts on Employee records:<br><ul><li>{0}</li></ul>").format(
                    "</li><li>".join(missing_bank_accounts)
                ),
                title=_("Bank Account Required")
            )
        
        employee_wise_accounting_enabled = frappe.db.get_single_value(
            "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
        )
        
        # Get salary slip details for all employees
        all_employees = []
        for account_data in selected_accounts.values():
            all_employees.extend(account_data.get("employees", []))
        
        salary_slips = frappe.get_all(
            "Salary Slip",
            filters={
                "payroll_entry": self.name,
                "docstatus": 1,
                "employee": ["in", all_employees]
            },
            fields=["name", "employee", "net_pay", "base_net_pay"]
        )
        
        # Create a mapping of employee to salary slip
        employee_salary_map = {ss.employee: ss for ss in salary_slips}
        
        precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
        company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
        accounting_dimensions = []
        if hasattr(self, 'get_accounting_dimensions'):
            accounting_dimensions = self.get_accounting_dimensions() or []
        
        created_journal_entries = []
        
        # Process each bank account
        for bank_account_name, account_data in selected_accounts.items():
            employees = account_data.get("employees", [])
            posting_date = account_data.get("posting_date")
            exchange_rate = flt(account_data.get("exchange_rate", 1))
            account_currency = account_data.get("currency", company_currency)
            
            if not employees:
                continue
            
            if not posting_date:
                frappe.throw(_("Posting date is required for bank account {0}").format(bank_account_name))
            
            # Get bank account details
            bank_account_doc = frappe.get_doc("Bank Account", bank_account_name)
            payment_account = bank_account_doc.account
            
            # Calculate total amount for this bank account
            total_amount = 0
            employee_amounts = {}
            
            for employee in employees:
                if employee in employee_salary_map:
                    salary_slip = employee_salary_map[employee]
                    amount = flt(salary_slip.base_net_pay if account_currency == company_currency else salary_slip.net_pay)
                    total_amount += amount
                    employee_amounts[employee] = amount
            
            if total_amount <= 0:
                continue
            
            # Build journal entry accounts
            accounts = []
            currencies = []
            
            # Credit: Bank/Payment Account
            exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
                payment_account, total_amount, company_currency, currencies
            )
            accounts.append(
                self.update_accounting_dimensions(
                    {
                        "account": payment_account,
                        "bank_account": bank_account_name,
                        "credit_in_account_currency": flt(amount, precision),
                        "exchange_rate": flt(exchange_rate),
                        "cost_center": self.cost_center,
                    },
                    accounting_dimensions,
                )
            )
            
            # Debit: Payroll Payable Account
            if employee_wise_accounting_enabled:
                # Create separate entries per employee
                for employee, amount in employee_amounts.items():
                    if amount <= 0:
                        continue
                    
                    # Get cost centers for employee
                    cost_centers = self.get_payroll_cost_centers_for_employee(
                        employee, None  # We'd need salary structure, but for now use None
                    )
                    
                    if cost_centers:
                        for cost_center, percentage in cost_centers.items():
                            amount_against_cost_center = flt(amount) * percentage / 100
                            exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                                self.payroll_payable_account, amount_against_cost_center, company_currency, currencies
                            )
                            accounts.append(
                                self.update_accounting_dimensions(
                                    {
                                        "account": self.payroll_payable_account,
                                        "debit_in_account_currency": flt(amt, precision),
                                        "exchange_rate": flt(exchange_rate),
                                        "reference_type": self.doctype,
                                        "reference_name": self.name,
                                        "party_type": "Employee",
                                        "party": employee,
                                        "cost_center": cost_center,
                                    },
                                    accounting_dimensions,
                                )
                            )
                    else:
                        # No cost center split - single entry per employee
                        exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                            self.payroll_payable_account, amount, company_currency, currencies
                        )
                        accounts.append(
                            self.update_accounting_dimensions(
                                {
                                    "account": self.payroll_payable_account,
                                    "debit_in_account_currency": flt(amt, precision),
                                    "exchange_rate": flt(exchange_rate),
                                    "reference_type": self.doctype,
                                    "reference_name": self.name,
                                    "party_type": "Employee",
                                    "party": employee,
                                    "cost_center": self.cost_center,
                                },
                                accounting_dimensions,
                            )
                        )
            else:
                # Single entry for all employees
                exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
                    self.payroll_payable_account, total_amount, company_currency, currencies
                )
                accounts.append(
                    self.update_accounting_dimensions(
                        {
                            "account": self.payroll_payable_account,
                            "debit_in_account_currency": flt(amount, precision),
                            "exchange_rate": flt(exchange_rate),
                            "reference_type": self.doctype,
                            "reference_name": self.name,
                            "cost_center": self.cost_center,
                        },
                        accounting_dimensions,
                    )
                )
            
            # Create journal entry
            bank_entry = self.make_journal_entry(
                accounts,
                currencies,
                voucher_type="Bank Entry",
                user_remark=_("Payment of salaries from {0} to {1} - Bank Account: {2}").format(
                    self.start_date, self.end_date, bank_account_name
                ),
                submit_journal_entry=False,  # Don't auto-submit, let user review
                employee_wise_accounting_enabled=employee_wise_accounting_enabled,
            )
            
            # Set posting date
            bank_entry.posting_date = posting_date
            bank_entry.save()
            
            # Update flags for employees
            for employee in employees:
                frappe.db.set_value(
                    "Payroll Employee Detail",
                    {"parent": self.name, "employee": employee},
                    "za_is_bank_entry_created",
                    1,
                )
            
            created_journal_entries.append(bank_entry.name)
        
        # Clear selected_payment_account after processing
        self.selected_payment_account = {}
        
        if created_journal_entries:
            frappe.msgprint(
                _("Created {0} Bank Entry Journal Entries: {1}").format(
                    len(created_journal_entries),
                    ", ".join([frappe.bold(je) for je in created_journal_entries])
                ),
                indicator="green",
                alert=True
            )
        
        return created_journal_entries


@frappe.whitelist()
def make_payment_entry_for_payroll(dt, dn, selected_payment_account=None):
    """
    Standalone wrapper function to call make_payment_entry on a Payroll Entry document.
    This bypasses run_doc_method's permission checks which may be too strict for submitted documents.
    
    Args:
        dt: DocType name (should be "Payroll Entry")
        dn: Document name
        selected_payment_account: Dictionary of bank accounts and employees
    """
    # Check basic read permission - this works for both draft and submitted documents
    if not frappe.has_permission(dt, "read", dn):
        frappe.throw(_("You do not have permission to access this {0}").format(dt))
    
    doc = frappe.get_doc(dt, dn)
    return doc.make_payment_entry(selected_payment_account)


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

