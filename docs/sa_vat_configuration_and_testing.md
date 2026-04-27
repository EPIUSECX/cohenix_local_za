# SA VAT Configuration and Testing Practitioner Guide

This guide explains how to configure, test, and validate the SA VAT module in ZA Local.

## Purpose And Scope

SA VAT helps practitioners configure South African VAT in ERPNext, prepare VAT201 working papers, review linked VAT transactions, and validate South African tax-invoice readiness.

SA VAT does not replace ERPNext Accounting. Sales Invoices, Purchase Invoices, tax templates, GL Entries, and ERPNext VAT accounts remain the accounting source. ZA Local adds South African setup, classification, working-paper, report, and print-format support.

Direct SARS electronic submission is not supported. The supported process is prepare, review, export, and file manually through SARS eFiling.

## Prerequisites

Before configuring SA VAT:

- ERPNext Accounting is configured.
- A South African company exists.
- The company has a VAT registration number if it is VAT registered.
- The chart of accounts contains VAT output and VAT input accounts.
- Sales and purchase tax templates can be created for the company.
- Items, customers, suppliers, and accounts are configured well enough to post test invoices.
- The practitioner has permission to access Company, Accounts, Tax Templates, Sales Invoice, Purchase Invoice, VAT201 Return, and Reports.

## Required Master Data And Settings

Review or create:

- Company VAT registration number.
- Output VAT account for VAT charged on sales.
- Input VAT account for VAT paid on purchases.
- `South Africa VAT Settings` for each VAT registered company.
- VAT Vendor Type.
- VAT rates.
- Sales Taxes and Charges Templates.
- Purchase Taxes and Charges Templates.
- Item Tax Templates where used.
- Item VAT categories.
- VAT201 classification mappings.

## Configuration Tutorial

### 1. Configure Company VAT Details

1. Open `Company`.
2. Select the South African company.
3. Confirm the country and company abbreviation.
4. Capture the VAT registration number.
5. Save.

Validation:

- The VAT number appears on South African sales print formats where applicable.
- The same company is used for VAT settings and VAT201 returns.

### 2. Confirm VAT Accounts

1. Open `Chart of Accounts`.
2. Confirm or create an output VAT account.
3. Confirm or create an input VAT account.
4. Ensure both accounts belong to the same company.
5. Ensure both accounts are appropriate tax/control accounts for VAT reporting.

Validation:

- The accounts can be selected in `South Africa VAT Settings`.
- Posted invoice tax rows use these accounts.

### 3. Create Company VAT Settings

1. Open `South Africa VAT Settings`.
2. Create a record for the company.
3. Set `Company`.
4. Set `VAT Vendor Type`.
5. Set `VAT Filing Frequency`.
6. Set `VAT Filing Day`, normally the due day allocated by SARS.
7. Confirm `Standard VAT Rate` is the current standard VAT rate.
8. Set `Output VAT Account`.
9. Set `Input VAT Account`.
10. Optionally set `Item Tax Template Account` if item tax template automation is required.
11. Save.

Validation:

- `default_vat_report_company` matches `company`.
- VAT rates are present.
- VAT accounts are tracked.
- Saving does not create invalid item tax templates when no valid item tax account is selected.

### 4. Review VAT Rates

Open the VAT Rates table and confirm:

- Standard Rate exists.
- Zero Rate exists.
- Exempt exists.
- Rates match current practitioner-confirmed statutory treatment.

Validation:

- No blank VAT rate rows remain.
- Standard rate is not confused with zero-rated or exempt treatment.

### 5. Review Tax Templates

Open and review:

- `Sales Taxes and Charges Template`
- `Purchase Taxes and Charges Template`
- `Item Tax Template`

Minimum templates to validate:

- Standard-rated sales.
- Zero-rated local sales.
- Export zero-rated sales.
- Exempt sales.
- Standard-rated purchases.
- Capital goods purchases.
- Purchase cases with no deductible VAT.

Validation:

- Template accounts point to the company VAT accounts.
- Template rates match the intended VAT treatment.
- Templates used for VAT201 mapping are selected in `South Africa VAT Settings`.

### 6. Configure Item VAT Categories

Open each test item and set the relevant South African VAT category:

- Standard Rated
- Zero Rated
- Export Zero Rated
- Exempt
- Capital Goods
- Imported Capital Goods
- Imported Other Goods

Validation:

- Item categories support classification.
- Posted tax rows still remain the source of VAT amounts.

## Transaction Workflow

1. Create standard ERPNext Sales Invoices and Purchase Invoices.
2. Use the correct tax template for each transaction.
3. Submit the invoices.
4. Create `VAT201 Return` for the company and period.
5. Click `Get VAT Transactions`.
6. Review every linked transaction row.
7. Resolve any row with `Needs Review`.
8. Review VAT201 totals.
9. Run VAT reports.
10. Export or print working papers for manual filing.

## Desk Test Cases

### Test 1: Company VAT Registration Setup

Steps:

1. Open Company.
2. Enter a valid test VAT registration number.
3. Save.

Expected result:

- Company saves successfully.
- VAT registration number is available for VAT settings and print formats.

### Test 2: Company-Scoped VAT Settings

Steps:

1. Create `South Africa VAT Settings` for Company A.
2. Create a separate record for Company B if available.
3. Save both.

Expected result:

- Each company has its own VAT settings.
- Company A settings do not affect Company B.

