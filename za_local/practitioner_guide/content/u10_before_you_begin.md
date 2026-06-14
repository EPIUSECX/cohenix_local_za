# Before You Begin: What Must Be Set Up

Before you capture transactions or run payroll, a few things must already be configured. This page is a **checklist you can run through** — if something is missing, ask whoever set up the system (or follow the linked practitioner pages).

## Always required

- [ ] **Company created** with country South Africa and the SA registration fields completed (VAT number if registered). → [practitioner: Company & SA Registration](/sa-guide/foundation-setup-both-tracks/company-registration)
- [ ] **Chart of Accounts** loaded, including VAT Output and VAT Input accounts. → [practitioner: Chart of Accounts](/sa-guide/foundation-setup-both-tracks/chart-of-accounts)
- [ ] **A March–February Fiscal Year** exists. → [practitioner: ZA Local Setup & Fiscal Year](/sa-guide/foundation-setup-both-tracks/za-local-setup)

## Required for VAT

- [ ] **South Africa VAT Settings** exist for your company, with output/input VAT accounts and the standard rate (15%). → [practitioner: South Africa VAT Settings](/sa-guide/erpnext-only-track-vat-documents/vat-settings)
- [ ] **Tax templates** for standard, zero-rated and exempt supplies are available to pick on invoices. → [practitioner: Tax Templates & Item VAT Categories](/sa-guide/erpnext-only-track-vat-documents/tax-templates-item-categories)
- [ ] **Items** carry the right VAT category (standard / zero-rated / exempt / capital).

## Required for payroll (Frappe HR)

- [ ] Company **PAYE, UIF and SDL reference numbers** captured.
- [ ] **Payroll Settings** map the statutory components (PAYE, UIF, SDL). → [practitioner: Payroll Prerequisites & Settings](/sa-guide/full-suite-payroll-foundations/payroll-prerequisites-settings)
- [ ] **Statutory rates** loaded for the current tax year (tax slab, rebates, medical credits, ETI). → [practitioner: Statutory Rate Data](/sa-guide/full-suite-payroll-foundations/statutory-rate-data)
- [ ] **Salary Components** and at least one **Salary Structure** exist.
- [ ] A **Payroll Period** and a **Holiday List** for the year exist.
- [ ] Employees have a **submitted Salary Structure Assignment** with the correct Income Tax Slab.

## If something is missing

Most of this is one-time setup. The quickest path is to open **ZA Local Setup** (SA Overview workspace) — it can load the chart of accounts, statutory rates and master data for your company in one step. → [practitioner: ZA Local Setup](/sa-guide/foundation-setup-both-tracks/za-local-setup)

## Next

Confirm the live settings on your company: [Confirm Company, VAT & Payroll Settings](confirm-company-settings).
