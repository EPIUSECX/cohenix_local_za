# South Africa Payroll Configuration and Testing

This guide documents the current `za_local` SA Payroll setup flow and the sandbox evidence captured on `development.cohenix`.

## Current SARS Baseline

Use official SARS references before changing production defaults:

- The 2027 tax year runs from 1 March 2026 to 28 February 2027.
- The individual PAYE table starts at 18% from the first rand and uses rebates to create the tax-free thresholds.
- 2027 rebates are primary `R17,820`, secondary `R9,765`, and tertiary `R3,249`.
- 2027 medical scheme fees tax credits are `R376` for the taxpayer, `R376` for the first dependant, and `R254` for each additional dependant.
- Retirement fund deductions are capped for PAYE at the lower of actual qualifying contributions, `27.5%` of the relevant taxable base before the deduction, and `R350,000` per tax year.
- EMP201 is monthly and covers PAYE, SDL, UIF, and ETI.

References:

- SARS employer tax deduction tables: https://www.sars.gov.za/wp-content/uploads/Ops/Guides/PAYE-GEN-01-G01-Guide-for-Employers-in-respect-of-Tax-Deduction-Tables-External-Guide.pdf
- SARS employees tax guide 2027: https://www.sars.gov.za/guide-for-employers-in-respect-of-employees-tax-2027/
- SARS EMP201 guide: https://www.sars.gov.za/types-of-tax/pay-as-you-earn/completing-the-monthly-employer-declaration-emp201/
- SARS medical tax credit rates: https://www.sars.gov.za/tax-rates/medical-tax-credit-rates/
- SARS PAYE BRS source-code guide: https://www.sars.gov.za/wp-content/uploads/Docs/PAYE/BRS/SARS_PAYE_BRS-PAYE-Employer-Reconciliation_V25-1-0.pdf
- SARS retirement contribution deduction FAQ: https://www.sars.gov.za/faq/faq-what-are-s11f-annual-allowable-deductions/

## ERPNext and HRMS Integration Model

SA Payroll extends HRMS payroll instead of replacing it.

- HRMS must be installed for Salary Slip, Salary Structure, Payroll Entry, and related payroll doctypes.
- `za_local` overrides HRMS `Salary Slip`, `Payroll Entry`, `Additional Salary`, and `Salary Structure Assignment` only when HRMS is installed.
- SARS payroll codes are stored on Salary Components through `za_sars_payroll_code`.
- Company contributions use the HRMS `Company Contribution` table on Salary Structure and Salary Slip.
- EMP201 totals are generated from submitted Salary Slips, salary component SARS codes, company contributions, and stored ETI values.
- Retirement-fund deduction rows are recognised by SARS code or component name and are treated as pre-tax before applying the South African annual cap.
- Medical aid credits are sourced from `Employee Private Benefit`; a main member with no dependants still receives the main-member monthly credit.

## Required Setup Procedure

1. Confirm the company has a 2026/2027 fiscal year and payroll period.
2. Assign a Holiday List through `Holiday List Assignment`; HRMS uses this for working-day calculations.
3. Configure Company registration fields:
   - PAYE reference number
   - UIF reference number
   - SDL reference number
   - COIDA registration number where applicable
4. Open `Payroll Settings` and set the SA statutory components:
   - PAYE Salary Component: `PAYE`
   - UIF Employee Salary Component: `UIF Employee Contribution`
   - UIF Employer Salary Component: `UIF Employer Contribution`
   - SDL Salary Component: `SDL Contribution`
5. Confirm salary component account rows for the company:
   - Earnings to salary expense accounts.
   - PAYE to a SARS/PAYE liability account.
   - UIF employee to a UIF liability account.
   - UIF employer and SDL to employer contribution expense accounts. The Payroll Entry company-contribution journal credits Payroll Payable separately.
6. Confirm the seeded Salary Components:
   - Statutory: `PAYE`, `UIF Employee Contribution`, `UIF Employer Contribution`, `SDL Contribution`.
   - Earnings: `Basic Salary`, `Housing Allowance`, `Transport Allowance`, `13th Cheque`, `Performance Bonus`, `Overtime`, `Commission`.
7. Confirm tax data:
   - `South Africa 2026-2027` Income Tax Slab uses seven marginal brackets from 18% to 45%.
   - `Tax Rebates and Medical Tax Credit` includes the current payroll period rows.
8. Create an Employee Type such as `Permanent` and link it to the payroll payable account.
9. Create employees with South African payroll fields:
   - Employee Type
   - SA ID number
   - hours per month for ETI pro-rating
   - tax certificate fields where IRP5/IT3(a) processing is required
