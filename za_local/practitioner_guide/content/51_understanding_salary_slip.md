# Understanding the SA Salary Slip

`za_local`'s Salary Slip override computes the South African statutory amounts. This page explains what each calculated figure means so you can review slips with confidence.

## What the engine calculates

| Figure | How it is derived |
|---|---|
| **Gross pay** | Sum of earnings. |
| **Taxable income** | Gross, adjusted for each component's **PAYE inclusion %** (e.g. only 80% of a fixed travel allowance), less pre-tax deductions such as deductible retirement contributions. Annualised over the payroll period. |
| **PAYE** | Annualised taxable income run through the **Income Tax Slab** brackets, less age-based **rebates** (primary/secondary/tertiary), less the **medical scheme tax credit**, de-annualised to the period. ETI does **not** reduce the employee's PAYE on the slip — it reduces what the employer pays over on the EMP201. |
| **UIF (employee)** | 1% of the UIF base (capped at the monthly UIF cap from the rate pack). |
| **UIF (employer)** | 1% on the same capped base, as a company contribution. |
| **SDL** | 1% of the SDL base, as a company contribution (employer cost). |
| **ETI** (`za_monthly_eti`) | Employment Tax Incentive for eligible employees, from the ETI Slab band for their remuneration and employment-month, prorated by hours. Stored on the slip and consumed by the EMP201. |
| **Retirement excess** (`za_retirement_fund_taxable_excess`) | Retirement contributions above the deductible cap, added back to taxable income. |
| **Total company contribution** | Sum of employer contributions (UIF employer, SDL, employer retirement/medical). |
| **Net pay** | Gross less employee deductions (PAYE, employee UIF, medical, retirement, etc.). |

## Reading the statutory bases

UIF, SDL and COIDA each have their own base, controlled by the **UIF/SDL/COIDA Applicable** flags on the salary components. A component only enters a base if its flag is set. This is why component configuration ([Salary Components & SA Treatment](../full-suite-payroll-foundations/salary-components)) matters: a mis-flagged component silently shifts the statutory bases.

## PAYE inclusion percentage

The **PAYE inclusion %** on a component determines how much of it is taxed monthly. A **Fixed Travel Allowance** defaults to 80% inclusion (the standard treatment where the employee uses the vehicle substantially for business). Where the statutory rule allows 20% inclusion, set the component's inclusion percentage accordingly. The engine annualises the included portion correctly across the period.

## ETI on the slip vs the EMP201

The slip shows the **calculated ETI** (`za_monthly_eti`) for visibility, but ETI is an **employer** incentive: it reduces the PAYE the employer pays to SARS, declared on the **EMP201**. The employee's own PAYE and net pay are unaffected by ETI. Keep this distinction clear when explaining a payslip to an employee.

## What to sanity-check on each slip

- PAYE is non-zero for taxable earners and not absurdly high (a sign of wrong-year slab or missing rebate).
- UIF employee and employer are equal and capped.
- ETI appears only for eligible employees and is within the band maximum.
- Retirement excess is zero unless contributions genuinely exceed the cap.
- The medical tax credit reduced PAYE where the employee is on a scheme.

## Next

Work through the [Review, Submit & Post](review-submit-post) routine.
