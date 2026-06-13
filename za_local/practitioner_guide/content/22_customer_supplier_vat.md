# Customer & Supplier VAT Fields

`za_local` adds South African VAT fields to the Customer master and validates VAT numbers so your tax invoices and VAT201 are accurate.

## Customer VAT fields

On each **Customer**, complete the `za_local` fields:

| Field | Notes |
|---|---|
| Is VAT Vendor | Tick if the customer is a registered VAT vendor. Drives whether a full tax invoice (with their VAT number) is appropriate. |
| Company Registration | The customer's CIPC company registration number. |
| Tax ID (VAT number) | The customer's SARS VAT number, captured on the standard Tax ID field / address. |

When you save a Customer, `za_local`'s validation checks the South African VAT number format. A malformed VAT number is flagged so it is corrected before it lands on a tax invoice.

> **Full tax invoice vs abridged:** South African VAT rules require a *full* tax invoice (showing the recipient's name, address and VAT number) above the prescribed threshold, and allow an *abridged* tax invoice below it. Capturing the customer's VAT details lets you issue the correct format — see [SA Print Formats](print-formats).

## Supplier details

Capture each **Supplier**'s VAT number (Tax ID) and address. Accurate supplier VAT numbers support your input-tax claims and keep purchase documents audit-ready. Where a supplier is not VAT-registered, ensure purchases use a zero/non-deductible tax template so input tax is not overclaimed.

## Audit-trail protection

To preserve the SARS audit trail, `za_local` prevents deletion of posted sales and purchase documents (Quotation, Sales Order, Sales Invoice, Request for Quotation, Supplier Quotation, Purchase Order, Purchase Receipt, Purchase Invoice). Cancel and amend rather than delete. This is intentional and applies in both tracks.

## Next

Set up [SA Print Formats & Tax Invoices](print-formats).
