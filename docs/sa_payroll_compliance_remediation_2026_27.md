# 2026/27 Payroll Remediation Verification Note

This document records the current verification scope for the 1 March 2026 to 28 February 2027 tax year. It is not a certificate of statutory compliance and does not replace employer, tax-practitioner, payroll-practitioner, bank or legal approval.

## Configured headline values

The date-effective 2026/27 statutory pack currently contains:

| Item | Configured value |
|---|---:|
| Primary / secondary / tertiary annual rebates | R17,820 / R9,765 / R3,249 |
| Under-65 / age-65 / age-75 tax thresholds | R99,000 / R153,250 / R171,300 |
| Medical scheme fees credit: main / first dependant / additional dependant, monthly | R376 / R376 / R254 |
| UIF monthly remuneration cap | R17,712 |
| UIF employee / employer rate | 1% / 1% |
| SDL employer rate | 1% |
| Reimbursive travel rate | R4.95/km |
| Retirement deduction cap | 27.5%, limited to R430,000 annually |
| COIDA annual earnings cap | R668,000 per employee |
| Employer-provided housing abatement | R99,000 |

Official-interest-rate entries are date-effective because the prescribed rate may change during a tax year. Do not replace these with one annual constant.

Before production use, reconcile every value to the applicable SARS guide, Gazette or Department of Employment and Labour notice, including later amendments. In particular, confirm the COIDA ceiling and assessment rate against the Compensation Fund notice for the relevant assessment year.

## Remediated behavior to verify

- PAYE uses date-effective slabs, rebates and medical credits and fails when required statutory configuration is absent.
- UIF, SDL and COIDA bases use explicit Salary Component classifications instead of unrestricted gross pay.
- Retirement deductions apply the percentage and annual monetary limit.
- ETI applies date-effective bands and eligibility controls; reconcile generated, utilised and carried-forward ETI on EMP201.
- Recurring and overwrite Additional Salary behavior is preserved from HRMS.
- Loan repayments, exchange rates and rounding remain in net-pay calculations after statutory adjustments.
- Submitted Company Car, Housing and Low Interest Loan benefits can create taxable non-cash Salary Slip rows without increasing cash net pay.
- EMP201, IRP5/IT3(a) and EMP501 are internal working papers with readiness/reconciliation controls.
- COIDA caps assessable remuneration per employee and uses the company/class industry rate.

## External-format boundary

ZA Local does **not** perform direct SARS or eCOID submission. It does not produce the SARS BRS payroll-import CSV or encrypted reconciliation file. Generic PDF and CSV exports are review aids only and must not be represented or uploaded as statutory submission files.

Payroll bank export is enabled only for FNB Online Banking Enterprise CSV through a submitted Payroll Payment Batch. Other bank formats require a separately implemented, versioned specification and formal bank acceptance testing.

## Required acceptance evidence

Do not approve go-live from a source-code review alone. On a disposable staging site restored from representative data:

1. back up and rehearse migration, then repeat it to assess idempotency;
2. run static checks and the complete server test suite;
3. stage and verify the documented E2E payroll, statutory, VAT and COIDA scenarios;
4. reconcile payroll to GL, payment batch, EMP201 and certificates;
5. reconcile VAT201 to posted tax rows and GL;
6. inspect role/permission boundaries and private files;
7. obtain FNB acceptance for a low-value payment file; and
8. obtain written payroll/tax practitioner approval of statutory sources, mappings, calculations and filing procedures.

See [TESTING.md](../TESTING.md) for commands and the full acceptance matrix.

## Signoff limits

Automated tests can establish repeatability against encoded expectations. They cannot determine whether an employee is legally eligible for ETI, whether a benefit valuation reflects all facts, whether a VAT supply is zero-rated, whether a directive applies, whether a COIDA classification/rate is correct, or whether SARS/DEL changed a requirement after the software release. Those decisions remain with the employer and appropriately qualified practitioners.
