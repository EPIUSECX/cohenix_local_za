# Reviewing a Salary Slip

**Goal:** understand and sanity-check a salary slip before you submit it.

## What's on the slip

| Figure | Meaning |
|---|---|
| **Gross pay** | Total earnings. |
| **PAYE** | Employees' tax, from the tax slab less rebates and the medical tax credit. |
| **UIF (employee)** | 1% of the UIF base, capped at the monthly UIF cap. |
| **UIF (employer)** | 1% on the same base (an employer cost). |
| **SDL** | 1% of the SDL base (an employer cost). |
| **ETI** (monthly ETI) | Employment Tax Incentive for eligible young/low earners. Shown for visibility. |
| **Net pay** | Gross less employee deductions (PAYE, employee UIF, medical, retirement, etc.). |
| **Total company contribution** | Sum of employer costs (UIF employer, SDL, employer retirement/medical). |

## Two things people get wrong

- **ETI doesn't reduce the employee's pay.** It's an *employer* incentive that reduces the PAYE the employer pays to SARS on the EMP201. The employee's PAYE and net pay are unaffected.
- **Travel allowances are partly taxed.** A fixed travel allowance is taxed at 80% by default (only 80% enters PAYE monthly). That's correct, not an error.

## Quick sanity-check per slip

- PAYE is non-zero for taxable earners and not wildly high (a sign of the wrong-year tax slab).
- Employee UIF = employer UIF, both capped.
- ETI appears only for eligible employees.
- The medical tax credit reduced PAYE for scheme members.
- Net pay is positive and sensible.

If something looks off, it usually traces back to the employee's **Salary Structure Assignment** (wrong tax slab year) or a **Salary Component**'s configuration. For the detail of how each figure is derived, see the practitioner guide → [Understanding the SA Salary Slip](/sa-guide/full-suite-running-payroll/understanding-the-salary-slip).

## Next

Once the slips look right: [Pay Employees & Distribute Payslips](pay-employees).
