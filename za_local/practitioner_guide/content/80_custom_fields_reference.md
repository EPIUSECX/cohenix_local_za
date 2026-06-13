# Custom Fields Reference

`za_local` adds custom fields to standard ERPNext/HRMS DocTypes. They are applied automatically on install and migrate (the source of truth is `za_local/sa_setup/custom_fields.py`). This page is a quick reference; field labels in your site may differ slightly by version.

## Company

South African Registration: VAT Number, COIDA Registration Number, SDL Reference Number, UIF Reference Number, PAYE Reference Number, Trading Name, Business Address. Additional Configuration: SETA, Bargaining Council, Sectoral Determination.

## Customer

Company Registration (CIPC), Is VAT Vendor.

## Item Group

Is Capital Goods (for VAT201 capital-input classification).

## Address

South African Address: Unit No, Complex Name, Street No, Suburb/District, Country Code (default ZA); Postal Address Type (Street, PO Box, Private Bag, Post Office, Care Of, Other), Care Of, Postal Service Number, Address Line 3/4.

## Employee (full suite)

- **South African Details:** ID Number, Employee Type, Special Economic Zone, Hours per Month (ETI), Payroll Payable Bank Account, Nationality, Working Hours per Week, Has Children, Has Other Employments, Number of Dependants, Highest Qualification.
- **Employment Equity:** Race, Occupational Level, Is Disabled.
- **Tax Certificate:** Identity Type, Income Tax Reference Number, Passport Country of Issue, Nature of Person, Residential Address, Postal Address, Business Address Override, Not Paid Electronically, Bank Account Type, Bank Account Holder Name, Bank Account Holder Relationship.

## Salary Component (full suite)

SARS Payroll Code, Exclude from IRP5, Payroll Treatment, PAYE Inclusion %, UIF Applicable, SDL Applicable, COIDA Applicable, Is Reimbursement, Variable Pay Treatment.

## Payroll Settings (full suite)

Calculate Annual Taxable Amount Based On, Disable ETI Calculation; statutory component mapping: PAYE / UIF Employee / UIF Employer / SDL / COIDA Salary Component.

## Salary Structure / Salary Slip / Salary Structure Assignment (full suite)

- **Salary Structure:** Company Contribution table.
- **Salary Slip:** Company Contribution table, Total Company Contribution, `za_retirement_fund_taxable_excess`, `za_monthly_eti`.
- **Salary Structure Assignment:** Annual Bonus.

## Other (full suite)

- **Additional Salary:** Is Company Contribution.
- **HR/Payroll settings:** Amount per Kilometre (mileage).
- **Expense Claim:** Business Trip (link).
- **Journal Entry Account:** Is Payroll Entry, Is Company Contribution.

## Re-applying

If a field is missing, run `bench --site <site> migrate` — the custom-field sync is idempotent and restores any missing fields.
