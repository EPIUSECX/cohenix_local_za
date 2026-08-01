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

## Practitioner Guides

Use the practitioner guides for Desk-first configuration, testing, and validation.

- [Practitioner Guide Index](docs/practitioners_guide.md)
- [SA Overview and Setup Practitioner Guide](docs/sa_overview_setup_practitioner_guide.md)
- [SA VAT Configuration and Testing](docs/sa_vat_configuration_and_testing.md)
- [SA Payroll Configuration and Testing](docs/sa_payroll_configuration_and_testing.md)
- [SA Labour Configuration and Testing](docs/sa_labour_configuration_and_testing.md)
- [SA COIDA Configuration and Testing](docs/sa_coida_configuration_and_testing.md)

## Supported Stack

- Frappe Framework v16
- ERPNext v16
- Frappe HR/HRMS v16 for payroll features
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

ZA Local assumes a South-Africa-first site. Installation/migration synchronizes app-owned schema, custom fields, workspaces and print formats. The System-Manager-only `ZA Local Setup` job loads deliberately selected company/master/statutory data sets and may create or refresh app-owned defaults; its completion status is not practitioner signoff.

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
- Direct SARS electronic submission is not supported. VAT201 is an internal working paper: review it against the general ledger and capture the approved figures on SARS eFiling. A generic PDF or CSV exported from ERPNext is not a SARS submission file.

Available SA VAT reports:

- `VAT 201 Linked Transactions`
- `VAT 201 Account Classifications`
- `VAT Analysis`
- ERPNext `VAT Audit Report`

Detailed VAT setup and Desk validation scenarios are documented in [`docs/sa_vat_configuration_and_testing.md`](docs/sa_vat_configuration_and_testing.md).

## SA Payroll

SA Payroll extends HRMS payroll with South African statutory behaviour.

- Salary Slip override calculates PAYE using HRMS income tax slabs plus SA rebates and medical tax credits.
- UIF employee and employer contributions are formula-driven and capped at the configured monthly limit.
- SDL is handled as an employer company contribution.
- Retirement-fund deductions are treated as pre-tax and capped using the South African annual retirement contribution limit.
- Medical scheme tax credits use date-effective `Employee Private Benefit` records with an active private-medical-aid contribution and dependant count.
- Submitted Company Car, Housing and Low Interest Loan benefit records can feed taxable non-cash fringe-benefit earnings into Salary Slips. These values affect PAYE and certificate reporting but not cash net pay.
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

EMP501 and IRP5 / IT3(a) support follows the statutory workflow: monthly EMP201 working papers, certificate preparation, and interim or annual reconciliation. ZA Local does not generate the SARS BRS payroll-import CSV, encrypted reconciliation file, or a direct eFiling/e@syFile submission. Do not upload a generic app CSV to SARS; capture through an approved SARS channel or use a separately validated BRS-compatible integration.

Payroll EFT export is deliberately limited to the implemented and tested **FNB Online Banking Enterprise CSV** format. It is generated from a submitted `Payroll Payment Batch`, is stored as a private file, and requires the batch's source snapshot to remain unchanged. ABSA, Nedbank and Standard Bank exports are not supported until each current bank specification has completed controlled onboarding and acceptance testing.

India-specific HRMS reports such as `Provident Fund Deductions` and `Professional Tax Deductions` are not exposed in ZA Payroll. ZA Local provides `Retirement Fund Deductions` for South African pension/provident/retirement-annuity deduction review instead.

Detailed payroll setup and Desk validation scenarios are documented in [`docs/sa_payroll_configuration_and_testing.md`](docs/sa_payroll_configuration_and_testing.md).

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

Detailed labour setup and Desk validation scenarios are documented in [`docs/sa_labour_configuration_and_testing.md`](docs/sa_labour_configuration_and_testing.md).

## SA COIDA

SA COIDA supports Compensation Fund setup, annual return working papers, workplace injuries, and OID claims.

- `COIDA Settings` is a site-wide settings record. Its industry-rate rows are selected by company and industry class; company registration data remains on the Company master.
- COIDA Annual Return uses a 1 March to end-February assessment year, includes only submitted Salary Slips fully inside the period, applies Salary Component COIDA classifications and the date-effective per-employee earnings cap, and calculates the working-paper assessment from the configured company/class rate.
- Workplace Injury records support injury details, medical attention, leave linkage where HRMS leave is available, and OID claim creation.
- OID Claims track claim date, claim status, medical reports, compensation amount, and payment date after submission.
- Direct Compensation Fund/eCOID submission is not automated; the supported posture is prepare, review, and manually file.
- SA COIDA currently uses working-paper DocTypes rather than script reports: `COIDA Annual Return`, `Workplace Injury`, and `OID Claim`.

Detailed COIDA setup and Desk validation scenarios are documented in [`docs/sa_coida_configuration_and_testing.md`](docs/sa_coida_configuration_and_testing.md).

## Accounting and Financial Reports

ZA Local relies on ERPNext Accounting as the system of record. Practitioners should validate that VAT, payroll, supplier, customer, and statutory postings reconcile to the core ERPNext reports.

Recommended reports to review:

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

Before migration, back up the database and files and rehearse the upgrade on a restored staging copy. Then run the site migration in a maintenance window:

```bash
bench --site your-site.local migrate
bench build --app za_local
bench --site your-site.local clear-cache
```

Run all app tests on a dedicated test site:

```bash
bench --site your-test.local run-tests --app za_local --lightmode
```

Useful focused checks:

```bash
bench --site your-site.local execute za_local.test_data_loading.run_all_tests
bench --site your-site.local run-tests --app za_local --module za_local.sa_vat.doctype.south_africa_vat_settings.test_south_africa_vat_settings
```

Practitioner-facing validation steps are documented in the module guides linked above.

## Important Boundaries

- ZA Local prepares South African VAT and payroll working papers; it does not perform direct SARS electronic filing and its generic exports are not SARS BRS submission files.
- Setup completion, successful migration, and passing automated tests are technical controls, not statutory signoff. A registered tax practitioner/payroll specialist must approve rates, mappings, calculations, submissions and payment totals for the employer's facts.
- Statutory figures are date-effective configuration. Confirm the applicable SARS and Department of Employment and Labour publications before the first payroll/return of each period and before back-dated processing.
- Payroll calculations depend on correct HRMS company, holiday list, salary component account, payroll period, income tax slab, and salary structure setup.
- VAT201 depends on posted ERPNext tax rows and explicit VAT201 mappings; item categories are classification aids, not substitutes for tax evidence.
- Labour WSP, ATR, and Employment Equity reports are supporting records and report surfaces; statutory portal submission remains manual.
- COIDA Annual Return and OID Claim records are working papers and tracking records; Compensation Fund/eCOID submission remains manual.
- Bank files require bank-specific acceptance testing. Only the FNB Online Banking Enterprise CSV implementation is currently enabled; verify a low-value test batch with the bank before production use.
- Cohenix, EPI-USE, contributors, and implementers do not accept responsibility for incorrect calculations, incorrect setup, incorrect statutory interpretation, or missed submissions. Employers and practitioners remain responsible for validating all statutory values before filing.

## License

MIT, unless otherwise specified by the project owner.
