# SA Overview and Setup Practitioner Guide

This guide explains how to configure the ZA Local app before working in the VAT, Payroll, Labour, or COIDA modules.

## Purpose And Scope

SA Overview is the administrator landing page for South African localisation. It helps a practitioner or implementer confirm that the app is installed, South African defaults are loaded, module workspaces are visible, and each statutory area has a clear next step.

Use this guide before configuring any individual module.

## Prerequisites

Before starting:

- ERPNext is installed and the site is accessible through Desk.
- HRMS is installed if payroll execution is required.
- At least one South African company exists.
- The company's chart of accounts has the accounts required for VAT, payroll liabilities, payroll expenses, and statutory clearing accounts.
- The current fiscal year and payroll period exist where payroll will be used.
- The practitioner has System Manager, Accounts Manager, HR Manager, Payroll Manager, or equivalent permissions.

## Initial Setup Tutorial

1. Open Desk.
2. Search for `ZA Local Setup`.
3. Create or open the setup record for the company.
4. Select the South African company.
5. Review the available setup sections.
6. Apply the setup sections required for the site:
   - Workspaces and sidebar navigation.
   - Custom fields.
   - VAT defaults.
   - Payroll defaults, if HRMS is installed.
   - Labour and COIDA defaults.
   - Print formats.
   - Module onboarding.
7. Save the setup record.
8. Open the `SA Overview` workspace.
9. Confirm the module cards are visible:
   - SA VAT
   - SA Payroll
   - SA Labour
   - SA COIDA
10. Confirm the `Getting Started` onboarding card is visible where onboarding has not been completed.

## App-Wide Configuration Checks

### Company

Open the Company record and confirm:

- Company name and abbreviation are correct.
- Country is South Africa where applicable.
- Default currency is correct.
- VAT registration number is captured if the company is VAT registered.
- PAYE, UIF, SDL, and COIDA reference numbers are captured if payroll and COIDA are used.
- Default receivable, payable, expense, liability, and payroll accounts are configured.

### Users And Roles

Confirm the right users have access:

- Accounts users can access VAT settings, VAT201 returns, tax templates, and accounting reports.
- Payroll users can access HRMS payroll records, SA Payroll settings, EMP201, EMP501, and IRP5 / IT3(a).
- HR users can access Employee records, Employment Equity fields, Labour records, and COIDA incident records.
- System administrators can access setup, custom fields, and print formats.

### Workspaces

Open each workspace:

- SA Overview
- SA VAT
- SA Payroll
- SA Labour
- SA COIDA

For each workspace, confirm:

- The sidebar opens.
- The module onboarding card appears where applicable.
- Links open the intended DocType, Report, or Workspace.
- No module exposes unrelated country-specific reports.

### Print Formats

Open `Print Format` and confirm the expected South African formats are enabled:

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
- SA Salary Slip
- IRP5 Employee Certificate
- IRP5-it3 Certificate

## Desk Test Cases

### Test 1: Setup Record Opens And Saves

Steps:

1. Open `ZA Local Setup`.
2. Select a company.
3. Review the setup status.
4. Save the record.

Expected result:

- The record saves without error.
- Setup status remains a system-controlled status field.
- No unexpected script errors appear.

### Test 2: Workspaces Are Available

Steps:

1. Open the app switcher or workspace sidebar.
2. Open each ZA Local workspace.

Expected result:

- SA Overview, SA VAT, SA Payroll, SA Labour, and SA COIDA are available.
- Each workspace contains relevant module links.
- Payroll workspace is useful only where HRMS is installed.

### Test 3: Module Onboarding Appears

Steps:

1. Open each module workspace.
2. Review the `Getting Started` card.
3. Click one onboarding step.

Expected result:

- The onboarding card appears.
- Steps follow the practitioner workflow: settings first, transactions next, reports last.
- Clicked steps route to the intended list, form, or report.

### Test 4: Custom Fields Are Visible

Steps:

1. Open Company.
2. Open Employee.
3. Open Salary Component if HRMS is installed.
4. Open Item.

Expected result:

- Company has South African statutory reference fields.
- Employee has South African identity, tax, Employment Equity, and IRP5 source fields.
- Salary Component has SARS payroll code fields where HRMS is installed.
- Item has VAT category fields used by SA VAT.

### Test 5: Print Formats Are Selectable

Steps:

1. Open a compatible document such as Sales Invoice, Purchase Invoice, Salary Slip, or IRP5 Certificate.
2. Open the print view.
3. Select the relevant South African print format.

Expected result:

- The format appears in the print format selector.
- The preview renders without template errors.
- South African fields show where the source document has values.

## Troubleshooting

- If a workspace is missing, run migration and confirm the app is installed on the site.
- If onboarding is missing, check the `Workspace Sidebar` record for the relevant module.
- If payroll links fail, confirm HRMS is installed.
- If print formats do not appear, confirm the Print Format records are enabled and linked to the correct DocType.
- If custom fields are missing, rerun ZA Local setup or migration and confirm customizations synced successfully.

## Practitioner Responsibility

The setup process creates a starting point. Practitioners must still review every statutory setting, account, tax rate, salary component, and report before live use.

