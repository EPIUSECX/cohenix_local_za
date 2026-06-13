# Salary Structures & Assignments

A **Salary Structure** defines the earnings, deductions and company contributions for a pay grade or role. A **Salary Structure Assignment** attaches a structure to an individual employee, with their base salary and the income tax slab to use.

## 1. Create a Salary Structure

Go to **Salary Structure → New**:

1. **Name** it for the grade/year, e.g. `General Staff 2026-27`.
2. **Company** — set it.
3. **Earnings** — add components (Basic Salary, Travel Allowance, etc.), each with an amount or formula.
4. **Deductions** — add PAYE, UIF Employee Contribution, Medical Aid, Pension, etc. PAYE and UIF are formula/auto-calculated by the SA engine, so you do not hand-key their amounts.
5. **Company Contribution** — `za_local` adds a *Company Contribution* table to the Salary Structure. Add **UIF Employer Contribution** and **SDL Contribution** here (and employer retirement/medical if applicable). These are employer costs, not employee deductions.
6. **Save and Submit.**

> The Company Contribution table is what feeds employer UIF/SDL and other employer costs onto the salary slip and into the payroll posting. If it is empty, employer contributions will not post.

## 2. Create a Salary Structure Assignment per employee

Go to **Salary Structure Assignment → New** for each employee:

| Field | Value |
|---|---|
| Employee | The employee. |
| Salary Structure | The structure from step 1. |
| Company | The company. |
| From Date | When this structure takes effect (use 1 March for a new tax year). |
| Base | The employee's monthly base salary. |
| Income Tax Slab | The Income Tax Slab for the **tax year of the payroll period** (e.g. `South Africa 2026-2027`). |
| Annual Bonus | (`za_local` field) Expected annual bonus, used to annualise PAYE correctly. |

**Submit** the assignment.

> The **Income Tax Slab** link is critical: PAYE is computed from the slab on the assignment. If it points at the wrong year, PAYE will be wrong. At each tax-year rollover, create a fresh assignment dated 1 March linked to the new slab.

## 3. Multiple structures and changes

- Use separate structures for materially different remuneration models (e.g. monthly-paid staff vs commission earners).
- When an employee's pay changes mid-year, create a **new** assignment with the new base and a later *From Date*; do not edit a submitted assignment.

## Optional: retirement funds and private benefits

If the employer offers retirement funds or fringe benefits, configure them next in [Retirement Funds & Private Benefits](retirement-and-benefits) before running payroll, so deductions and medical tax credits compute correctly.

## Next

Configure [Retirement Funds & Private Benefits](retirement-and-benefits), then capture your [Employee Master & SA Details](../full-suite-employees/employee-master).
