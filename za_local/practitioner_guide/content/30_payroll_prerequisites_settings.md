# Payroll Prerequisites & Settings

This section begins the **full suite**. It assumes HRMS is installed and the [Foundation Setup](../foundation-setup-both-tracks/company-registration) is done.

## Prerequisites checklist

Before configuring payroll, confirm:

- [ ] **HRMS is installed** and the **SA Payroll** workspace is visible.
- [ ] Company **PAYE, UIF and SDL reference numbers** are captured (needed for EMP201/EMP501).
- [ ] **Chart of Accounts** includes Salaries and Wages, PAYE Payable – SARS, UIF Employee Contribution, UIF Employer Expense, SDL Expense and Payroll Payable.
- [ ] A **Fiscal Year** and **Payroll Period** for the active tax year (1 March – end February) exist.
- [ ] A **Holiday List** is assigned to the company.
- [ ] The statutory rate pack for the active tax year resolves (see [Post-Install Verification](../getting-started/post-install-verification)).

## Payroll Settings — SA statutory components

`za_local` adds a **South African Settings** section to **Payroll Settings** (HRMS). Open **Payroll Settings** and complete it. This mapping tells the salary-slip engine which Salary Components represent each statutory item.

| Field | Map to component | Notes |
|---|---|---|
| PAYE Salary Component | `PAYE` | The deduction component for employees' tax. |
| UIF Employee Salary Component | `UIF Employee Contribution` | Employee's 1% UIF. |
| UIF Employer Salary Component | `UIF Employer Contribution` | Employer's 1% UIF (company contribution). |
| SDL Salary Component | `SDL Contribution` | Skills Development Levy (company contribution). |
| COIDA Salary Component | (optional) | If you track COIDA via a component. |

Also set:

- **Calculate Annual Taxable Amount Based On** — *Payroll Period* (default, recommended) or *Joining/Relieving Date*. This controls how income is annualised for PAYE.
- **Disable ETI Calculation** — leave unticked unless the employer does not claim ETI.

> These statutory components are seeded on install (when HRMS is present). If a dropdown is empty, the component seeding did not run — re-run `bench migrate`, then re-open Payroll Settings.

## Mileage / reimbursement rate

`za_local` adds an **Amount per Kilometre** field to the HR/Payroll settings for mileage reimbursement (used by Business Trips). Set it to the current prescribed reimbursive rate, or rely on the [Travel Allowance Rate](statutory-rate-data) seeded from the statutory pack.

## Next

Load and verify the [Statutory Rate Data](statutory-rate-data) (tax slabs, rebates, medical credits, ETI).
