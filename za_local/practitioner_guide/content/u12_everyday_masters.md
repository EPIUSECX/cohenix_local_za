# Everyday Masters: Customers, Suppliers, Items, Employees

These are the records you create and maintain as part of normal work. Getting the South African fields right here means your invoices, VAT201 and payroll come out correct without rework.

## Customers

When creating a **Customer**, complete the SA fields:

- **Is VAT Vendor** — tick if the customer is VAT-registered. This guides whether you issue a full tax invoice.
- **Company Registration** — their CIPC number.
- **Tax ID / VAT number** — their SARS VAT number.

The system validates the VAT number format on save, so a typo is caught early. A customer's VAT details are what allow you to issue a **full tax invoice** (see [Tax Invoices, Credit & Debit Notes](../working-with-vat/tax-invoices-credit-notes)).

## Suppliers

Capture each **Supplier**'s **VAT number** and address. Accurate supplier VAT numbers support your input-tax claims. If a supplier is not VAT-registered, use a zero/non-deductible tax template on their purchases so you don't overclaim input VAT.

## Items

On each **Item**, set the **VAT category** (standard rated, zero rated, exempt, capital goods, imported, etc.). This drives:

- the VAT applied on invoices, and
- the classification on the VAT201 return.

On **Item Group**, the **Is Capital Goods** flag marks groups whose purchases are capital input on the VAT201 — set it for asset/equipment groups.

> Keep item VAT categories accurate. Most "needs review" rows on the VAT201 come from items with a missing or wrong category.

## Employees (Frappe HR)

When you add or maintain an **Employee**, the South African sections matter for payroll and certificates. The essentials:

- **ID Number** (13-digit SA ID) and **Income Tax Reference Number**.
- **Hours per Month** (for ETI) and **Number of Dependants** (for the medical tax credit).
- **Residential and Postal Address** (required on the IRP5).
- **Bank account details** for electronic payment.
- For Employment Equity reporting: **Race**, **Occupational Level**, **Is Disabled**.

A fuller field-by-field walkthrough is in the practitioner guide → [Employee Master & SA Details](/sa-guide/full-suite-employees/employee-master). Capture these when you onboard someone; back-filling later is tedious and holds up year-end certificates.

## Next

Start transacting: [Create a Sales Invoice with VAT](../working-with-vat/sales-invoice-vat).
