# SARS Payroll Codes

**SARS Payroll Code** records are the income, deduction and employer-contribution codes that appear on the IRP5/IT3(a) certificate. Each Salary Component maps to one of these codes so that, at year-end, the IRP5 groups amounts under the correct SARS code.

## Seeded codes

A default set of SARS codes is seeded on install. Open the **SARS Payroll Code** list (SA Payroll workspace) to review them. Each record carries:

| Field | Meaning |
|---|---|
| Code | The SARS code, e.g. `3601` (income), `4102` (PAYE), `4141` (UIF). |
| Description | Human-readable label. |
| Category | Income, Deduction, Tax Credit or Employer Contribution. |
| Tax Treatment | Taxable, Non-Taxable or Reference. |
| Print Sequence | Controls ordering on the IRP5. |
| Active | Whether the code is in use. |

## Common codes you will use

| Code | Typical use |
|---|---|
| 3601 | Income — normal remuneration (salary/wages). |
| 3605 | Annual payment (bonus / 13th cheque). |
| 3701 / 3702 | Travel allowance (fixed / reimbursive context). |
| 3697 / 3698 | Gross retirement-funding / non-retirement-funding income totals. |
| 4001 | Pension/retirement-annuity fund contributions. |
| 4005 | Medical scheme contributions. |
| 4102 | PAYE. |
| 4141 | UIF (employee + employer). |
| 4142 | SDL. |

> Always confirm codes against the current **SARS PAYE BRS (Business Requirements Specification)** for the tax year you are filing. Codes and their validation rules are updated periodically.

## Mapping components to codes

You assign the SARS code on each **Salary Component** via the `za_local` *SARS Payroll Code* field. You can also tick *Exclude from IRP5* on components that should never appear on the certificate (for example working-paper-only items). This mapping is covered next in [Salary Components & SA Treatment](salary-components).

## Permissions

SARS Payroll Code, Tax Rebates and ETI Slab are statutory configuration. They are editable by **System Manager** and **HR Manager**, and readable by **HR User**, so payroll staff can verify the codes and rates being applied without holding the System Manager role.

## Next

Configure [Salary Components & SA Treatment](salary-components).