### Test 3: VAT Vendor Type And VAT Rates

Steps:

1. Open VAT settings.
2. Select a VAT Vendor Type.
3. Review VAT rates.
4. Save.

Expected result:

- Vendor type is selectable.
- Standard, zero, and exempt rates are visible.
- Filing frequency defaults sensibly where configured.

### Test 4: VAT Account Tracking

Steps:

1. Set output and input VAT accounts.
2. Save VAT settings.
3. Review tracked VAT accounts.

Expected result:

- Actual VAT tax accounts are tracked.
- Non-tax classification accounts are not stored as VAT tax accounts.

### Test 5: Standard-Rated Sales

Steps:

1. Create a Sales Invoice for a standard-rated item.
2. Apply the standard-rated sales tax template.
3. Submit.
4. Fetch transactions into VAT201.

Expected result:

- VAT output is based on the posted tax row.
- The row is classified as standard-rated output.
- VAT201 output tax increases by the posted VAT amount.

### Test 6: Zero-Rated Local Sales

Steps:

1. Create a Sales Invoice for a zero-rated local item.
2. Apply the zero-rated sales template.
3. Submit.
4. Fetch transactions into VAT201.

Expected result:

- The transaction appears as zero-rated local supplies.
- VAT amount is zero.
- It does not inflate standard output VAT.

### Test 7: Export Zero-Rated Sales

Steps:

1. Create a Sales Invoice for an export item.
2. Use export zero-rated treatment.
3. Submit.
4. Fetch transactions into VAT201.

Expected result:

- The row is classified separately from local zero-rated supplies.
- VAT amount is zero.

### Test 8: Exempt Sales

Steps:

1. Create a Sales Invoice for an exempt item.
2. Use exempt treatment.
3. Submit.
4. Fetch transactions into VAT201.

Expected result:

- The row is treated as exempt.
- It does not create VAT output.

### Test 9: Standard-Rated Purchases

Steps:

1. Create a Purchase Invoice with standard input VAT.
2. Submit.
3. Fetch transactions into VAT201.

Expected result:

- Input VAT is based on the posted purchase tax row.
- The row is classified into the mapped input VAT box.

### Test 10: Capital Goods Purchase

Steps:

1. Create a Purchase Invoice for a capital goods item.
2. Apply the capital purchase mapping/template.
3. Submit.
4. Fetch transactions into VAT201.

Expected result:

- Input VAT appears in the capital goods input category.
- It is separated from ordinary local input VAT.

### Test 11: Purchase With No Deductible VAT

Steps:

1. Create a purchase invoice with no posted deductible VAT.
2. Submit.
3. Fetch transactions into VAT201.

Expected result:

- No input VAT is created from assumptions.
- If mapping is unclear, the row is flagged for review rather than silently included.

### Test 12: VAT201 Needs Review Control

Steps:

1. Create a transaction with incomplete mapping.
2. Fetch it into VAT201.
3. Try to finalise the VAT201 return.

Expected result:

- The transaction is visible as `Needs Review`.
- Finalisation is blocked until the row is resolved.

### Test 13: VAT Reports Reconcile

Steps:

1. Open the VAT201 Return.
2. Open `VAT 201 Linked Transactions`.
3. Open `VAT Analysis`.
4. Open ERPNext `VAT Audit Report`.

Expected result:

- Reports show the same source population for the period.
- VAT totals reconcile to the VAT201 working paper.

### Test 14: Tax Invoice Print Formats

Steps:

1. Open a submitted Sales Invoice.
2. Print using `SA Abridged Tax Invoice`.
3. Print using `SA Full Tax Invoice`.
4. Review supplier and customer VAT details.

Expected result:

- Company VAT number appears.
- Customer VAT number appears where required and available.
- Invoice totals, VAT amount, and consideration are readable.
- Print output matches the invoice threshold and document purpose.

### Test 15: Direct SARS Submission Boundary

Steps:

1. Open VAT201 Return.
2. Attempt any SARS submission action if visible.

Expected result:

- Direct electronic SARS submission is blocked or not available.
- Practitioner is guided to manual SARS eFiling using reviewed working papers.

## Reports And Print Formats To Review

Reports:

- VAT 201 Linked Transactions
- VAT 201 Account Classifications
- VAT Analysis
- ERPNext VAT Audit Report
- General Ledger for VAT accounts

Print formats:

- SA Sales Invoice
- SA Full Tax Invoice
- SA Abridged Tax Invoice
- SA Credit Note
- SA Purchase Invoice
- SA Debit Note
- SA Quotation
- SA Sales Order
- SA Delivery Note
- SA Purchase Order
- SA Payment Entry

## Common Mistakes And Troubleshooting

- If VAT201 has no transactions, confirm invoices are submitted and fall inside the VAT period.
- If VAT rows are `Needs Review`, review tax template mappings and item VAT categories.
- If input VAT is too high, check whether non-deductible purchases are incorrectly mapped.
- If tax invoice formats do not show VAT numbers, check Company and Customer VAT fields.
- If ERPNext VAT Audit Report differs, confirm ERPNext VAT account tracking rows are aligned to the company.
- If item tax templates fail to generate, select a valid item tax template account or leave automation disabled intentionally.

## Practitioner Responsibility

The practitioner must validate VAT rates, classifications, invoice requirements, VAT201 totals, and final SARS eFiling values before submission. ZA Local provides working papers and controls; it does not guarantee compliance without review.

