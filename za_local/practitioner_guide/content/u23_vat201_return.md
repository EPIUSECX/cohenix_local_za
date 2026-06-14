# Prepare & Review the VAT201 Return

**Goal:** build the periodic VAT201 working paper from your posted invoices, review it, and file it on SARS eFiling.

## Before you start

- All sales and purchase invoices for the period are **submitted**.
- Item VAT categories and tax templates are correct (this is what makes classification accurate).

## Steps

1. **New VAT201 Return.** SA VAT workspace → **VAT201 Return → New**.
2. **Set the period.** Choose the **company**, the **period** (matching your filing frequency), and the **From / To dates**.
3. **Get VAT Transactions.** Click the fetch action to pull every posted sales and purchase invoice in the period into the transactions table.
4. **Review classifications.** Each row shows its type (Sales/Purchase) and classification (standard output, zero-rated, exempt, standard/capital input, etc.). Rows the system can't classify confidently are flagged **needs review**.
5. **Clear the review rows.** For each flagged row, check the item's VAT category and the tax template on the source document, correct it, and re-fetch. Aim for zero review rows.
6. **Check the totals.** The return computes **Total Output VAT**, **Total Input VAT**, and **VAT Payable = Output − Input** (or a refund).
7. **File on eFiling.** Export/print the return and capture it on **SARS eFiling**. The system produces the working paper and audit trail; the submission itself is manual.

## Reconcile before you file

- Use the VAT reports to cross-check — see [VAT Reports](../reports/vat-reports).
- Confirm the VAT Payable figure agrees with your **VAT Output** and **VAT Input** ledger balances for the period.

## Monthly/period routine (summary)

Post all invoices → create VAT201 Return → **Get VAT Transactions** → clear review rows → reconcile against the ledger → export and file on eFiling → record the payment or refund.

## Common issues

- **Many "needs review" rows** → items missing a VAT category, or wrong tax template on source documents. Fix the source and re-fetch.
- **Totals don't tie to the ledger** → an invoice was posted/credited after you fetched; re-fetch the return.

## Next

Learn the reports that support the return: [VAT Reports](../reports/vat-reports). If you also run payroll, continue to [Run a Monthly Payroll](../running-payroll/monthly-payroll-run).
