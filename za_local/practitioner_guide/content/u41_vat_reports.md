# VAT Reports

Found in the **SA VAT** workspace. Use these to prepare and check the VAT201 return.

| Report | What it shows | Use it to |
|---|---|---|
| **VAT Analysis** | Output and input VAT by period and rate | See the VAT picture for a period at a glance; spot anomalies. |
| **VAT 201 Linked Transactions** | The individual invoices behind each VAT201 line | Drill from a return figure back to source documents. |
| **VAT 201 Account Classifications** | How each VAT account maps to a VAT201 box | Confirm accounts are classified to the right return field. |

> An **ERPNext VAT Audit Report** is also available as a final accounting cross-check.

## A practical VAT-period workflow

1. Run **VAT Analysis** for the period to see total output and input VAT.
2. Build the [VAT201 Return](../working-with-vat/vat201-return) and clear any review rows.
3. Use **VAT 201 Linked Transactions** to verify a return line by drilling to its invoices.
4. Reconcile the **VAT Payable** figure against your VAT Output and VAT Input ledger balances for the period.
5. Export the support and file on SARS eFiling.

## Reading the numbers

- **Output VAT** is what you charged on sales; **Input VAT** is what you paid on purchases.
- **VAT Payable = Output − Input** (a negative result is a refund).
- Zero-rated and exempt supplies show 0% but are reported separately — that separation matters for the return.

## Next

If you run payroll: [Payroll Reports](payroll-reports). Otherwise: [Exporting & Printing Reports](exporting-printing).
