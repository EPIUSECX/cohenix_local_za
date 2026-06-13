# Salary Components & SA Treatment

Salary Components are the building blocks of pay. `za_local` extends each component with **SA payroll-treatment fields** that drive PAYE inclusion, statutory bases (UIF/SDL/COIDA), and IRP5 grouping. Getting these right is the single most important step for accurate South African payroll.

## The SA fields on Salary Component

| Field | Purpose | Typical default |
|---|---|---|
| SARS Payroll Code | Links the component to its IRP5 code. | per component |
| Exclude from IRP5 | Hide the component from the certificate. | 0 |
| Payroll Treatment | Classifies how the component is taxed/handled (see below). | Regular Remuneration |
| PAYE Inclusion % | Portion of the component subject to PAYE. | 100 |
| UIF Applicable | Include in the UIF base. | 1 |
| SDL Applicable | Include in the SDL base. | 1 |
| COIDA Applicable | Include in the COIDA base. | 1 |
| Is Reimbursement | Mark non-taxable reimbursements. | 0 |
| Variable Pay Treatment | How variable pay is annualised (Recurring Annualised / Once-Off Full Tax / Manual Review). | Recurring Annualised |

### Payroll Treatment options

Regular Remuneration, Annual Payment, Overtime, Commission, Fixed Travel Allowance, Reimbursive Travel, Non-Taxable Reimbursement, PAYE, UIF, SDL, Retirement Fund, Medical Aid, Severance Benefit, Leave Payout, Notice Pay, and Working Paper Only.

The treatment, not the component name, is what the engine uses. For example, a **Fixed Travel Allowance** defaults to **80% PAYE inclusion** (only 80% of the allowance is taxed monthly), which the engine applies automatically.

## Seeded components

When HRMS is installed, these components are seeded with SA treatment and account mappings:

- **PAYE** (deduction, variable based on taxable salary)
- **UIF Employee Contribution** (deduction, 1% capped at the monthly UIF cap)
- **UIF Employer Contribution** (company contribution)
- **SDL Contribution** (company contribution, 1%)
- **Severance Benefit**, **Leave Payout**, **Notice Pay**, **Tax on Lump Sum**

The seeding also applies sensible classifications to common components if they exist (Basic Salary, Travel/Transport Allowance, Performance Bonus / 13th Cheque, Commission, Overtime, Medical Aid, Retirement Fund).

## Reference configuration

A practical starting point for a standard employer:

| Component | Type | Treatment | PAYE % | UIF | SDL | COIDA | SARS code |
|---|---|---|---|---|---|---|---|
| Basic Salary | Earning | Regular Remuneration | 100 | 1 | 1 | 1 | 3601 |
| Travel Allowance | Earning | Fixed Travel Allowance | 80 | 1 | 1 | 1 | 3701 |
| Overtime | Earning | Overtime | 100 | 1 | 1 | 1 | 3601 |
| Commission | Earning | Commission | 100 | 1 | 1 | 1 | 3606 |
| 13th Cheque / Bonus | Earning | Annual Payment | 100 | 1 | 1 | 1 | 3605 |
| PAYE | Deduction | PAYE | 0 | 0 | 0 | 0 | 4102 |
| UIF Employee Contribution | Deduction | UIF | 0 | 0 | 0 | 0 | 4141 |
| UIF Employer Contribution | Company Contribution | UIF | 0 | 0 | 0 | 0 | 4141 |
| SDL Contribution | Company Contribution | SDL | 0 | 0 | 0 | 0 | 4142 |
| Medical Aid | Deduction | Medical Aid | 0 | 0 | 0 | 0 | 4005 |
| Pension / Provident | Deduction | Retirement Fund | 0 | 0 | 0 | 0 | 4001 |
| Severance Benefit | Earning | Severance Benefit | 100 | 0 | 0 | 0 | 3901 |
| Leave Payout | Earning | Leave Payout | 100 | 1 | 1 | 1 | 3907 |
| Notice Pay | Earning | Notice Pay | 100 | 1 | 1 | 1 | 3601 |

> Treat this as a template, not gospel. Confirm SARS codes and treatments against the current SARS PAYE BRS and the client's actual remuneration policy. Where a component's statutory treatment is unusual, set the SA fields explicitly rather than relying on the default.

## Component accounts

Each component's **Accounts** table maps it to a GL account per company. Confirm the statutory components point at the right accounts (PAYE Payable – SARS, UIF liability/expense, SDL Expense) before the first payroll run, so the [posting](../full-suite-running-payroll/review-submit-post) is correct.

## Next

Build [Salary Structures & Assignments](salary-structures).
