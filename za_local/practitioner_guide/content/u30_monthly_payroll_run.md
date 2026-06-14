# Run a Monthly Payroll

**Goal:** generate salary slips for the month using a Payroll Entry. (Requires Frappe HR.)

## Before you run

- New starters, leavers and pay changes for the month are captured.
- Each employee to be paid has a **submitted Salary Structure Assignment** with the correct **Income Tax Slab** for the tax year.
- The **Payroll Period** and **Holiday List** for the period exist.

## Steps

1. **New Payroll Entry.** SA Payroll workspace → **Payroll Entry → New**.
2. **Set the run.** Choose **Company**, **Payroll Frequency** (e.g. Monthly), **Payroll Period**, and the **Start / End dates**.
3. **Get Employees.** Run the action to pull employees with an active assignment for the period. Review the list and remove anyone who shouldn't be paid this run.
4. **Create Salary Slips.** This generates one **draft** salary slip per employee. As each slip is created, the South African engine calculates PAYE, UIF, SDL, ETI, the medical tax credit and retirement treatment.
5. **Review the slips** before submitting — see [Reviewing a Salary Slip](reviewing-a-payslip).

## Different pay frequencies

If you pay some staff weekly/fortnightly and others monthly, run a **separate Payroll Entry per frequency** with the matching period dates, so annualisation and statutory caps apply correctly.

## Off-cycle / single payments

For a one-off (a correction, or a leaver's final pay) you can create a single **Salary Slip** directly. The same SA calculations apply. For terminations and lump sums, the directive/severance handling is in the practitioner guide → [Tax Directives & Final Settlements](/sa-guide/full-suite-statutory-submissions/directives-and-final-settlements).

## Common issues

- **No employees pulled** → assignments aren't submitted, are dated after the period, or the company doesn't match.
- **A slip is missing a component** → the employee's salary structure is incomplete or not assigned.
- **PAYE looks wrong** → the Income Tax Slab on the assignment is for the wrong tax year.

## Next

Check what the engine produced: [Reviewing a Salary Slip](reviewing-a-payslip).
