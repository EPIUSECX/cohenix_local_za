# South Africa VAT Configuration and Testing

This guide documents the practitioner setup flow for the `za_local` SA VAT module and the sandbox evidence captured on `development.cohenix`.

## Current SARS Baseline

Use the official SARS references before changing production defaults:

- VAT is currently levied at the standard rate of 15%.
- From 1 April 2026, compulsory VAT registration is R2.3 million and voluntary VAT registration is R120,000.
- VAT201 is a declaration that must be supported by reviewable source records and working papers.
- Tax records must be retained for the statutory record-keeping period.
- Tax invoice treatment is threshold-aware: no tax invoice is required at R50 or less, an abridged tax invoice may be used at R5,000 or less, and a full tax invoice is required above R5,000.

References:

- SARS VAT overview: https://www.sars.gov.za/types-of-tax/value-added-tax/
- SARS VAT rates and thresholds: https://www.sars.gov.za/tax-rates/other-taxes/
- SARS VAT201 guide: https://www.sars.gov.za/guide-to-completing-the-value-added-tax-vat201-return/
- SARS tax invoices: https://www.sars.gov.za/businesses-and-employers/government/tax-invoices/
- SARS record keeping: https://www.sars.gov.za/client-segments/record-keeping/

## ERPNext Integration Model

`za_local` intentionally integrates with ERPNext instead of replacing its accounting model.

- `South Africa VAT Settings` is company-scoped. Create one record per South African company.
- `company` is the authoritative company field. `default_vat_report_company` is compatibility-only and must match `company`.
- `vat_accounts` uses ERPNext's `South Africa VAT Account` child DocType. ERPNext's `VAT Audit Report` reads these rows with `parent = company`.
- Sales and Purchase Invoices remain standard ERPNext documents. VAT201 uses posted tax rows and explicit mappings as evidence.
- Item VAT categories help classification, but they do not replace posted tax evidence for taxable VAT amounts.
- Direct SARS electronic submission is not supported. The supported flow is prepare, review, export, and file manually through SARS eFiling.

## Company Setup Procedure

1. Open the `Company` record and confirm the company is South African.
2. Add the company's 10-digit VAT registration number on the Company record.
3. Confirm the chart of accounts has actual VAT tax accounts, for example:
   - Output VAT: `VAT Collected - Sales - CX`
   - Input VAT: `VAT Paid - Purchases - CX`
4. Open or create `South Africa VAT Settings` for the company.
5. Set:
   - VAT Vendor Type: `Standard`, `Voluntary`, or the practitioner-confirmed category.
   - VAT Filing Frequency: normally `Bi-Monthly` unless SARS allocated another category.
   - VAT Filing Day: integer day of month, normally `25`.
   - Standard VAT Rate: `15`.
   - Output VAT Account: the sales/output VAT tax account.
   - Input VAT Account: the purchase/input VAT tax account.
   - Item Tax Template Account: optional, but if set it must be a valid ERPNext tax/template account for the same company.
6. Save the settings. This seeds VAT vendor types, VAT rates, ERPNext VAT tracking rows, and the default sales/purchase tax templates.
7. Review the VAT201 mapping fields and confirm each template maps to the intended VAT201 box.
8. Configure items with `South Africa VAT Category` where helpful:
   - `Standard Rated`
   - `Zero Rated`
   - `Export Zero Rated`
   - `Exempt`
   - `Capital Goods`
   - `Imported Capital Goods`
   - `Imported Other Goods`

## Transaction Workflow

Use standard ERPNext Selling and Buying documents:

1. Create Sales Invoices with the correct sales tax template:
   - Standard-rated local sales use 15% output VAT.
   - Zero-rated local sales use a zero-rated sales template and zero-rated item category.
   - Export zero-rated sales use the export zero-rated sales template and export item category.
   - Exempt supplies use the exempt sales template and exempt item category.
2. Create Purchase Invoices with the correct purchase tax template:
   - Standard local purchases use 15% input VAT.
   - Capital purchases use the capital input VAT template and capital item category.
   - Purchases without posted deductible VAT must not create input VAT totals.
3. Create a `VAT201 Return` for the company and VAT period.
4. Click `Get VAT Transactions`.
5. Review linked transactions:
   - `Classified` rows are included in VAT201 totals.
   - `Needs Review` rows block finalisation.
   - Rows without deductible VAT evidence must not inflate input tax.
6. Reconcile:
   - `VAT201 Return`
   - `VAT 201 Linked Transactions`
   - `VAT Analysis`
   - ERPNext `VAT Audit Report`
7. Export working papers and file manually on SARS eFiling.

