# ZA Local

South African localization for ERPNext, with optional HRMS payroll support.

`za_local` is the single South African localization app for this bench. It provides South African setup, VAT201 working papers, payroll statutory processing, labour records, COIDA workflows, print formats, workspaces, onboarding, and setup/help surfaces.

## Current Scope

- `SA Overview`: administrator landing page, setup checklist, help, and cross-module navigation.
- `SA VAT`: company-scoped VAT settings, VAT201 working-paper flow, tax-invoice readiness, ERPNext VAT Account integration, and VAT reports.
- `SA Payroll`: HRMS payroll extensions for PAYE, UIF, SDL, ETI, company contributions, EMP201, EMP501, IRP5/IT3(a), and payroll reports.
- `SA Labour`: SETA, bargaining council, sectoral wage, skills planning, training, and employment-equity reporting support.
- `SA COIDA`: COIDA settings, industry rates, annual returns, workplace injuries, and OID claims.

HRMS is optional for the app, but payroll features require HRMS. Without HRMS, accounting, VAT, setup, print-format, workspace, labour, and COIDA features remain available.

## Supported Stack

- Frappe Framework v15/v16
- ERPNext v15/v16
- HRMS v15/v16 for payroll features
- Python 3.10+

## Installation

```bash
cd /path/to/bench
bench get-app https://github.com/your-org/za_local.git
bench --site your-site.local install-app za_local
bench --site your-site.local migrate
bench restart
```

## Setup Model

ZA Local assumes a South-Africa-first site. The setup wizard and `ZA Local Setup` can load South African defaults, custom fields, workspaces, statutory payroll data, VAT setup helpers, print formats, and module onboarding.

For existing sites:

1. Open `ZA Local Setup`.
2. Select the company.
3. Load the required setup sections.
4. Open `SA Overview` and follow the module onboarding cards.
5. Verify each module-specific settings record before processing statutory work.

## SA VAT

SA VAT is company-scoped and integrates with ERPNext accounting rather than replacing it.

- `South Africa VAT Settings` is one document per company.
- `company` is the authoritative company field.
- ERPNext's `South Africa VAT Account` child DocType is used for tracked VAT accounts.
- VAT201 totals come from posted tax evidence and linked `VAT201 Return Transaction` rows.
- Unclassified or ambiguous rows are kept visible for practitioner review.
- `VAT 201 Linked Transactions`, `VAT 201 Account Classifications`, `VAT Analysis`, and ERPNext `VAT Audit Report` are the review surfaces.
- Tax-invoice readiness distinguishes no-tax-invoice, abridged invoice, and full tax invoice thresholds.
- Direct SARS electronic submission is not supported; the supported posture is prepare, review, export, and file manually through SARS eFiling.

Available SA VAT reports:

- `VAT 201 Linked Transactions`
- `VAT 201 Account Classifications`
- `VAT Analysis`
- ERPNext `VAT Audit Report`

Detailed VAT setup and sandbox evidence are documented in [`docs/sa_vat_configuration_and_testing.md`](docs/sa_vat_configuration_and_testing.md).

## SA Payroll

SA Payroll extends HRMS payroll with South African statutory behaviour.

- Salary Slip override calculates PAYE using HRMS income tax slabs plus SA rebates and medical tax credits.
- UIF employee and employer contributions are formula-driven and capped at the configured monthly limit.
- SDL is handled as an employer company contribution.
- Retirement-fund deductions are treated as pre-tax and capped using the South African annual retirement contribution limit.
- Medical aid tax credits support main-member-only and dependant scenarios through Employee Private Benefit records.
- ETI eligibility and monthly ETI are calculated from employee age, joining date, SA ID, hours, remuneration, and ETI slabs.
- Salary Structure supports company contribution rows for UIF employer, SDL, employer retirement fund contributions, and employer medical aid contributions.
- EMP201 fetches submitted Salary Slip values, including ETI, PAYE, UIF, and SDL.
- Payroll Register uses SARS code mappings so current ZA component names and legacy names both report correctly.
- Payroll Entry creates GL for submitted Salary Slips; employer UIF and SDL company contributions debit expense accounts and credit Payroll Payable.

Current seeded payroll data includes:

- Statutory components: `PAYE`, `UIF Employee Contribution`, `UIF Employer Contribution`, `SDL Contribution`.
- Earnings components: `Basic Salary`, `Housing Allowance`, `Transport Allowance`, `13th Cheque`, `Performance Bonus`, `Overtime`, `Commission`.
- SARS payroll code mappings for common IRP5/EMP201 codes.
- Income Tax Slabs and `Tax Rebates and Medical Tax Credit` rows for the supported tax years.

Available SA Payroll reports:

- ZA reports: `Payroll Register`, `EMP201 Report`, `Department Cost Analysis`, `Statutory Submissions Summary`, `Retirement Fund Deductions`
- HRMS payroll reports exposed in the ZA workspace: `Salary Register`, `Bank Remittance`, `Salary Payments Based On Payment Mode`, `Salary Payments via ECS`, `Income Tax Deductions`, `Income Tax Computation`
- Accounting reports exposed in the ZA Payroll workspace: `General Ledger`, `Accounts Payable`, `Accounts Receivable`

