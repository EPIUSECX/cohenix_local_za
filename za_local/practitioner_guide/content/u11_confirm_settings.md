# Confirm Company, VAT & Payroll Settings

A two-minute check that the live configuration is correct for your company. Do this once when you start using the system, and again whenever something looks off.

## Company

Open your **Company** and confirm:

- **Country** is South Africa and **Default Currency** is ZAR.
- **VAT Number** is present and correct (if VAT-registered).
- For payroll: **PAYE / UIF / SDL reference numbers** are filled in.

## VAT settings

Open **South Africa VAT Settings** (SA VAT workspace) for your company and confirm:

- **Standard VAT Rate** is 15%.
- **Output VAT** and **Input VAT** accounts are set.
- The **VAT Rates** table lists Standard (15%), Zero (0%) and Exempt (0%).
- **VAT Filing Frequency** matches what SARS allocated (e.g. Bi-Monthly).

If templates are missing, the person who set up the system can run **Apply Recommended VAT Setup** on this screen to create the standard SA tax templates. → [practitioner: South Africa VAT Settings](/sa-guide/erpnext-only-track-vat-documents/vat-settings)

## Payroll settings (Frappe HR)

Open **Payroll Settings** and confirm the **South African Settings** section maps:

- **PAYE**, **UIF Employee**, **UIF Employer** and **SDL** to the correct salary components.
- **Calculate Annual Taxable Amount Based On** is set (usually *Payroll Period*).

Then open the **Income Tax Slab** for the current year and confirm it exists and is effective from 1 March.

## What if a value is wrong?

Don't fix statutory configuration by guessing. Most of these are owned by your administrator/consultant. Flag it to them or follow the linked practitioner page. Capturing transactions on wrong settings (e.g. an out-of-date tax slab) produces wrong VAT or PAYE.

## Next

Maintain the day-to-day master records: [Everyday Masters](everyday-masters).
