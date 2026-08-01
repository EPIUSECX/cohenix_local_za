# Pay Employees & Distribute Payslips

**Goal:** submit the payroll, post it to the accounts, pay staff by EFT, and send payslips.

## 1. Submit the slips and the Payroll Entry

1. With the draft slips reviewed, **submit** each Salary Slip (or use the Payroll Entry's submit action for the batch).
2. **Submit the Payroll Entry.** This posts the accounting entries — earnings, the statutory liabilities (PAYE, UIF, SDL), other deductions, and net pay to **Payroll Payable**.

## 2. Check the posting

- Open the **General Ledger** for the period and confirm the payroll accounts balance.
- **PAYE Payable – SARS** should equal the month's total PAYE (this becomes your EMP201 PAYE).
- **Payroll Payable** should equal total net pay (this is what you pay out).

## 3. Generate the bank payment file (EFT)

The localisation currently enables only **FNB Online Banking Enterprise CSV**. ABSA, Nedbank and Standard Bank formats are not supported.

- Create and review a **Payroll Payment Batch** from the submitted Payroll Entry, then submit it and generate its private FNB OBE CSV.
- Reconcile its source hash and control total, download securely, and upload through FNB's approved portal.
- The total in the file should equal the **Payroll Payable** amount from the posting.

> Employees must have valid banking details and not be marked *Not Paid Electronically*. Export is restricted to authorised HR Manager, Accounts Manager or System Manager users with batch write access. Complete an FNB low-value acceptance test before production use.

## 4. Distribute payslips

Print or email the **SA Salary Slip** print format to each employee. It reflects the SA earnings, deductions, employer contributions and statutory figures.

## Corrections

If you find an error after submitting, **cancel and amend** the salary slip (and re-post if needed) rather than editing posted data. Posted documents can't be deleted, by design.

## Next

Declare the month to SARS: [Submit the Monthly EMP201](emp201-monthly).
