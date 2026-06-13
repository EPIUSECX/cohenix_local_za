# Overview & Architecture

`za_local` (app title **SA Localisation**, published by Cohenix) is a comprehensive South African localisation for ERPNext. It adds the statutory configuration, calculations, documents and reports a South African business needs: VAT, PAYE/UIF/SDL/ETI payroll, COIDA, and labour-law reporting.

This guide takes a new practitioner from an empty site through to committing payroll and filing statutory returns. It is written for two audiences:

- **ERPNext-only practitioners** who use the app for VAT compliance and South African document templates (tax invoices, credit notes, etc.) without payroll.
- **Full-suite practitioners** who also run South African payroll on Frappe HR (HRMS).

Read [Choosing Your Track](choosing-your-track) to decide which path applies to you.

## The modules

The app is organised into six Frappe modules, each with its own workspace:

| Module | Workspace | Purpose | Needs HRMS? |
|---|---|---|---|
| SA Setup | SA Overview | Install, guided setup, navigation, custom fields | No |
| SA VAT | SA VAT | VAT settings, rates, VAT201 return, VAT reports, tax-invoice print formats | No |
| SA Payroll | SA Payroll | PAYE/UIF/SDL/ETI, salary slip, EMP201, EMP501, IRP5 | **Yes** |
| SA Labour | SA Labour | SETA, bargaining councils, skills (WSP/ATR), Employment Equity, business trips | No |
| SA COIDA | SA COIDA | COIDA settings, workplace injuries, OID claims, annual return | No |

## How it plugs into ERPNext

`za_local` does not replace ERPNext or HRMS, it extends them:

- **Custom fields** are added to standard DocTypes (Company, Customer, Item, Employee, Salary Component, Payroll Settings, Address, and others). These are applied automatically on install and migrate. See the [Custom Fields Reference](../reference-operations/custom-fields-reference).
- **Controller extensions** add SA VAT logic to Sales Invoice and Purchase Invoice (always active).
- **Controller overrides** add SA payroll logic to Salary Slip, Payroll Entry, Additional Salary, Leave Application, Employee Separation and Salary Structure Assignment. **These register only when HRMS is installed** (`za_local.utils.hrms_detection`).
- **Document events** protect the SARS audit trail by preventing deletion of posted sales/purchase documents and validating SA VAT numbers on Customer.
- **Print formats** provide SARS-compliant tax invoices and certificates.
- **A date-effective statutory rate engine** (`za_local.utils.statutory_rates`) resolves PAYE brackets, rebates, medical credits, UIF, SDL, ETI, travel, retirement and lump-sum values for the payroll date, instead of hard-coding rates. See [Statutory Rate Data](../full-suite-payroll-foundations/statutory-rate-data).

## The South African tax year

The SA tax year runs **1 March to the last day of February**. The "year of assessment" is the calendar year in which it ends, so the **2026-2027** tax year (1 March 2026 to 28 February 2027) has year of assessment **2027**. Statutory rate files in the app are suffixed with the year of assessment (e.g. `statutory_rates_2027.json`). Keep this in mind whenever you create a Fiscal Year, Payroll Period or Income Tax Slab.

## What to read next

1. [Prerequisites & Installation](prerequisites-installation)
2. [Choosing Your Track](choosing-your-track)
3. [Post-Install Verification](post-install-verification)
4. Then either the **ERPNext-Only Track** (VAT) or the **Full Suite** (payroll) sections.
