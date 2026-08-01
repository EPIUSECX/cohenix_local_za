# Create a Sales Invoice with VAT

**Goal:** raise a sales invoice with reviewed South African VAT treatment and issue the appropriate tax-invoice format.

## Steps

1. **New Sales Invoice.** SA VAT workspace (or search "Sales Invoice") → **New**.
2. **Customer.** Pick the customer and verify recipient/VAT details. The ZAR consideration threshold determines the required full/abridged level; customer details supply the full-invoice particulars.
3. **Add items.** Add each line item and quantity. The Item VAT category assists classification, but the selected posted tax template/rows determine the accounting tax calculation.
4. **Choose the tax template.** In *Taxes and Charges*, select the matching template — e.g. **SA Standard Rated Sales 15%**, **SA Zero Rated Sales 0%**, or an export/exempt template. The default template auto-applies; change it if the supply differs.
5. **Check the VAT line.** Confirm VAT is calculated (15% for standard supplies) and the **grand total** is VAT-inclusive.
6. **Save**, then **Submit** when the invoice is final.

## What the system does for you

The South African invoice logic calculates the VAT and records the **classification** (standard output, zero-rated, exempt, etc.) that the VAT201 return later picks up. You don't classify it again at return time — keeping the item categories and templates correct here is what makes the VAT201 accurate.

## Mixed-rate invoices

If a single invoice has lines at different rates (e.g. some standard, some zero-rated), use **Item Tax Templates** on the affected lines, or split into separate invoices. Keep line-level tax consistent with each item's VAT category to avoid "needs review" rows on the VAT201.

## After submitting

- **Print/issue the tax invoice** — see [Tax Invoices, Credit & Debit Notes](tax-invoices-credit-notes).
- The invoice now feeds the period's [VAT201 Return](vat201-return).
- **Don't delete** a submitted invoice — the system blocks deletion to protect the SARS audit trail. To reverse it, issue a **credit note** (cancel/return), not a delete.

## Check

- VAT amount and rate are correct for the supply.
- Customer and item details are right (they appear on the tax invoice).
- Status is **Submitted**.

## Next

Issue the document: [Tax Invoices, Credit & Debit Notes](tax-invoices-credit-notes).
