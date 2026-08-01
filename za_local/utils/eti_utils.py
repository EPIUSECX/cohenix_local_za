"""
Employment Tax Incentive (ETI) Utility Functions

The Employment Tax Incentive is a South African tax incentive aimed at encouraging
employers to hire young, less experienced job seekers.

ETI Eligibility Criteria:
- Age: 18-29 years on the last day of the month
- Monthly remuneration within qualifying thresholds
- Employment period: First 24 months only
- Hired on or after October 1, 2013
- Valid SA ID or Asylum Seeker permit
"""

from datetime import date, timedelta

import frappe
from frappe.utils import cint, date_diff, flt, get_first_day, getdate

from za_local.utils.statutory_rates import calculate_eti_from_pack, find_rate_pack

WAGE_BASIS_REGULATED = "National or Regulated Minimum Wage"
WAGE_BASIS_UNREGULATED = "No Regulating Measure or NMW Exempt"


def check_eti_eligibility(employee, salary_slip, monthly_remuneration=None):
    """
    Check if an employee qualifies for ETI.

    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document

    Returns:
        dict: {eligible: bool, reason: str, months_employed: int}
    """
    emp_doc = frappe.get_cached_doc("Employee", employee)
    payroll_settings = frappe.get_cached_doc("Payroll Settings")
    hours_per_month = get_eti_hours(emp_doc, salary_slip)

    if payroll_settings.get("za_disable_eti_calculation"):
        return eligibility_result(False, "ETI calculation is disabled in Payroll Settings", hours=hours_per_month)

    if emp_doc.get("za_is_domestic_worker"):
        return eligibility_result(False, "Domestic workers do not qualify for ETI", hours=hours_per_month)

    if emp_doc.get("za_is_connected_person_to_employer"):
        return eligibility_result(
            False,
            "Connected persons to the employer do not qualify for ETI",
            hours=hours_per_month,
        )

    # Check date of birth
    if not emp_doc.date_of_birth:
        return eligibility_result(False, "Employee date of birth not set", hours=hours_per_month)

    # Check age (18-29 years on last day of month)
    last_day_of_month = getdate(salary_slip.end_date)
    dob = getdate(emp_doc.date_of_birth)

    age = last_day_of_month.year - dob.year
    if (last_day_of_month.month, last_day_of_month.day) < (dob.month, dob.day):
        age -= 1

    if age < 18 or age > 29:
        return eligibility_result(
            False,
            f"Employee age ({age}) not within 18-29 range",
            hours=hours_per_month,
        )

    # Check employment start date
    if not emp_doc.date_of_joining:
        return eligibility_result(False, "Employee joining date not set", hours=hours_per_month)

    joining_date = getdate(emp_doc.date_of_joining)

    # Must be employed on or after October 1, 2013
    eti_start_date = date(2013, 10, 1)
    if joining_date < eti_start_date:
        return eligibility_result(
            False,
            "Employee joined before ETI program start (Oct 1, 2013)",
            hours=hours_per_month,
        )

    months_employed = get_eti_qualifying_month_number(employee, salary_slip, joining_date)

    # ETI only applies for first 24 months
    if months_employed > 24:
        return eligibility_result(
            False,
            "Employee has exceeded 24 qualifying ETI months",
            months=months_employed,
            hours=hours_per_month,
        )

    # Check if employee has valid SA ID or permit
    if not emp_doc.get("za_id_number"):
        # Could also check for asylum seeker permit field if implemented
        return eligibility_result(
            False,
            "Employee SA ID number not set",
            months=months_employed,
            hours=hours_per_month,
        )

    wage_check = check_eti_minimum_wage(
        emp_doc,
        salary_slip,
        payroll_settings,
        monthly_remuneration,
        hours_per_month,
    )
    if not wage_check.eligible:
        return eligibility_result(
            False,
            wage_check.reason,
            months=months_employed,
            hours=hours_per_month,
            **get_wage_audit_details(wage_check),
        )

    return eligibility_result(
        True,
        "Employee qualifies for ETI",
        months=months_employed,
        hours=hours_per_month,
        **get_wage_audit_details(wage_check),
    )


def eligibility_result(eligible, reason, months=0, hours=None, **details):
    """Return one stable eligibility payload for calculation and audit logging."""
    result = frappe._dict(
        eligible=eligible,
        reason=reason,
        months_employed=months,
        hours_per_month=hours,
    )
    result.update(details)
    return result


