# Payroll Entry & Salary Slips

**Payroll Entry** is the batch that creates and manages salary slips for a period. This is the start of the monthly payroll run.

## Pre-run checklist

- [ ] All employees to be paid have a **submitted Salary Structure Assignment** with the correct **Income Tax Slab** for the tax year.
- [ ] Statutory components are mapped in **Payroll Settings**.
- [ ] The **Payroll Period** and **Holiday List** for the period exist.
- [ ] New starters, terminations and pay changes for the month are captured.

## Step-by-step

1. **Create the Payroll Entry.** Go to **Payroll Entry → New**. Set **Company**, **Payroll Frequency** (e.g. Monthly), **Payroll Period**, and the **Start / End dates** for the period.

2. **Get Employees.** Use the action to pull employees who have an active salary structure assignment for the period. Review the list; remove anyone who should not be paid this run.

3. **Create Salary Slips.** This generates one **draft** Salary Slip per employee. The SA engine calculates PAYE, UIF, SDL, ETI, medical credit and retirement treatment on each slip as it is created.

4. **Review the slips** before submitting — see [Understanding the SA Salary Slip](understanding-the-salary-slip) and the review checklist in [Review, Submit & Post](review-submit-post).

## Payroll frequency

`za_local` supports per-employee payroll frequency (monthly, fortnightly, weekly) via the Employee Payroll Frequency configuration. Run a separate Payroll Entry per frequency, each with the matching period dates, so annualisation and statutory caps are applied correctly.

## Off-cycle and individual slips

You can also create a single **Salary Slip** directly for an off-cycle payment (e.g. a correction or a final settlement). The same SA calculations apply. For terminations and lump sums, see [Tax Directives & Final Settlements](../full-suite-statutory-submissions/directives-and-final-settlements).

## Common issues at this stage

- **No employees pulled** — check that assignments are *submitted* and dated on/before the period, and that the company matches.
- **A slip is missing components** — the employee's salary structure is missing earnings/deductions, or the structure is not assigned.
- **PAYE looks wrong** — almost always the Income Tax Slab on the assignment is for the wrong tax year.

## Next

Understand what the engine computed: [Understanding the SA Salary Slip](understanding-the-salary-slip).
