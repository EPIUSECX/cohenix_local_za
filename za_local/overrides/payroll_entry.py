"""
South African Payroll Entry Override

This module extends the standard HRMS Payroll Entry functionality to support
South African payroll requirements including frequency-based processing and
bank entry management.

Note: This module only works when HRMS is installed.
"""

import frappe
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe import _
from frappe.utils import escape_html, flt, getdate

from za_local.utils.hrms_detection import get_hrms_doctype_class, require_hrms

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
    is_payroll_processed,
)

LOGGER = frappe.logger("za_local_payroll")


class ZAPayrollEntry(PayrollEntry):
    """
    South African Payroll Entry implementation.

    Extends the standard Payroll Entry with:
    - Frequency-based payroll processing (Quarterly, Half-Yearly, Yearly)
    - Bank account validation for employees
    - Employee type validation
    """

    def validate(self):
        """Run stock HRMS validation and mandatory SA employee checks on every save."""
        require_hrms("Payroll Entry")
        super().validate()
        self.validate_employee_requirements()

    def before_save(self):
        self.ensure_consistent_status()

    def on_submit(self):
        if hasattr(super(), "on_submit"):
            super().on_submit()
        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        if hasattr(super(), "on_cancel"):
            super().on_cancel()
        self.db_set("status", "Cancelled", update_modified=False)

    def ensure_consistent_status(self):
        if self.docstatus == 0 and self.get("status") == "Submitted":
            self.status = "Draft"
        elif self.docstatus == 1:
            self.status = "Submitted"
        elif self.docstatus == 2:
            self.status = "Cancelled"

    def validate_employee_requirements(self):
        """
        Validate that all employees have required SA fields populated.

        Note: Bank account is only needed when creating bank entries (payments),
        not for creating salary slips. Employee type is always required.

        Employee metadata is fetched in one query so large payrolls do not cause
        two database round trips per employee during every save.
        """
        employees = self.get("employees") or []
        if not employees:
            return

        employee_names = list(dict.fromkeys(row.employee for row in employees if row.employee))
        employee_details = {
            row.name: row
            for row in frappe.get_all(
                "Employee",
                filters={"name": ["in", employee_names]},
                fields=[
                    "name",
                    "employee_name",
                    "za_employee_type",
                    "za_payroll_payable_bank_account",
                ],
            )
        }
        employees_without_employee_type = [
            row for row in employees if not employee_details.get(row.employee, {}).get("za_employee_type")
        ]
        employees_without_bank_account = [
            row
            for row in employees
            if not employee_details.get(row.employee, {}).get("za_payroll_payable_bank_account")
        ]

        if employees_without_employee_type:
            labels = []
            for row in employees_without_employee_type:
                detail = employee_details.get(row.employee) or {}
                employee_name = detail.get("employee_name") or row.get("employee_name") or ""
                labels.append(escape_html(f"{row.employee}: {employee_name}"))
            frappe.throw(
                _("Employee Type is required for the following employees:")
                + "<br><ul><li>"
                + "</li><li>".join(labels)
                + "</li></ul>",
                title=_("Missing Required Field"),
            )

        if employees_without_bank_account:
            LOGGER.warning(
                "Payroll Entry %s has %s employee(s) without a payroll bank account: %s",
                self.name or "New Payroll Entry",
                len(employees_without_bank_account),
                ", ".join(row.employee for row in employees_without_bank_account),
            )

    def validate_mandatory_fields(self):
        """
        Validate that all mandatory fields are filled before creating salary slips.
        This prevents silent failures when the form is not properly saved.
        """
        mandatory_fields = {
            "posting_date": _("Posting Date"),
            "company": _("Company"),
            "currency": _("Currency"),
            "exchange_rate": _("Exchange Rate"),
            "payroll_payable_account": _("Payroll Payable Account"),
            "payroll_frequency": _("Payroll Frequency"),
            "start_date": _("Start Date"),
            "end_date": _("End Date"),
            "cost_center": _("Cost Center"),
        }

        missing_fields = []
        for field, label in mandatory_fields.items():
            if not self.get(field):
                missing_fields.append(label)

        if missing_fields:
            error_msg = _("Mandatory fields required in Payroll Entry") + "<br><br><ul><li>"
            error_msg += "</li><li>".join(missing_fields)
            error_msg += "</li></ul>"
            frappe.throw(
                error_msg,
                title=_("Missing Fields"),
                exc=frappe.MandatoryError
            )

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
        pay_at = frappe.db.get_single_value("Employee Payroll Frequency", "pay_at")

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

        # Validate mandatory fields before proceeding
        self.validate_mandatory_fields()

        # Ensure document is saved before creating salary slips
        # If document doesn't have a name, it hasn't been saved yet
        if not self.name:
            # Document hasn't been saved yet - save it first
            try:
                self.save()
            except Exception as e:
                # If save fails, show the error
                frappe.throw(
                    _("Cannot create salary slips. Please fix the errors and save the document first: {0}").format(str(e)),
                    title=_("Validation Error")
                )

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
        except Exception:
            # If frequency check fails, include all employees
            # Log error but don't block creation
            frappe.log_error(
                title=f"Payroll Entry frequency check failed: {self.name}",
                message=frappe.get_traceback(),
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
                    create_salary_slips_for_employees(employees, args, publish_progress=False)
                    self.reload()

                    created_for = set(
                        frappe.get_all(
                            "Salary Slip",
                            filters={
                                "payroll_entry": self.name,
                                "employee": ["in", employees],
                                "docstatus": ["<", 2],
                            },
                            pluck="employee",
                        )
                    )
                    missing = sorted(set(employees) - created_for)
                    if missing:
                        frappe.throw(
                            _(
                                "Salary Slips were not created for: {0}. Review the Payroll Entry Error Message and Error Log before continuing."
                            ).format(", ".join(missing)),
                            title=_("Salary Slip Creation Incomplete"),
                        )
                    frappe.msgprint(
                        _("Salary slips created successfully."),
                        indicator="green",
                        alert=True
                    )

                return True
            except Exception as e:
                # Log the full error
                frappe.log_error(
                    title=f"Payroll Entry salary slip creation failed: {self.name}",
                    message=frappe.get_traceback(),
                )
                # Re-raise with a user-friendly message
                frappe.throw(
                    _("Error creating salary slips: {0}. Please check the Error Log for details.").format(str(e)),
                    title=_("Salary Slip Creation Failed")
                )

        return False

    @frappe.whitelist(methods=["POST"])
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
        LOGGER.debug(
            "make_payment_entry called by %s for %s, docstatus=%s",
            frappe.session.user,
            self.name,
            self.docstatus,
        )

        # This creates bank Journal Entries, i.e. it moves money. run_doc_method only
        # enforces READ on the document (frappe/handler.py -> get_doc(check_permission=True)
        # -> check_permission("read")), so gating must happen here or any user who can
        # merely view a Payroll Entry can pay it. HRMS's own make_bank_entry does the same.
        self.check_permission("write")

        # Reload document to ensure we have latest state
        self.reload()

        # Get selected_payment_account from method argument or document attribute
        selected_accounts = selected_payment_account or getattr(self, 'selected_payment_account', None)

        if not selected_accounts:
            frappe.throw(_("No payment accounts selected. Please select bank accounts and employees."))

        # Parse if string (JSON)
        if isinstance(selected_accounts, str):
            import json
            selected_accounts = json.loads(selected_accounts)

        # Validate that employees have bank accounts configured
        selected_employees = list(
            dict.fromkeys(
                employee
                for account_data in selected_accounts.values()
                for employee in account_data.get("employees", [])
            )
        )
        if not selected_employees:
            frappe.throw(_("Select at least one employee for payment."))

        employee_details = {
            row.name: row
            for row in frappe.get_all(
                "Employee",
                filters={"name": ["in", selected_employees]},
                fields=["name", "employee_name", "za_payroll_payable_bank_account"],
            )
        }
        missing_bank_accounts = [
            escape_html(
                f"{employee}: {(employee_details.get(employee) or {}).get('employee_name') or ''}"
            )
            for employee in selected_employees
            if not (employee_details.get(employee) or {}).get("za_payroll_payable_bank_account")
        ]

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
        salary_slips = frappe.get_all(
            "Salary Slip",
            filters={
                "payroll_entry": self.name,
                "docstatus": 1,
                "employee": ["in", selected_employees]
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
            # From dialog (company default in UI). Used only to choose base_net_pay vs net_pay; ledger currency is from Account (CoA).
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


@frappe.whitelist(methods=["POST"])
def make_payment_entry_for_payroll(dt, dn, selected_payment_account=None):
    """
    Standalone wrapper function to call make_payment_entry on a Payroll Entry document.
    This bypasses run_doc_method's permission checks which may be too strict for submitted documents.

    Args:
        dt: DocType name (should be "Payroll Entry")
        dn: Document name
        selected_payment_account: Dictionary of bank accounts and employees
    """
    # dt is caller-supplied; pin it so this cannot be pointed at another DocType
    # that happens to expose a make_payment_entry method.
    if dt != "Payroll Entry":
        frappe.throw(_("This action is only available for Payroll Entry."))

    # Verify document exists
    if not frappe.db.exists(dt, dn):
        frappe.throw(_("{0} {1} does not exist").format(dt, dn))

    # This creates bank Journal Entries, i.e. it moves money. Read access is not
    # sufficient — require submit or write on the Payroll Entry.
    if not (frappe.has_permission(dt, "submit", dn) or frappe.has_permission(dt, "write", dn)):
        frappe.throw(
            _("You do not have permission to create bank entries for {0} {1}. Please contact your manager to get access.").format(dt, dn),
            frappe.PermissionError,
            title=_("Permission Denied")
        )

    # frappe.get_doc does not check permissions itself; the explicit write/submit
    # check above is the gate. Unexpected load failures should retain their native
    # traceback and status rather than being converted to a data-leaking message.
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