10. Create and submit Salary Structure Assignments with:
   - `base`
   - `income_tax_slab`
   - `from_date`
11. Create Salary Slips for the payroll period and submit them.
12. Create EMP201 Submission, fetch EMP201 data, review totals, and file manually through SARS eFiling.

## Sandbox Evidence

The following live staging was run through Docker against site `development.cohenix` using company `Cohenix`.

Configuration staged:

- Company: `Cohenix`
- Payroll period: `2026-2027`
- Payroll month tested: March 2026
- Holiday List: `South Africa 2026 Sandbox Holiday List`
- Salary Structure: `ZA Payroll Sandbox Monthly Structure`
- Employee Type: `Permanent`
- Income Tax Slab: `South Africa 2026-2027`
- EMP201 Submission: `EMP201-00001`

Submitted payslips:

| Employee | Gross Pay | PAYE | UIF Employee | Net Pay | UIF Employer | SDL | Monthly ETI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `HR-EMP-00001` / ZA Payroll Low | R10,000.00 | R315.00 | R100.00 | R9,585.00 | R100.00 | R100.00 | R0.00 |
| `HR-EMP-00002` / ZA Payroll High | R30,000.00 | R4,681.01 | R177.12 | R25,141.87 | R177.12 | R300.00 | R0.00 |
| `HR-EMP-00003` / ZA Payroll ETI | R4,500.00 | R0.00 | R45.00 | R4,455.00 | R45.00 | R45.00 | R1,000.00 |

Controls verified:

- PAYE uses the current SARS marginal table and annual rebates.
- UIF employee and employer contributions apply at 1% with the `R177.12` monthly cap.
- SDL applies at 1% of gross pay as an employer contribution.
- ETI is calculated for the qualifying employee and stored on the Salary Slip.
- Payroll Register returns Basic, PAYE, UIF, gross pay, total deductions, and net pay from submitted slips.
- EMP201 includes PAYE, employee + employer UIF, SDL, and ETI.

EMP201 result:

- Gross PAYE before ETI: `R4,996.01`
- ETI generated current month: `R1,000.00`
- ETI utilised current month: `R1,000.00`
- Net PAYE payable: `R3,996.01`
- UIF payable: `R644.24`
- SDL payable: `R445.00`
- Total payable in EMP201 report: `R5,085.25`

## EMP501 and IRP5 / IT3(a) Certificate Evidence

The interim EMP501 flow was tested end-to-end for the 2026/2027 tax year using submitted salary slips from March to August 2026.

Monthly EMP201 submissions were submitted for the full interim period:

| Month | EMP201 | Net PAYE | UIF | SDL |
| --- | --- | ---: | ---: | ---: |
| March 2026 | `EMP201-00001` | R3,996.01 | R644.24 | R445.00 |
| April 2026 | `EMP201-00004` | R426,502.52 | R1,062.72 | R10,878.00 |
| May 2026 | `EMP201-00005` | R403,076.27 | R1,062.72 | R10,878.00 |
| June 2026 | `EMP201-00006` | R403,076.27 | R1,062.72 | R10,878.00 |
| July 2026 | `EMP201-00002` | R403,076.27 | R1,062.72 | R10,878.00 |
| August 2026 | `EMP201-00003` | R403,076.27 | R1,062.72 | R10,878.00 |

EMP501 reconciliation `EMP501-2026-04-00005` fetched all six EMP201 declarations with no missing periods and submitted successfully.

EMP501 totals:

- Total PAYE: `R2,042,803.61`
- Total SDL: `R54,835.00`
- Total UIF: `R5,957.84`
- Total ETI: `R1,000.00`
- Total tax payable: `R2,102,596.45`

IRP5 / IT3(a) certificate generation created or reused certificates for all six employees with submitted salary slips in the interim period. The coverage gate now blocks EMP501 submission unless every employee in the reconciliation period has a valid certificate reference.

Certificate evidence:

- Six submitted IRP5 certificates exist for `Cohenix`, tax year `2026-2027`.
- High-income stress employees generated income, deduction, and employer-contribution certificate rows.
- Low-income ETI employee generated a certificate with zero PAYE and a reason for non-deduction for practitioner review.
- `EMP501_2026-2027_Interim.csv` generation succeeded.
- IRP5 official PDF generation succeeded for a submitted certificate.
- SARS XML / BRS export is intentionally blocked with a manual-filing message because direct SARS BRS submission is not supported in this release.

Additional certificate-control fixes validated during testing:

