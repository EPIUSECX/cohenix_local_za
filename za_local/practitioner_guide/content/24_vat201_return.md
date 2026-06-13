# VAT201 Return Workflow & Reports

The **VAT201 Return** is a working paper that gathers your posted sales and purchase transactions for a VAT period, classifies them, and totals output and input VAT for manual submission on SARS eFiling.

## Prerequisites

- [South Africa VAT Settings](vat-settings) configured for the company.
- Tax templates and item VAT categories in place ([Tax Templates & Item VAT Categories](tax-templates-item-categories)) so transactions carry the correct classification.
- Sales and Purchase Invoices for the period **posted (submitted)**.

## Step-by-step

1. **Create the return.** Go to **VAT201 Return → New**. Set the **Company**, the **period** (matching your filing frequency), and the **From / To dates**. The vendor type and rates come from your VAT settings.

2. **Pull transactions.** Use **Get VAT Transactions** (the fetch action) to populate the transaction table with all posted Sales and Purchase Invoices in the period.

3. **Review classifications.** Each row carries a transaction type (Sales/Purchase) and a classification — for example Standard Output, Zero-Rated Output, Exempt, Standard Input or Capital Input. Rows the app cannot classify confidently are flagged for review.

4. **Resolve "needs review" rows.** For each flagged row, check the underlying item's VAT category and the tax template used. Correct the source document or item classification, then re-fetch. Clean source data means fewer review rows.

5. **Check the totals.** The return computes Total Output VAT, Total Input VAT, and **VAT Payable = Output − Input** (or a refund if input exceeds output).

6. **File on SARS eFiling.** Export/print the return and capture it on eFiling. `za_local` does **not** submit electronically to SARS — it produces the working paper and audit trail; the eFiling submission is manual.

## Reconciling before you file

Use the VAT reports in the **SA VAT** workspace to sanity-check the return:

- **VAT 201 Linked Transactions** — drill from a VAT201 line back to the source invoices.
- **VAT 201 Account Classifications** — verify each VAT account maps to the right return field.
- **VAT Analysis** — review output/input VAT by period and rate.

Cross-check the VAT Payable figure against your **VAT Output** and **VAT Input** ledger balances in the General Ledger for the period. They should agree.

## Periodic routine (summary)

Each VAT period: post all sales/purchase invoices → create VAT201 Return → Get VAT Transactions → clear review rows → reconcile against the GL → export and file on eFiling → record the payment/refund.

## Next

- **ERPNext-only track:** VAT setup is complete. Review the [SA Labour](../sa-labour-coida/sa-labour) and [SA COIDA](../sa-labour-coida/sa-coida) modules if the client needs them, and the [Reference & Operations](../reference-operations/custom-fields-reference) section.
- **Full suite:** continue to [Payroll Prerequisites & Settings](../full-suite-payroll-foundations/payroll-prerequisites-settings).
