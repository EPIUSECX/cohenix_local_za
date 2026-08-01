# Prerequisites & Installation

## Prerequisites

| Requirement | Notes |
|---|---|
| Frappe Framework | v16 (the app targets `>=16.0.0,<17.0.0`). |
| ERPNext | **Required.** The app depends on ERPNext accounting. |
| Frappe HR (HRMS) | **Optional.** Install only if you need payroll. Without it, all payroll DocTypes, overrides and the SA Payroll workspace are disabled and the rest of the app works normally. |
| A site | A Frappe site on the bench where you will install the app. |

> If you are unsure whether to install HRMS, read [Choosing Your Track](choosing-your-track) first. HRMS can be added later, but rehearse the combined migration on staging and verify all payroll metadata/settings before use.

## Install the app

From the bench directory:

```bash
# 1. Fetch the app into the bench (use your repository URL/branch)
bench get-app za_local <repo-url> --branch version-16

# 2. (Optional) install Frappe HR if you need payroll
bench get-app hrms
bench --site <site> install-app hrms

# 3. Install za_local on the site
bench --site <site> install-app za_local

# 4. Build assets and clear cache
bench build --app za_local
bench --site <site> clear-cache
```

## What installation does automatically

`za_local`'s `after_install` (and `after_migrate`) hook runs a single sync routine that seeds and wires everything. You do **not** create these by hand:

- **Custom fields** are applied to Company, Customer, Item Group, Address, Employee, Salary Component, Payroll Settings, Salary Structure, Salary Slip, Salary Structure Assignment and more.
- **Property setters** adjust standard fields for the SA context.
- **Print formats** are installed: SA Sales Invoice, SA Full Tax Invoice, SA Abridged Tax Invoice, SA Credit Note, SA Debit Note, SA Quotation, SA Sales Order, SA Delivery Note, SA Purchase Invoice, SA Purchase Order, SA Payment Entry, and (with HRMS) SA Salary Slip, IRP5 Employee Certificate and IRP5-it3 Certificate.
- **SARS Payroll Codes** are seeded (income, deduction, employer-contribution codes used on IRP5).
- **Statutory rate packs** for the configured tax years are loaded, seeding ETI Slab and Travel Allowance Rate records.
- **Salary Components** with SA payroll treatment are seeded (PAYE, UIF Employee, UIF Employer, SDL, Severance Benefit, Leave Payout, Notice Pay, Tax on Lump Sum) — **only when HRMS is installed**.
- **Workspaces and desktop icons** are created: SA Overview, SA VAT, SA Payroll (HRMS only), SA Labour, SA COIDA, nested under a single "SA Localisation" app tile.

Install/migrate synchronizes app-owned schema and defaults. It may create or update configuration, so do not treat it as a harmless repair button. Back up database and files, rehearse on a restored staging site, review logs and local customizations, then run it in a controlled production maintenance window.

## Upgrading

To pick up a newer version on an existing site, first restore the production backup to staging and complete the documented acceptance matrix. In the controlled deployment window:

```bash
bench --site <site> migrate
bench build --app za_local
bench --site <site> clear-cache
```

`migrate` synchronizes schema/configuration. Review migration output, Error Log, custom fields, statutory coverage, accounts, permissions and navigation afterwards; successful execution is not practitioner signoff.

## Next

Continue to [Choosing Your Track](choosing-your-track), then verify the install with [Post-Install Verification](post-install-verification).
