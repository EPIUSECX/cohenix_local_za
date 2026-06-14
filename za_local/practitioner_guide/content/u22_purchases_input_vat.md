# Purchase Invoices & Input VAT

**Goal:** capture supplier invoices so input VAT is claimed correctly and flows into the VAT201 return.

## Steps

1. **New Purchase Invoice.** Search "Purchase Invoice" → **New** (or use the SA VAT workspace).
2. **Supplier.** Pick the supplier. Confirm their VAT number is on file (needed to support the input claim).
3. **Add items / expenses.** Add the lines. Mark capital items via the item / item group (**Is Capital Goods**) so they classify as **capital input** on the VAT201.
4. **Choose the purchase tax template.** Select the matching template — e.g. **SA Standard Rated Purchases 15%**, **SA Capital Purchases 15%**, **SA Capital Imports 15%**, or **SA Other Imports 15%**. For non-VAT or non-deductible purchases, use a 0%/non-deductible template.
5. **Check the input VAT line.** Confirm 15% input VAT posts to the **VAT Input** account for standard purchases.
6. **Save** and **Submit**.

## Getting the classification right

The VAT201 separates input tax into **capital** and **other** goods, and **local** vs **imported**. Picking the correct purchase template (and flagging capital item groups) is what populates those boxes correctly. If you're unsure, check the item's VAT category and the template name.

## Non-VAT and non-deductible purchases

- **Supplier not VAT-registered:** use a 0% template so no input tax is claimed.
- **Non-deductible VAT** (e.g. entertainment, certain motor vehicles): use the appropriate non-deductible treatment so it isn't claimed as input tax.

## After submitting

- The purchase feeds the period's [VAT201 Return](vat201-return) as input tax.
- As with sales, submitted purchase documents **can't be deleted** — cancel/amend or use a debit note to correct.

## Check

- Input VAT posts to the VAT Input account at the right rate.
- Capital purchases are flagged so they land in the capital-input box.
- Supplier VAT number is on file.

## Next

Pull it all together: [Prepare & Review the VAT201 Return](vat201-return).
