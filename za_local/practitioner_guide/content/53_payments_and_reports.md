# Payroll Payments & Reports

With the payroll posted, pay employees and use the reports to validate and reconcile the run.

## Paying employees (EFT)

`za_local` includes an **EFT file generator** to produce bank payment files from a submitted Payroll Entry. It supports Standard Bank and FNB formats (other banks can be prepared manually).

To generate a file, call the endpoint for the payroll entry, choosing the bank format:

```
za_local.utils.integrations.eft_file_generator.generate_eft_file
  payroll_entry=<Payroll Entry name>
  bank_format="standard_bank"   # or "fnb"
```

It returns the file content and a filename to download and upload to your banking portal. Access requires read permission on the Payroll Entry (it contains employee banking details and net pay), and the bank format is validated.

> Employees must have valid banking details (and *Not Paid Electronically* unticked) for inclusion. The net pay total in the file should equal the **Payroll Payable** credit from the posting.

## Distributing payslips

Print or email the **SA Salary Slip** print format. It reflects the SA earnings, deductions, employer contributions and statutory figures.

## Reports

The **SA Payroll** workspace provides the validation and reconciliation reports:

| Report | Use |
|---|---|
| **Payroll Register** | All employees with earnings, deductions, net pay and statutory amounts for the period. Your primary review and reconciliation view. |
| **EMP201 Report** | PAYE, UIF, SDL and ETI totals for the month — the basis for the EMP201 declaration. |
| **Statutory Submissions Summary** | Consolidated statutory totals across periods. |
| **Retirement Fund Deductions** | Retirement contributions by employee/component, to reconcile against fund schedules. |
| **Department Cost Analysis** | Payroll cost by department. |

Standard HRMS reports (Salary Register, Bank Remittance, Income Tax Computation) remain available too.

## Month-end reconciliation routine

1. Payroll Register totals = General Ledger payroll postings.
2. PAYE Payable – SARS balance = EMP201 PAYE.
3. UIF (employee + employer) = EMP201 UIF.
4. SDL = EMP201 SDL.
5. ETI total = sum of `za_monthly_eti` across slips.
6. Payroll Payable = EFT batch net pay.

When these tie out, you are ready to declare on the EMP201.

## Next

Move to statutory submissions, starting with the [EMP201 Monthly Declaration](../full-suite-statutory-submissions/emp201).
