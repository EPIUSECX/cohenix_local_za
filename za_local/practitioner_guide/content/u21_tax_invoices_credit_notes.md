# Tax Invoices, Credit & Debit Notes

**Goal:** issue the correct SARS-compliant document for a sale, and handle returns and corrections with credit/debit notes.

## Issuing a tax invoice

1. Open the submitted **Sales Invoice**.
2. Click **Print** (or **Print** → preview).
3. Choose the print format:
   - **SA Full Tax Invoice** — shows the recipient's name, address and VAT number. Use this above the prescribed threshold, or whenever the customer is a VAT vendor who needs to claim input tax.
   - **SA Abridged Tax Invoice** — for smaller supplies below the threshold.
4. Download as PDF or print, and send to the customer.

> The words "Tax Invoice", your VAT number, the customer details (for a full invoice), and VAT shown separately at 15% must all appear. If the customer's VAT number is missing on a full tax invoice, capture it on the [customer master](../first-time-configuration/everyday-masters) and reprint.

## Full vs abridged — which to use

| Use… | When |
|---|---|
| **SA Full Tax Invoice** | Consideration above the full-tax-invoice threshold, or customer is a registered VAT vendor. |
| **SA Abridged Tax Invoice** | Smaller supplies below the threshold. |

## Credit notes (sales returns / corrections)

To reverse or reduce a sale, raise a **credit note** rather than deleting the invoice:

1. Open the original Sales Invoice → **Create → Return / Credit Note** (or create a Sales Invoice marked as a return).
2. Confirm the (negative) amounts and VAT.
3. **Submit**, then print using **SA Credit Note**.

The credit note carries negative VAT, which the VAT201 nets off in the period it falls in.

## Debit notes (purchase side)

To adjust a supplier purchase upward (or record a supplier debit), use the purchase **debit note** flow and print **SA Debit Note**. See [Purchase Invoices & Input VAT](purchases-input-vat).

## Why you can't delete documents

Submitted sales and purchase documents **cannot be deleted** — this protects the SARS audit trail. Always **cancel and amend**, or issue a **credit/debit note**, to correct something. This is intentional.

## Next

Capture the buying side: [Purchase Invoices & Input VAT](purchases-input-vat).
