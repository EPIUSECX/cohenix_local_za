# Year-End: IRP5 & EMP501

**Goal:** produce employee tax certificates (IRP5/IT3(a)) and reconcile the year with the EMP501. This runs at the SARS interim and annual reconciliation periods.

## The two pieces

- **IRP5 / IT3(a) Certificate** — each employee's annual tax certificate. (Where no tax was deducted, the same record is an IT3(a).)
- **EMP501 Reconciliation** — ties the twelve monthly EMP201s to the IRP5 certificates and proves they agree.

## 1. Generate IRP5 certificates

1. SA Payroll workspace → generate the **IRP5 Certificate** records for the company and tax year (individually or in bulk).
2. The system sums each employee's salary-slip amounts for the year and groups them under their **SARS payroll codes** (income, deductions, employer contributions).
3. **Review each certificate:** ID/passport and income tax reference number present, residential and postal addresses complete, codes and amounts correct, and totals matching the year's slips.
4. **Print** with the **IRP5 Employee Certificate** format (or **IRP5-it3 Certificate** for IT3(a) cases).

## 2. Build the EMP501 reconciliation

1. **New EMP501 Reconciliation** → set company and tax year (1 March – end February).
2. **Link the twelve EMP201s** and the **IRP5 certificates**.
3. **Run the readiness checks.** The reconciliation verifies employer references, that all months are covered, that every employee has an IRP5, that SARS codes are complete, and that directive numbers exist for any lump sums.
4. **Reconcile.** The legs must agree: sum of monthly EMP201 PAYE = sum of IRP5 PAYE = PAYE actually paid to SARS.
5. **File** on SARS eFiling / e@syFile once the checks pass and the legs reconcile.

> If the EMP501 won't submit, a readiness check failed — read the message (missing month, unlinked IRP5, missing reference or directive) and fix the underlying record. This is intentional.

## Leavers and lump sums

Severance, retirement lump sums and some leave payouts need a **SARS tax directive**, and the directive number must appear on the IRP5. The detail is in the practitioner guide → [Tax Directives & Final Settlements](/sa-guide/full-suite-statutory-submissions/directives-and-final-settlements).

## Next

Learn the reports that support all of this: [Finding & Running Reports](../reports/finding-reports).
