# SA Print Formats & Tax Invoices

`za_local` ships SARS-compliant print formats for the common sales and purchase documents. They are installed automatically and available in the **Print** view of each document.

## Available formats

| Print Format | Document | Use |
|---|---|---|
| SA Full Tax Invoice | Sales Invoice | Full tax invoice (recipient name, address, VAT number) — required above the prescribed threshold. |
| SA Abridged Tax Invoice | Sales Invoice | Abridged tax invoice — allowed below the prescribed threshold. |
| SA Sales Invoice | Sales Invoice | General SA sales invoice layout. |
| SA Credit Note | Sales Invoice (return) | Credit note. |
| SA Debit Note | Purchase Invoice (debit) | Debit note. |
| SA Quotation | Quotation | SA-formatted quotation. |
| SA Sales Order | Sales Order | SA-formatted sales order. |
| SA Delivery Note | Delivery Note | SA-formatted delivery note. |
| SA Purchase Invoice | Purchase Invoice | SA-formatted purchase invoice. |
| SA Purchase Order | Purchase Order | SA-formatted purchase order. |
| SA Payment Entry | Payment Entry | SA-formatted remittance/receipt. |

With HRMS you also get **SA Salary Slip**, **IRP5 Employee Certificate** and **IRP5-it3 Certificate** (covered in the payroll sections).

## Choosing full vs abridged tax invoice

- Use **SA Full Tax Invoice** when the consideration exceeds the prescribed full-tax-invoice threshold, or whenever the customer is a registered VAT vendor who needs to claim input tax. It shows the recipient's name, address and VAT number (captured per [Customer & Supplier VAT Fields](customer-supplier-vat)).
- Use **SA Abridged Tax Invoice** for smaller supplies below the threshold.

## Setting a default print format

To make a format the default for a document type:

1. Open **Print Format** and the relevant SA format, or
2. Go to the DocType's **Print Settings** / customise the form and set the **Default Print Format**.

You can also set the **Default Letter Head** on the Company so the letterhead appears consistently.

## Verifying output

Raise a test Sales Invoice with a standard-rated item, open **Print**, choose **SA Full Tax Invoice**, and confirm:

- The words "Tax Invoice" appear.
- The supplier's name, address and VAT number show.
- The recipient's details show (for a full tax invoice).
- VAT is shown separately at 15% with the VAT amount and the VAT-inclusive total.

## Next

Move on to the [VAT201 Return Workflow & Reports](vat201-return) to prepare your periodic VAT submission.
