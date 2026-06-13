# Choosing Your Track

`za_local` supports two deployment shapes. Decide which one you are configuring before you start, because it changes what you install and which sections of this guide you follow.

## Track A — ERPNext-only (VAT & documents)

Choose this if the client uses ERPNext for accounting, sales and purchasing, and needs South African **VAT compliance** and **SARS-compliant document templates**, but runs payroll elsewhere (or not at all).

You get:

- South Africa VAT Settings, VAT rates and vendor types
- Standard-rated, zero-rated, exempt and capital-goods VAT handling
- SA tax-invoice, credit-note, debit-note and order/delivery print formats
- The VAT201 Return working paper with transaction classification and review
- VAT analysis and reconciliation reports

You do **not** install HRMS. Follow:

1. [Foundation Setup](../foundation-setup-both-tracks/company-registration) (Company, Chart of Accounts, ZA Local Setup)
2. The entire **ERPNext-Only Track: VAT & Documents** section.

## Track B — Full suite (VAT + payroll)

Choose this if the client also runs **South African payroll** on Frappe HR. This includes everything in Track A plus PAYE/UIF/SDL/ETI, salary slips, EMP201, IRP5 certificates, EMP501 reconciliation, and optionally COIDA and labour reporting.

You install **HRMS**. Follow:

1. [Foundation Setup](../foundation-setup-both-tracks/company-registration)
2. The **ERPNext-Only Track** VAT section (VAT applies to the full suite too)
3. **Full Suite: Payroll Foundations**, **Employees**, **Running Payroll**, and **Statutory Submissions**
4. **SA Labour & COIDA** as needed.

## Quick comparison

| Capability | Track A (ERPNext-only) | Track B (Full suite) |
|---|---|---|
| HRMS required | No | Yes |
| VAT settings & VAT201 | Yes | Yes |
| SA print formats (invoices) | Yes | Yes |
| Payroll (PAYE/UIF/SDL/ETI) | No | Yes |
| Salary slip & EMP201/EMP501/IRP5 | No | Yes |
| COIDA module | Yes (no payroll integration) | Yes (with payroll earnings) |
| SA Labour (SETA, EE, skills, trips) | Yes | Yes |

> COIDA and SA Labour work in both tracks. In the full suite, COIDA's annual return can aggregate earnings directly from submitted salary slips; in the ERPNext-only track you capture earnings manually.

## Moving from Track A to Track B later

You can start on Track A and add payroll later. Install HRMS, run `bench --site <site> migrate`, and the payroll DocTypes, overrides, salary components and SA Payroll workspace activate automatically. Then work through the payroll sections of this guide.