- EMP501 IRP5 generation now works on Frappe v16 without unsafe `distinct employee` select syntax.
- Submitted existing IRP5 certificates are reused instead of being treated as generation errors.
- Payroll-only deductions can be explicitly excluded from IRP5 / IT3(a) with `Exclude from IRP5 / IT3(a)`.
- Default mappings now include `Business Reimbursement` as non-taxable subsistence-style income and `Staff Loan Repayment` as loan repayment; `Garnishee Order` and `Union Subscription` are excluded from certificate export by default.

## High-Income and Complex Deduction Stress Test

Additional staging was run for higher salary and complex deduction scenarios to prove the payroll engine beyond the basic monthly examples.

Configuration added:

- Salary Structure: `ZA Payroll Stress Complex Structure`
- Salary Structure: `ZA Payroll Stress Retirement Cap Structure`
- Employee Private Benefit rows for medical aid with zero dependants and multiple dependants.
- Deduction components for pension fund, medical aid, garnishee order, staff loan repayment, and union subscription.
- Employer company contribution rows for UIF employer, SDL, employer pension contribution, and employer medical aid contribution.
- Taxable and non-taxable earnings for basic salary, housing allowance, travel allowance split, commission, performance bonus, overtime, company car fringe benefit, and business reimbursement.

Submitted August 2026 stress payslips:

| Employee | Gross Pay | PAYE | UIF Employee | Pension Deduction | Medical Deduction | Other Deductions | Net Pay | Employer Contributions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `HR-EMP-00004` / Executive Complex | R222,000.00 | R73,907.76 | R177.12 | R11,250.00 | R6,000.00 | R4,700.00 | R125,965.12 | R21,897.12 |
| `HR-EMP-00005` / Medical Main Only | R125,800.00 | R36,510.70 | R177.12 | R6,375.00 | R3,400.00 | R2,750.00 | R76,587.18 | R12,485.12 |
| `HR-EMP-00006` / Retirement Cap | R740,000.00 | R292,657.81 | R177.12 | R200,000.00 | R20,000.00 | R15,200.00 | R211,965.07 | R72,577.12 |

Retirement cap evidence:

- The `Retirement Cap` employee contributes `R200,000.00` per month to a pension component.
- The Salary Slip row is automatically marked tax-exempt because the component is recognised as a retirement-fund deduction.
- The annual disallowed retirement deduction add-back was `R1,650,000.00`.
- The disallowed add-back is stored on the read-only Salary Slip field `Retirement Fund Taxable Excess`.
- PAYE was calculated after the disallowed excess was added back, rather than allowing the full monthly pension deduction to shelter taxable income.

Company contribution evidence:

| Employee | UIF Employer | SDL | Employer Pension | Employer Medical | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Executive Complex | R177.12 | R2,220.00 | R15,000.00 | R4,500.00 | R21,897.12 |
| Medical Main Only | R177.12 | R1,258.00 | R8,500.00 | R2,550.00 | R12,485.12 |
| Retirement Cap | R177.12 | R7,400.00 | R50,000.00 | R15,000.00 | R72,577.12 |

August 2026 EMP201 result from submitted stress slips:

- Gross PAYE before ETI: `R403,076.27`
- ETI generated current month: `R0.00`
- Net PAYE payable: `R403,076.27`
- UIF payable: `R1,062.72`
- SDL payable: `R10,878.00`

Payroll Register result:

- The report returned all three August stress payslips.
- Basic salary, gross pay, PAYE, UIF employee, total deductions, and net pay matched the submitted Salary Slips.
- EMP201 UIF included both employee and employer UIF, while Payroll Register showed the employee UIF line only, as expected.

## Accounting and Report Sweep Evidence

April 2026 payroll was reposted through Payroll Entry `HR-PRUN-2026-00002` to prove the payroll data reaches Accounting correctly.

Payroll accrual journal `ACC-JV-2026-00003`:

- Debit `Salary - CX`: `R1,087,800.00`
- Credit `PAYE Payable - SARS - CX`: `R426,502.52`
- Credit `UIF Employee Contribution - CX`: `R531.36`
- Credit payroll deduction liabilities for pension, medical aid, staff loans, garnishee, and union fees.
- Credit `Payroll Payable - CX`: `R391,091.12`

Company contribution journal `ACC-JV-2026-00004`:

- Debit `SDL Expense - CX`: `R10,878.00`
- Debit `UIF Employer Expense - CX`: `R531.36`
- Credit `Payroll Payable - CX`: `R11,409.36`

Final report sweep on `development.cohenix`:

- SA Payroll reports passed: `Payroll Register`, `Department Cost Analysis`, `Statutory Submissions Summary`, `EMP201 Report`, `Retirement Fund Deductions`.
- HRMS reports exposed in ZA Payroll passed: `Salary Register`, `Bank Remittance`, `Salary Payments Based On Payment Mode`, `Salary Payments via ECS`, `Income Tax Deductions`, `Income Tax Computation`.
- Financial reports passed: `General Ledger`, `Accounts Receivable`, `Accounts Payable`, `Trial Balance`, `Profit and Loss Statement`, `Balance Sheet`.
- India-specific HRMS reports `Provident Fund Deductions` and `Professional Tax Deductions` are intentionally not exposed in the ZA Payroll workspace because they require India-only HRMS fields and are not South African payroll reports. ZA Local exposes `Retirement Fund Deductions` for South African pension/provident/retirement-annuity deduction review.

Additional payroll statutory workflow smoke tests passed:

- `Company Car Benefit`, `Housing Benefit`, `Low Interest Loan Benefit`, `Cellphone Benefit`, `Fuel Card Benefit`, and `Bursary Benefit` records were created and calculated.
- `Fringe Benefit` was submitted and generated a monthly taxable-value breakdown.
- `Tax Directive` was submitted and the active-directive lookup returned the expected record.
- `Employee Final Settlement` calculated gross, PAYE, UIF, and net settlement; automatic payslip/IRP5 actions are now explicitly gated as manual processes instead of showing placeholder success messages.
- `UIF U19 Declaration` calculated employee UIF contributions using SARS code mapping and generated U19 form data.
- `Leave Encashment SA` calculated tax/net values and created an HRMS `Additional Salary` record.
- `Payroll Payment Batch` calculated employee count and net-pay total from a submitted Payroll Entry and marked EFT evidence as generated.
- `Travel Allowance Rate` and `Sars Vehicle Emissions Rate` records were created and current-rate lookups succeeded.

## Verification Commands

Run data fixture validation:

```bash
docker exec 8afddd0cf4e4 bash -lc 'cd /workspace/development-bench && bench --site development.cohenix execute za_local.test_data_loading.run_all_tests'
```

Expected result:

```text
RESULTS: 7 passed, 0 failed
```

Run the staged EMP201 and payroll report check:

```bash
docker exec 8afddd0cf4e4 bash -lc 'cd /workspace/development-bench && env/bin/python - <<'"'"'PY'"'"'
import frappe

frappe.init(site="development.cohenix", sites_path="/workspace/development-bench/sites")
frappe.connect()

doc = frappe.get_doc("EMP201 Submission", "EMP201-00001")
print({
    "gross_paye_before_eti": doc.gross_paye_before_eti,
    "eti_generated_current_month": doc.eti_generated_current_month,
    "eti_utilized_current_month": doc.eti_utilized_current_month,
    "net_paye_payable": doc.net_paye_payable,
    "uif_payable": doc.uif_payable,
    "sdl_payable": doc.sdl_payable,
})

frappe.destroy()
PY'
```

Run the high-income payroll stress assertion:

```bash
docker exec 8afddd0cf4e4 bash -lc 'cd /workspace/development-bench && env/bin/python - <<'"'"'PY'"'"'
import frappe
from frappe.utils import flt
from za_local.sa_payroll.report.payroll_register.payroll_register import execute as payroll_register

frappe.init(site="development.cohenix", sites_path="sites")
frappe.connect()

emp201 = frappe.get_doc("EMP201 Submission", "EMP201-00003")
assert flt(emp201.gross_paye_before_eti, 2) == 403076.27
assert flt(emp201.uif_payable, 2) == 1062.72
assert flt(emp201.sdl_payable, 2) == 10878.0

slip = frappe.get_doc("Salary Slip", "Sal Slip/None/00018")
assert flt(slip.za_retirement_fund_taxable_excess, 2) == 1650000.00

_columns, rows = payroll_register({"company": "Cohenix", "from_date": "2026-08-01", "to_date": "2026-08-31"})
assert len(rows) == 3
print("High-income payroll stress assertion passed")

frappe.destroy()
PY'
```

## Practitioner Acceptance Criteria

A company is ready for SA payroll processing when:

- HRMS payroll doctypes are installed.
- Holiday List Assignment exists for the company or employees.
- Payroll Settings points to the ZA statutory components.
- Every Salary Component used on submitted slips has an account row for the company.
- Employees have Employee Type, SA identity/tax certificate fields, and ETI hours where applicable.
- Salary Structure Assignments use the correct South African Income Tax Slab.
- Submitted Salary Slips show PAYE, UIF employee, UIF employer, SDL, ETI, and net pay as expected.
- Retirement-fund salary components are mapped to SARS deduction codes and capped for PAYE.
- Medical-aid Employee Private Benefit rows exist where medical tax credits must apply.
- EMP201 fetch agrees with the submitted payslips and Payroll Register.
- Direct SARS submission is not implied; reviewed values are filed manually.