def get_wage_audit_details(wage_check):
    """Exclude control keys before merging wage evidence into eligibility."""
    return {key: value for key, value in wage_check.items() if key not in {"eligible", "reason"}}


def get_eti_hours(employee, salary_slip):
    """Use period-specific ordinary hours, falling back to the Employee master."""
    slip_hours = salary_slip.get("za_eti_hours") if hasattr(salary_slip, "get") else None
    if slip_hours is None or (salary_slip.is_new() and flt(slip_hours) <= 0):
        return flt(employee.get("za_hours_per_month"))
    return flt(slip_hours)


def check_eti_minimum_wage(employee, salary_slip, payroll_settings, remuneration, hours):
    """Validate the employee's wage against the explicitly configured ETI minimum."""
    if remuneration is None:
        return frappe._dict(eligible=False, reason="ETI remuneration was not provided")
    if hours <= 0:
        return frappe._dict(eligible=False, reason="ETI ordinary hours must be greater than zero")

    wage_basis = employee.get("za_eti_minimum_wage_basis")
    if wage_basis not in {WAGE_BASIS_REGULATED, WAGE_BASIS_UNREGULATED}:
        return frappe._dict(eligible=False, reason="ETI minimum wage basis is not configured")

    wage_paid, wage_components = get_eti_wage_paid(salary_slip)
    if not wage_components:
        return frappe._dict(
            eligible=False,
            reason="No Salary Component is marked as an ETI wage component",
        )

    if wage_basis == WAGE_BASIS_REGULATED:
        hourly_rate = flt(employee.get("za_eti_minimum_wage_rate"))
        if hourly_rate <= 0:
            return frappe._dict(
                eligible=False,
                reason="Applicable ETI minimum hourly wage is not configured",
            )
        minimum_wage = hourly_rate * hours
    else:
        monthly_floor = flt(payroll_settings.get("za_eti_unregulated_minimum_monthly_wage"))
        if monthly_floor <= 0:
            return frappe._dict(
                eligible=False,
                reason="Unregulated ETI minimum monthly wage is not configured",
            )
        minimum_wage = monthly_floor * min(hours, 160) / 160

    result = frappe._dict(
        eligible=wage_paid + 0.005 >= minimum_wage,
        wage_paid=flt(wage_paid, 2),
        minimum_wage=flt(minimum_wage, 2),
        monthly_remuneration=flt(remuneration, 2),
        wage_components=", ".join(wage_components),
    )
    result.reason = (
        "Employee meets the configured minimum wage"
        if result.eligible
        else f"ETI wage paid ({result.wage_paid:.2f}) is below the applicable minimum ({result.minimum_wage:.2f})"
    )
    return result


def get_eti_wage_paid(salary_slip):
    """Sum only earnings explicitly classified as wage for ETI section 4."""
    total = 0
    components = []
    earnings = salary_slip.get("earnings") if hasattr(salary_slip, "get") else []
    for row in earnings or []:
        component = row.get("salary_component")
        if component and frappe.get_cached_value("Salary Component", component, "za_eti_wage_component"):
            total += flt(row.get("amount"))
            components.append(component)
    return flt(total, 2), components


def get_eti_qualifying_month_number(employee, salary_slip, joining_date):
    """Return the current ETI cycle month from submitted audit history.

    Calendar elapsed months are used only for legacy employees who have no
    submitted ETI history at all. Once history exists, only distinct months
    recorded as qualifying consume one of the 24 available months.
    """
    calculation_date = getdate(salary_slip.end_date)
    filters = {
        "employee": employee,
        "docstatus": 1,
        "date": ["<", get_first_day(calculation_date)],
    }
    if getattr(salary_slip, "name", None):
        filters["against_salary_slip"] = ["!=", salary_slip.name]

    history = frappe.get_all(
        "Employee ETI Log",
        filters=filters,
        fields=["date", "is_qualifying_month", "eti_amount"],
        order_by="date asc",
    )
    if not history:
        return calculate_months_employed(joining_date, calculation_date)

    qualifying_months = {
        (getdate(row.date).year, getdate(row.date).month)
        for row in history
        if row.date and (cint(row.is_qualifying_month) or flt(row.eti_amount) > 0)
    }
    return len(qualifying_months) + 1


