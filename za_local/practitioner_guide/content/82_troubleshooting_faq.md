# Troubleshooting, FAQ & Glossary

## Troubleshooting

**Workspaces, fields or print formats are missing.**
Preserve the migration output and inspect Error Log/app versions. Reproduce and fix on a restored staging site; then back up and run the controlled migration/build/cache-clear workflow. Do not repeatedly migrate production as a diagnostic shortcut.

**"No South African statutory rate pack is configured for ..."**
The payroll engine has no rate pack covering that date. Add the rate pack for that tax year and migrate — see [Annual Statutory Update](annual-statutory-update). For back-dated runs, confirm a prior-year pack exists.

**SA Payroll workspace / payroll DocTypes are missing.**
HRMS is not installed. Install Frappe HR, then `bench --site <site> migrate`. Payroll features register only when HRMS is present.

**PAYE looks wrong (too high / too low / zero).**
Check payroll/slip dates, Payroll Period, Income Tax Slab, rate-pack coverage, rebates/medical benefit record, Salary Component classifications, prior slips/additional salaries and employee age/status. Reprocess only after identifying the mismatch.

**UIF is not capped / employer and employee differ.**
Check the UIF components' *UIF Applicable* flags and that the statutory components are mapped in Payroll Settings. UIF employee and employer should both be 1% of the same capped base.

**ETI is zero for an apparently eligible employee.**
Check age (18–29 from ID number), valid SA ID, months employed (≤24), remuneration below the ETI ceiling, *Hours per Month* set, and that *Disable ETI Calculation* is off in Payroll Settings.

**VAT201 has many "needs review" rows.**
Source items/templates are not classified. Set the item VAT category and use the correct tax template on the source documents, then re-fetch.

**EMP501 will not submit.**
A readiness check failed (missing month of EMP201, unlinked IRP5, missing employer reference, missing directive number). Read the specific message and fix the underlying record.

**Can't delete a posted invoice.**
This is intentional — `za_local` protects the SARS audit trail. Cancel and amend instead.

## FAQ

**Do I need HRMS?** Only for payroll. VAT, print formats, chart of accounts, COIDA and SA Labour work without it. See [Choosing Your Track](../getting-started/choosing-your-track).

**Does the app file to SARS electronically?** No. It produces internal working papers and audit trails. It does not create the SARS BRS payroll-import/encrypted reconciliation formats; generic CSV/PDF exports must not be uploaded as SARS files.

**Can I start ERPNext-only and add payroll later?** Yes, but restore to staging, install HRMS, rehearse migration, and verify all payroll metadata/settings before production activation.

**Where do the rates live?** In date-effective JSON rate packs (`statutory_rates_<YYYY>.json`), surfaced as Income Tax Slab, Tax Rebates, ETI Slab and Travel Allowance Rate records.

**How do I re-stage this guide after editing it?** Either click **Documentation → Publish Practitioner Guide** on **ZA Local Setup** (shown when the Wiki app is installed), or re-run `bench --site <site> execute za_local.practitioner_guide.stage.stage_space`. Both are idempotent.

## Glossary

| Term | Meaning |
|---|---|
| **PAYE** | Pay-As-You-Earn — employees' tax withheld monthly. |
| **UIF** | Unemployment Insurance Fund — 1% employee + 1% employer, capped. |
| **SDL** | Skills Development Levy — 1% employer levy. |
| **ETI** | Employment Tax Incentive — employer incentive reducing PAYE payable for qualifying young/low earners. |
| **COIDA / OID** | Compensation for Occupational Injuries and Diseases Act / Occupational Injury or Disease. |
| **EMP201** | Monthly employer declaration of PAYE/UIF/SDL/ETI. |
| **EMP501** | Annual/interim employer reconciliation. |
| **IRP5 / IT3(a)** | Employee annual tax certificate (IT3(a) where no tax was deducted). |
| **VAT201** | Periodic VAT return. |
| **SETA** | Sector Education and Training Authority. |
| **WSP / ATR** | Workplace Skills Plan / Annual Training Report. |
| **EEA2 / EEA4** | Employment Equity report forms. |
| **SARS** | South African Revenue Service. |
| **CIPC** | Companies and Intellectual Property Commission. |
| **BCEA** | Basic Conditions of Employment Act. |

## You're done

That completes the SA Practitioner Guide. Start at [Overview & Architecture](../getting-started/overview) if you need to orient a colleague.