India-specific HRMS reports such as `Provident Fund Deductions` and `Professional Tax Deductions` are not exposed in ZA Payroll. ZA Local provides `Retirement Fund Deductions` for South African pension/provident/retirement-annuity deduction review instead.

Detailed payroll setup and sandbox payslip/EMP201 evidence are documented in [`docs/sa_payroll_configuration_and_testing.md`](docs/sa_payroll_configuration_and_testing.md).

## SA Labour

SA Labour provides practitioner working papers and reports for South African labour administration.

- SETA and Bargaining Council masters support skills and sector administration.
- Sectoral Minimum Wage rows provide configurable wage-rate references; practitioners must keep statutory and bargaining-council rates current.
- Business Trip Settings, Regions, and Business Trips calculate daily allowances, incidentals, private-car mileage, receipts, accommodation, and other expenses.
- Workplace Skills Plan and Annual Training Report records summarize planned and completed training spend.
- Skills Development Records track employee-level training and B-BBEE skills-development support values.
- Employment Equity reports use Employee custom fields for race, disability, gender, and occupational level.
- WSP, ATR, and EE outputs are supporting records/reports; direct SETA or Department of Employment and Labour submission is not automated.

Available SA Labour reports:

- `Ee Workforce Profile`
- `Eea2 Income Differentials`
- `Eea4 Employment Equity Plan`

Detailed labour setup and sandbox evidence are documented in [`docs/sa_labour_configuration_and_testing.md`](docs/sa_labour_configuration_and_testing.md).

## SA COIDA

SA COIDA supports Compensation Fund setup, annual return working papers, workplace injuries, and OID claims.

- COIDA Settings stores the registration number, reference number, assessment year, submission deadline, and industry assessment rates.
- COIDA Annual Return fetches submitted Salary Slip data for the 1 March to end-February assessment period and calculates the assessment fee from earnings and the configured rate.
- Workplace Injury records support injury details, medical attention, leave linkage where HRMS leave is available, and OID claim creation.
- OID Claims track claim date, claim status, medical reports, compensation amount, and payment date after submission.
- Direct Compensation Fund/eCOID submission is not automated; the supported posture is prepare, review, and manually file.
- SA COIDA currently uses working-paper DocTypes rather than script reports: `COIDA Annual Return`, `Workplace Injury`, and `OID Claim`.

Detailed COIDA setup and sandbox evidence are documented in [`docs/sa_coida_configuration_and_testing.md`](docs/sa_coida_configuration_and_testing.md).

## Accounting and Financial Reports

The sandbox company `Cohenix` has posted ERPNext accounting data for VAT and payroll testing:

- Sales Invoices and Purchase Invoices post balanced GL entries for the SA VAT test set.
- Payroll Entry `HR-PRUN-2026-00002` posts April 2026 Salary Slip accruals to `ACC-JV-2026-00003`.
- Employer UIF and SDL company contributions post through `ACC-JV-2026-00004`.
- The April 2026 GL test balances `Journal Entry`, `Sales Invoice`, and `Purchase Invoice` voucher totals.

Core financial reports verified against the staged data:

- `General Ledger`
- `Trial Balance`
- `Profit and Loss Statement`
- `Balance Sheet`
- `Accounts Receivable`
- `Accounts Payable`

## Workspaces and Onboarding

Each primary module has its own workspace sidebar and module onboarding card:

- `SA Overview Onboarding`
- `SA VAT Onboarding`
- `SA Payroll Onboarding`
- `SA Labour Onboarding`
- `SA COIDA Onboarding`

The onboarding sequence is practitioner-first: configure company/settings records, review masters, create statutory returns/submissions, review reports, and then export/file manually where required.

## Development and Verification

Run migrations:

```bash
bench --site your-site.local migrate
```

Run all app tests:

```bash
bench --site your-site.local run-tests --app za_local
```

Useful focused checks:

```bash
bench --site your-site.local execute za_local.test_data_loading.run_all_tests
bench --site your-site.local run-tests --app za_local --module za_local.sa_vat.doctype.south_africa_vat_settings.test_south_africa_vat_settings
```

The final sandbox report sweep on `development.cohenix` verified 24 reports with 0 failures, including SA VAT, SA Payroll, SA Labour, HRMS payroll reports exposed in the ZA workspace, and ERPNext accounting/financial reports.

## Important Boundaries

- ZA Local prepares South African VAT and payroll working papers; it does not claim direct SARS electronic filing unless a real integration is added.
- Payroll calculations depend on correct HRMS company, holiday list, salary component account, payroll period, income tax slab, and salary structure setup.
- VAT201 depends on posted ERPNext tax rows and explicit VAT201 mappings; item categories are classification aids, not substitutes for tax evidence.
- Labour WSP, ATR, and Employment Equity reports are supporting records and report surfaces; statutory portal submission remains manual.
- COIDA Annual Return and OID Claim records are working papers and tracking records; Compensation Fund/eCOID submission remains manual.
- Always confirm SARS rates before changing statutory fixtures.

## License

MIT, unless otherwise specified by the project owner.
