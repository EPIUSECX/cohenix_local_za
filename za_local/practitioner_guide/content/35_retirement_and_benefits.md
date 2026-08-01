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
2. Create a date-effective **Employee Private Benefit** record with a positive private-medical-aid contribution and the medical dependant count. Prevent overlapping active records. The engine uses this record to compute the medical scheme fees tax credit.

The medical tax credit rates come from the statutory rate pack (Tax Rebates and Medical Tax Credit).

## Fringe benefits

Do not use Employee Private Benefit for non-medical fringe benefits. Create and submit the relevant **Company Car Benefit**, **Housing Benefit** or **Low Interest Loan Benefit** detail, link it to a submittable **Fringe Benefit**, and submit that record. Active submitted benefits flow to Salary Slips as taxable non-cash earnings: they affect PAYE and certificate reporting without increasing cash net pay or payroll accounting earnings.

- Company car: 3.5% monthly, or 3.25% with a maintenance plan; verify whether 80% or the documented 20% PAYE inclusion applies.
- Housing: apply the paragraph 9 formula, date-effective abatement/percentage, employer spend rules and employee consideration.
- Low-interest loan: maintain current outstanding balance; the benefit uses the date-effective official rate (repo plus one percentage point).

Cellphone, fuel-card and other benefit types require a supported valuation/mapping and practitioner evidence before use. Never assume that merely creating a record guarantees the correct IRP5 code or legal valuation.

## Next

Capture your [Employee Master & SA Details](../full-suite-employees/employee-master).
