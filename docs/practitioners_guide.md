# ZA Local Practitioner Guide

This guide is the starting point for payroll, VAT, accounting, HR, labour, and compliance practitioners who need to configure and validate the `za_local` South African localisation app in ERPNext, Frappe, and HRMS.

The documentation is written for Desk users. It focuses on configuration, operational workflow, practical validation, and review evidence. Developer commands are intentionally kept out of the practitioner flow unless they are needed in the project README.

## How To Use This Guide

1. Start with the app-wide setup guide.
2. Configure one module at a time.
3. Complete the Desk test cases for the module before using it for live statutory work.
4. Keep screenshots or exported reports as review evidence.
5. Ask a qualified practitioner to validate statutory rates, calculations, and final submissions before filing.

Recommended reading order:

1. [SA Overview and Setup Practitioner Guide](sa_overview_setup_practitioner_guide.md)
2. [SA VAT Configuration and Testing](sa_vat_configuration_and_testing.md)
3. [SA Payroll Configuration and Testing](sa_payroll_configuration_and_testing.md)
4. [SA Labour Configuration and Testing](sa_labour_configuration_and_testing.md)
5. [SA COIDA Configuration and Testing](sa_coida_configuration_and_testing.md)

## Module Map

| Module | Main Purpose | HRMS Required |
| --- | --- | --- |
| SA Overview | Initial setup, onboarding, navigation, and cross-module readiness checks | No |
| SA VAT | VAT settings, VAT201 working papers, tax-invoice readiness, and VAT reports | No |
| SA Payroll | PAYE, UIF, SDL, ETI, Salary Slip calculations, EMP201, EMP501, IRP5 / IT3(a), and payroll reports | Yes |
| SA Labour | SETA, bargaining council, sectoral wage references, business trips, WSP, ATR, skills records, and Employment Equity reports | Partially |
| SA COIDA | COIDA settings, industry rates, annual return working papers, workplace injuries, and OID claims | Partially |

## Minimum Implementation Sequence

Use this sequence for a new South African company:

1. Confirm ERPNext company details, chart of accounts, fiscal year, currencies, and users.
2. Install HRMS if payroll execution is required.
3. Run `ZA Local Setup` for the company.
4. Complete the SA Overview setup checks.
5. Configure SA VAT for the company and test VAT invoices before live VAT201 use.
6. Configure SA Payroll only after HRMS payroll master data is ready.
7. Configure SA Labour reference data before using WSP, ATR, business trips, or Employment Equity reports.
8. Configure SA COIDA before preparing the annual return or recording workplace injuries.
9. Run each module's Desk test cases.
10. Save test evidence and practitioner sign-off before using the app for production submissions.

## Validation Standard

A module should be considered ready only when:

- Required settings and master data have been reviewed.
- At least one positive test case has passed.
- At least one exception or review-control test case has passed.
- Reports agree with the source documents they are based on.
- Print formats render with the required South African details where applicable.
- The practitioner understands which activities remain manual filing or external portal work.

## App-Wide Compliance Boundary

ZA Local provides configuration, calculation support, working papers, reports, print formats, and workflow guidance. It does not replace professional statutory review.

Cohenix, EPI-USE, contributors, and implementers do not accept responsibility for incorrect calculations, incorrect setup, incorrect statutory interpretation, or missed submissions. The employer, payroll practitioner, tax practitioner, and appointed reviewers remain responsible for validating all calculations, statutory rates, return values, exports, and filings before submission to SARS, the Compensation Fund, SETAs, the Department of Employment and Labour, or any other authority.