## Sandbox Evidence

The following live staging was run through Docker against site `development.cohenix` using company `Cohenix`.

Configuration staged:

- Company: `Cohenix`
- VAT registration number: `4123456789`
- VAT settings: `Cohenix`
- Output VAT account: `VAT Collected - Sales - CX`
- Input VAT account: `VAT Paid - Purchases - CX`
- Tracked ERPNext VAT accounts: `VAT Collected - Sales - CX`, `VAT Paid - Purchases - CX`
- Period tested: `2026-04-24` to `2026-04-24`
- VAT201 Return: `VAT201-26-04-0002`

Submitted ERPNext documents:

- Standard-rated Sales Invoice: `ACC-SINV-2026-00001`
- Zero-rated local Sales Invoice: `ACC-SINV-2026-00002`
- Export zero-rated Sales Invoice: `ACC-SINV-2026-00003`
- Exempt Sales Invoice: `ACC-SINV-2026-00004`
- Standard-rated Purchase Invoice: `ACC-PINV-2026-00001`
- Capital goods Purchase Invoice: `ACC-PINV-2026-00002`
- Zero-rated Purchase Invoice without deductible VAT: `ACC-PINV-2026-00003`

VAT201 result:

- Linked transaction rows: `6`
- Classified rows: `6`
- Needs Review rows: `0`
- Standard-rated supplies: `R1,000.00`
- Zero-rated supplies: `R1,200.00`
- Exempt supplies: `R300.00`
- Standard-rated output VAT: `R150.00`
- Capital goods input VAT: `R150.00`
- Other goods/services input VAT: `R60.00`
- VAT payable: `R0.00`
- VAT refundable: `R60.00`

Report reconciliation:

- ERPNext `VAT Audit Report` returned rows for the same company and period.
- `VAT 201 Linked Transactions` returned `6` rows.
- `VAT Analysis` returned `6` rows.
- `VAT 201 Linked Transactions` VAT movement total: `R360.00`.
- `VAT Analysis` VAT movement total: `R360.00`.

Control check:

- `submit_to_sars()` is blocked with the expected manual filing message.

## Verification Commands

Run the focused settings and VAT behaviour tests:

```bash
docker exec 8afddd0cf4e4 bash -lc 'cd /workspace/development-bench && bench --site development.cohenix run-tests --app za_local --module za_local.sa_vat.doctype.south_africa_vat_settings.test_south_africa_vat_settings'
```

Expected result:

```text
Ran 20 tests
OK
```

Run a report consistency check for the staged VAT201 return:

```bash
docker exec 8afddd0cf4e4 bash -lc 'cd /workspace/development-bench && env/bin/python - <<'"'"'PY'"'"'
import frappe
from frappe.utils import flt

frappe.init(site="development.cohenix", sites_path="/workspace/development-bench/sites")
frappe.connect()

from za_local.sa_vat.report.vat_201_linked_transactions.vat_201_linked_transactions import execute as linked_execute
from za_local.sa_vat.report.vat_analysis.vat_analysis import execute as analysis_execute

vat_return = "VAT201-26-04-0002"
_, linked = linked_execute({"vat_return": vat_return})
_, analysis = analysis_execute({"vat_return": vat_return})

print({
    "vat_return": vat_return,
    "linked_rows": len(linked),
    "analysis_rows": len(analysis),
    "linked_tax_total": flt(sum(flt(row.tax_amount) for row in linked)),
    "analysis_tax_total": flt(sum(flt(row.vat_amount) for row in analysis)),
    "needs_review_rows": len([row for row in linked if row.classification_status == "Needs Review"]),
})

frappe.destroy()
PY'
```

Expected result includes:

```text
"linked_rows": 6
"analysis_rows": 6
"linked_tax_total": 360.0
"analysis_tax_total": 360.0
"needs_review_rows": 0
```

## Practitioner Acceptance Criteria

A company is ready for SA VAT processing when:

- The company has a VAT registration number.
- `South Africa VAT Settings` exists for that company.
- Output and input VAT accounts are real ERPNext Tax accounts.
- ERPNext `South Africa VAT Account` child rows contain the VAT accounts used on posted tax rows.
- VAT201 mapping fields point to the company's actual sales and purchase tax templates.
- Standard, zero-rated, export, exempt, capital, and non-capital purchase scenarios classify correctly.
- `Needs Review` rows are resolved before finalising the VAT201 working paper.
- The VAT201 return, linked transactions, VAT analysis, and ERPNext VAT Audit Report can be reconciled.
- SARS filing is handled manually from reviewed working papers and exports.