def calculate_eti_amount(employee, salary_slip, monthly_remuneration, eligibility=None):
    """Calculate date-effective ETI, using legacy Slabs only if no rate pack exists.

    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document
        monthly_remuneration (float): Monthly remuneration amount

    Returns:
        float: ETI amount for the month
    """
    # Check eligibility first
    eligibility = eligibility or check_eti_eligibility(employee, salary_slip, monthly_remuneration)

    if not eligibility["eligible"]:
        return 0

    months_employed = eligibility["months_employed"]
    remuneration = flt(monthly_remuneration)

    hours_per_month = eligibility.get("hours_per_month")
    calculation_date = getattr(salary_slip, "end_date", None)

    # Malformed packs are compliance errors and must not fall through silently.
    if find_rate_pack(calculation_date):
        return flt(
            calculate_eti_from_pack(
                remuneration,
                months_employed,
                calculation_date,
                hours_per_month=hours_per_month,
            ),
            2,
        )

    # Get ETI slab for calculation (based on employment period)
    eti_slab = get_eti_slab(months_employed, calculation_date)

    if not eti_slab:
        frappe.throw(
            frappe._("No ETI rate pack or submitted ETI Slab is configured for {0}.").format(
                getdate(calculation_date or frappe.utils.today())
            ),
            title=frappe._("Missing ETI Rates"),
        )

    standard_hours = flt(eti_slab.hours_in_a_month) or 160
    hours_ratio = 1
    if hours_per_month is not None:
        hours = flt(hours_per_month)
        if hours <= 0:
            return 0
        if hours < standard_hours:
            hours_ratio = hours / standard_hours
            remuneration /= hours_ratio

    # Determine which period (first 12 or second 12 months)
    is_first_period = months_employed <= 12

    eti_amount = 0

    # Apply ETI formulas based on remuneration brackets
    # Note: eti_slab_details is the child table name in ETI Slab DocType
    for detail in eti_slab.eti_slab_details:
        from_amt = flt(detail.from_amount)
        to_amt = flt(detail.to_amount)

        # Check if remuneration falls within this bracket
        if from_amt <= remuneration <= to_amt:
            # First 12 months or Second 12 months
            # For first 12 months, use first_qualifying_12_months field
            # For second 12 months, use second_qualifying_12_months field
            if is_first_period and not detail.first_qualifying_12_months:
                continue
            if not is_first_period and not detail.second_qualifying_12_months:
                continue

            # Calculate ETI amount based on bracket
            if detail.percentage and detail.percentage > 0:
                # Percentage-based calculation
                if detail.eti_amount and detail.eti_amount > 0:
                    # Declining formula: base amount - (percentage * (remuneration - from_amount))
                    decline_amount = (flt(detail.percentage) / 100) * (remuneration - from_amt)
                    eti_amount = flt(detail.eti_amount) - decline_amount
                    eti_amount = max(0, eti_amount)  # Cannot be negative
                else:
                    # Simple percentage: percentage * remuneration
                    eti_amount = (flt(detail.percentage) / 100) * remuneration
            elif detail.eti_amount:
                # Fixed amount
                eti_amount = flt(detail.eti_amount)
            else:
                # No ETI for this bracket
                eti_amount = 0

            break

    eti_amount *= hours_ratio

    return flt(eti_amount, 2)


def calculate_months_employed(joining_date, current_date):
    """
    Calculate the ETI month number for the current payroll month.

    ETI is claimed per qualifying calendar month, so the month an employee
    commences employment counts as month 1 (even if they joined part-way
    through it) and each subsequent calendar month increments the count. This
    determines whether the employee is in the first or second 12-month ETI
    window.

    Counting whole calendar months (rather than comparing the day-of-month)
    avoids undercounting employees who join late in a month, e.g. on the 31st.

    Args:
        joining_date (date): Date of joining
        current_date (date): Date within the payroll month being processed

    Returns:
        int: ETI month number (1 = first month of employment)
    """
    joining_date = getdate(joining_date)
    current_date = getdate(current_date)

    if current_date < joining_date:
        return 0

    # Inclusive calendar-month count: joining month is month 1.
    months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month) + 1

    return max(0, months)


def get_eti_slab(months_employed=1, date_value=None):
    """
    Get the current ETI Slab configuration based on employment period.

    Args:
        months_employed (int): Number of months employed (determines first/second 12 months)

    Returns:
        Document: ETI Slab document for the appropriate period
    """
    # Determine if first 12 or second 12 months
    period_keyword = "First" if months_employed <= 12 else "Second"
    calculation_date = getdate(date_value or frappe.utils.today())

    # Get the newest matching slab effective on the payroll date.
    slabs = frappe.get_all(
        "ETI Slab",
        filters={
            "docstatus": 1,
            "title": ["like", f"%{period_keyword}%"],
            "start_date": ["<=", calculation_date],
        },
        fields=["name", "start_date"],
        order_by="start_date desc",
        limit=1,
    )

    if slabs:
        return frappe.get_doc("ETI Slab", slabs[0].name)

    return None


