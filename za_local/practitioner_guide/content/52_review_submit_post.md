# Review, Submit & Post to the Ledger

Once salary slips are calculated, review them, submit, and post the payroll to the general ledger.

## 1. Review checklist (before submitting)

Run these checks on the draft slips, using the [Payroll Register](payments-and-reports) report for a batch view:

- [ ] **Headcount** matches the expected number of employees for the period.
- [ ] **PAYE** is reasonable for each earner; spot-check one manually against the Income Tax Slab.
- [ ] **UIF** employee = employer, and both are capped at the monthly UIF cap.
- [ ] **SDL** is 1% of the SDL base (employer only).
- [ ] **ETI** appears only for eligible employees and within band limits.
- [ ] **Retirement excess** is zero unless contributions exceed the cap.
- [ ] **Medical tax credit** applied for scheme members.
- [ ] **Net pay** is positive and sensible for each employee.
- [ ] No employee is missing a mandatory component.

## 2. Submit the salary slips

Submit each Salary Slip (or use the Payroll Entry's submit action to submit the batch). Submission locks the calculated figures and makes them available to the EMP201.

## 3. Submit the Payroll Entry and post accounting

Submit the **Payroll Entry**. `za_local`'s Payroll Entry override creates the accounting entries, posting employer contributions (UIF employer, SDL) correctly alongside earnings, employee deductions and net pay.

A typical posting per period aggregates to:

| Account | Dr | Cr |
|---|---|---|
| Salaries and Wages | gross earnings | |
| UIF Employer Expense | employer UIF | |
| SDL Expense | SDL | |
| PAYE Payable – SARS | | PAYE |
| UIF (employee + employer) liability | | UIF |
| Medical Aid / Pension payable | | employee deductions |
| Payroll Payable | | net pay |

The entry balances: total debits (gross + employer costs) equal total credits (statutory liabilities + other deductions + net pay).

## 4. Verify the posting

- Open the **General Ledger** filtered to the payroll accounts for the period and confirm the entries match the Payroll Register totals.
- Confirm **PAYE Payable – SARS** equals the period's total PAYE (this becomes your EMP201 PAYE).
- Confirm **Payroll Payable** equals total net pay (this drives the bank payment).

## Corrections

If you find an error after submission, **cancel and amend** the salary slip (and re-post if needed) rather than editing posted data. The audit-trail protections prevent deletion of posted documents by design.

## Next

Pay employees and review reports: [Payroll Payments & Reports](payments-and-reports).
