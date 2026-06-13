# Retirement Funds & Private Benefits

These are optional but common. Configure them before payroll so retirement deductions, the retirement-deduction cap, and medical tax credits are applied correctly.

## Retirement funds

Create a **Retirement Fund** record for each pension, provident or retirement-annuity fund the employer offers:

| Field | Notes |
|---|---|
| Fund Name | e.g. "Company Pension Fund". |
| Fund Type | Pension Fund, Provident Fund or Retirement Annuity. |
| Company | The company. |
| Employee Contribution % | The member contribution rate. |
| Employer Contribution % | The employer contribution rate. |

Then create the matching **Salary Components**:

- An employee deduction component (treatment **Retirement Fund**, 0% PAYE inclusion — contributions reduce taxable income), mapped to SARS code 4001 and the retirement liability account.
- An employer contribution component in the Salary Structure's **Company Contribution** table, if the employer contributes.

### The retirement-deduction cap

South African tax limits the deductible retirement contribution to a percentage of remuneration up to an annual cap (both held in the statutory rate pack). The salary-slip engine applies this automatically: contributions above the cap are not deductible, and the engine records the **non-deductible excess** in the salary slip field `za_retirement_fund_taxable_excess`, adding it back to taxable income. You do not calculate this by hand — but you should review it (see [Understanding the SA Salary Slip](../full-suite-running-payroll/understanding-the-salary-slip)).

## Medical aid and the medical tax credit

For employees on a medical scheme:

1. Add a **Medical Aid** deduction component (treatment Medical Aid, SARS code 4005).
2. Record the number of dependants on the **Employee** (`Number of Dependants` field) so the engine can compute the **medical scheme fees tax credit** (main member + dependants) and offset it against PAYE.

The medical tax credit rates come from the statutory rate pack (Tax Rebates and Medical Tax Credit).

## Fringe / private benefits

`za_local` provides DocTypes for common fringe benefits, captured per employee via **Employee Private Benefit** and the specific benefit types:

- Company Car Benefit
- Housing Benefit
- Low-Interest Loan Benefit
- Cellphone Benefit
- Fuel Card Benefit
- Bursary Benefit

Capture the benefit details so the taxable fringe-benefit value flows into the employee's remuneration and onto the IRP5 under the correct SARS code. Configure these for employees who receive such benefits before processing their pay.

## Next

Capture your [Employee Master & SA Details](../full-suite-employees/employee-master).