def log_eti_calculation(employee, salary_slip, eti_amount, eligibility_details):
    """
    Log ETI calculation details for audit trail.

    Args:
        employee (str): Employee ID
        salary_slip: Salary Slip document
        eti_amount (float): Calculated ETI amount
        eligibility_details (dict): Eligibility check results
    """
    existing_log = frappe.db.exists(
        "Employee ETI Log", {"employee": employee, "against_salary_slip": salary_slip.name}
    )
    log_doc = frappe.get_doc("Employee ETI Log", existing_log) if existing_log else frappe.new_doc("Employee ETI Log")
    if log_doc.docstatus == 1:
        return log_doc.name

    log_doc.employee = employee
    log_doc.against_salary_slip = salary_slip.name
    log_doc.employee_name = getattr(salary_slip, "employee_name", None)
    log_doc.date = salary_slip.end_date
    log_doc.eti_amount = eti_amount
    log_doc.carry_forwarding_eti_amount = 0
    log_doc.is_qualifying_month = cint(eligibility_details.get("eligible"))
    log_doc.qualifying_month_number = (
        cint(eligibility_details.get("months_employed")) if eligibility_details.get("eligible") else 0
    )
    log_doc.eligibility_reason = eligibility_details.get("reason")
    log_doc.hours = flt(eligibility_details.get("hours_per_month"), 2)
    log_doc.monthly_remuneration = flt(eligibility_details.get("monthly_remuneration"), 2)
    log_doc.wage_paid = flt(eligibility_details.get("wage_paid"), 2)
    log_doc.minimum_wage = flt(eligibility_details.get("minimum_wage"), 2)
    log_doc.save(ignore_permissions=True)
    return log_doc.name


def submit_eti_log(employee, salary_slip):
    """Submit the calculation log only after its Salary Slip is submitted."""
    log_name = frappe.db.exists(
        "Employee ETI Log", {"employee": employee, "against_salary_slip": salary_slip.name}
    )
    if not log_name:
        frappe.throw(
            frappe._("Employee ETI Log is missing for Salary Slip {0}.").format(salary_slip.name),
            title=frappe._("Missing ETI Audit Log"),
        )
    log_doc = frappe.get_doc("Employee ETI Log", log_name)
    if log_doc.docstatus == 0:
        log_doc.submit()


def cancel_eti_log(employee, salary_slip):
    """Cancel the linked submitted ETI log with the Salary Slip."""
    log_name = frappe.db.exists(
        "Employee ETI Log", {"employee": employee, "against_salary_slip": salary_slip.name}
    )
    if not log_name:
        return
    log_doc = frappe.get_doc("Employee ETI Log", log_name)
    if log_doc.docstatus == 1:
        log_doc.cancel()


def get_employee_eti_history(employee, from_date=None, to_date=None):
    """
    Get ETI history for an employee.

    Args:
        employee (str): Employee ID
        from_date (date): Optional start date filter
        to_date (date): Optional end date filter

    Returns:
        list: List of ETI Log documents
    """
    filters = {"employee": employee, "docstatus": 1}

    if from_date:
        filters["date"] = [">=", from_date]
    if to_date:
        if "date" in filters:
            filters["date"] = ["between", [from_date, to_date]]
        else:
            filters["date"] = ["<=", to_date]

    return frappe.get_all(
        "Employee ETI Log",
        filters=filters,
        fields=[
            "name",
            "employee",
            "against_salary_slip",
            "date",
            "eti_amount",
            "is_qualifying_month",
            "qualifying_month_number",
        ],
        order_by="date desc",
    )


def calculate_total_eti_for_period(company, from_date, to_date):
    """
    Calculate total ETI for a company in a period (for EMP201/EMP501).

    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date

    Returns:
        float: Total ETI amount
    """
    # Get all eligible salary slips in the period
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "company": company,
            "start_date": [">=", from_date],
            "end_date": ["<=", to_date],
            "docstatus": 1,
        },
        fields=["name", "za_monthly_eti"],
    )

    total_eti = sum(flt(slip.get("za_monthly_eti", 0)) for slip in salary_slips)

    return flt(total_eti, 2)
