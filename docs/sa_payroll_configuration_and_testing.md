# SA Payroll Configuration and Testing Practitioner Guide

This guide explains how to configure, test, and validate South African payroll functionality in ZA Local.

## Purpose And Scope

SA Payroll extends HRMS payroll for South African statutory payroll processing. It supports PAYE, UIF, SDL, ETI, retirement fund treatment, medical tax credits, employer contributions, payroll reports, EMP201, EMP501, and IRP5 / IT3(a) certificate working papers.

HRMS is required for payroll execution. ZA Local does not replace HRMS payroll; it extends HRMS Salary Slip, Salary Structure, Payroll Entry, and related payroll workflows where HRMS is installed.

Direct SARS electronic submission is not supported. Practitioners must review working papers, exports, PDFs, and reports before manual SARS submission.

## Prerequisites

Before configuring SA Payroll:

- HRMS is installed.
- A South African company exists.
- Payroll Period and Fiscal Year exist.
- Holiday List and Holiday List Assignment are configured.
- Employee records exist.
- Chart of accounts contains payroll expense, payroll payable, PAYE liability, UIF liability, SDL expense, and employer contribution accounts.
- The practitioner has access to HRMS payroll, Salary Components, Salary Structures, Payroll Entry, Employee, EMP201, EMP501, IRP5 Certificate, and payroll reports.

## Required Master Data And Settings

Review or create:

- Company PAYE reference number.
- Company UIF reference number.
- Company SDL reference number.
- Payroll Settings statutory components.
- Payroll Period.
- Income Tax Slab.
- Tax Rebates and Medical Tax Credit.
- SARS Payroll Codes.
- Salary Components with SARS code mappings.
- Employee Type.
- Employees with South African identity and tax fields.
- Employee Private Benefit records for medical aid and other private benefits.
- Salary Structure and Salary Structure Assignment.
- Payroll Entry.

## Configuration Tutorial

### 1. Configure Company Statutory References

1. Open `Company`.
2. Capture PAYE reference number.
3. Capture UIF reference number.
4. Capture SDL reference number.
5. Capture COIDA reference where applicable.
6. Save.

Validation:

- EMP501 readiness checks can find employer references.
- IRP5 / IT3(a) certificate fields can be populated from Company.

### 2. Configure Payroll Settings

1. Open `Payroll Settings`.
2. Set the PAYE salary component.
3. Set the UIF employee salary component.
4. Set the UIF employer salary component.
5. Set the SDL salary component.
6. Review any payroll frequency, rounding, or working-day settings required by HRMS.
7. Save.

Validation:

- Statutory components are selectable.
- Components are mapped to the correct salary component type and account rows.

### 3. Review Salary Components

Open `Salary Component` and review:

- Basic Salary.
- Allowances.
- Overtime.
- Commission.
- Bonuses.
- PAYE.
- UIF Employee Contribution.
- UIF Employer Contribution.
- SDL Contribution.
- Pension, provident, retirement annuity, or retirement fund components.
- Medical aid deduction and employer contribution components.
- Non-statutory deductions such as staff loans, garnishee orders, and union subscriptions.

For each component, confirm:

- Type is earning, deduction, or company contribution as intended.
- Account row exists for the company.
- SARS payroll code is mapped where the component must appear on EMP201, IRP5, or deduction reports.
- Components that must not appear on IRP5 are explicitly excluded where the app provides that option.

### 4. Review Tax Tables And Credits

1. Open `Income Tax Slab`.
2. Confirm the relevant South African tax year exists.
3. Confirm all PAYE brackets and rates.
4. Open `Tax Rebates and Medical Tax Credit`.
5. Confirm rebate rows and medical credit rows for the payroll year.
6. Save.

Validation:

- The Salary Structure Assignment can reference the correct Income Tax Slab.
- PAYE calculations use the expected tax year.

### 5. Configure Employees

For each employee:

1. Open `Employee`.
2. Set company, department, designation, date of joining, and employment status.
3. Set Employee Type.
4. Capture South African identity or passport details.
5. Capture income tax reference where available.
6. Capture bank details where salary payment and IRP5 output require them.
7. Capture ETI-related fields where ETI is applicable.
8. Capture Employment Equity fields if Labour reports are also used.
9. Save.

Validation:

- Employee can be used on Salary Structure Assignment.
- IRP5 readiness checks do not report avoidable missing fields.

### 6. Configure Employee Private Benefits

Create `Employee Private Benefit` rows where applicable:

- Medical aid main member.
- Medical aid dependants.
- Company car.
- Housing.
- Low-interest loan.
- Cellphone.
- Fuel card.
- Bursary.

Validation:

- Medical tax credits apply only where a medical aid benefit exists.
- Fringe benefits are visible and reviewable.

### 7. Configure Salary Structure

1. Create or open `Salary Structure`.
2. Add earnings.
3. Add deductions.
4. Add company contributions.
5. Ensure all components have account rows for the company.
6. Save and submit if required by HRMS.

Recommended test structures:

- Low salary structure.
- High salary structure.
- ETI qualifying structure.
- Medical aid structure.
- Retirement fund structure.
- Retirement cap stress structure.

### 8. Create Salary Structure Assignment

1. Open `Salary Structure Assignment`.
2. Select employee.
3. Select salary structure.
4. Set base amount.
5. Set from date.
6. Select Income Tax Slab.
7. Submit.

Validation:

- Salary Slip can be created from the assignment.
- Income tax slab is populated.

### 9. Process Payroll

1. Open `Payroll Entry`.
2. Select company, payroll period, payroll frequency, start date, and end date.
3. Get employees.
4. Create Salary Slips.
5. Review each Salary Slip.
6. Submit Salary Slips.
7. Submit Payroll Entry where applicable.
8. Post accounting entries.

Validation:

- Salary Slips calculate PAYE, UIF, SDL, ETI, retirement treatment, medical credits, and net pay correctly.
- GL Entries are balanced.
- Payroll payable and statutory liability accounts agree to payroll reports.

## Desk Test Cases

### Test 1: Payroll Settings Statutory Mapping

Steps:

1. Open Payroll Settings.
2. Confirm PAYE, UIF employee, UIF employer, and SDL components.
3. Save.

Expected result:

- Settings save.
- Each statutory component points to the intended Salary Component.

### Test 2: Low Salary PAYE/UIF Scenario

Steps:

1. Create an employee with a low monthly salary.
2. Assign a salary structure.
3. Create and submit a Salary Slip.

Expected result:

- UIF employee and employer calculate up to the monthly cap.
- PAYE reflects tax table, rebates, and taxable income.
- Net pay equals gross less deductions.

### Test 3: High Salary PAYE Scenario

Steps:

1. Create an employee with a high monthly salary.
2. Assign a structure with taxable earnings.
3. Submit a Salary Slip.

Expected result:

- PAYE uses the correct marginal tax brackets.
- UIF is capped.
- SDL is calculated as an employer contribution where configured.

### Test 4: ETI Qualifying Employee

Steps:

1. Create an employee who meets ETI criteria.
2. Capture ETI hours and identity details.
3. Submit a Salary Slip.

Expected result:

- Monthly ETI is calculated where eligible.
- ETI is stored on the Salary Slip.
- EMP201 can utilise ETI against PAYE.

### Test 5: Medical Aid Main Member

Steps:

1. Create Employee Private Benefit for medical aid main member.
2. Submit Salary Slip.

Expected result:

- Medical tax credit is applied for the main member.
- PAYE is reduced only by the allowed credit.

### Test 6: Medical Aid Dependants

Steps:

1. Add dependants to the medical aid benefit.
2. Submit Salary Slip.

Expected result:

- Medical credit includes main member, first dependant, and additional dependant rates.
- The credit does not exceed configured statutory treatment.

### Test 7: Pension / Provident / Retirement Annuity

Steps:

1. Add a retirement fund deduction component.
2. Map the SARS payroll code.
3. Submit Salary Slip.

Expected result:

- Retirement deduction is treated as pre-tax where allowed.
- Retirement Fund Deductions report shows the deduction.

### Test 8: Retirement Contribution Cap

Steps:

1. Create a salary slip where annualised retirement contributions exceed the statutory cap.
2. Submit Salary Slip.

Expected result:

- Excess retirement deduction is added back as taxable.
- Read-only retirement taxable excess field shows the excess.
- PAYE is calculated after the add-back.

### Test 9: Company Contributions

Steps:

1. Add UIF employer and SDL as company contribution rows.
2. Submit Salary Slip.
3. Post Payroll Entry accounting.

Expected result:

- Employee deductions and employer contributions are separated.
- Employer contributions post to expense and payroll payable according to configuration.

### Test 10: Payroll Entry To GL

Steps:

1. Create Payroll Entry.
2. Submit Salary Slips.
3. Submit Payroll Entry and post accounting.
4. Open General Ledger.

Expected result:

- Earnings debit salary expense accounts.
- PAYE, UIF employee, and other deductions credit liability accounts.
- Net pay credits payroll payable.
- Employer contributions post as configured.

### Test 11: EMP201 Creation And Review

Steps:

1. Create `EMP201 Submission`.
2. Select company and month.
3. Fetch EMP201 data.
4. Review PAYE, UIF, SDL, ETI, and total payable.

Expected result:

- EMP201 values agree with submitted Salary Slips.
- ETI reduces PAYE only as allowed.
- Unmapped statutory components are flagged before finalisation.

### Test 12: EMP501 Reconciliation

Steps:

1. Create monthly EMP201 submissions for the reconciliation period.
2. Create `EMP501 Reconciliation`.
3. Select tax year and reconciliation period.
4. Fetch EMP201 references.
5. Validate coverage.

Expected result:

- Missing EMP201 months are reported.
- EMP501 cannot proceed without required monthly declarations.

### Test 13: IRP5 / IT3(a) Certificate

Steps:

1. Generate or create IRP5 certificates for employees in the reconciliation period.
2. Review employer details.
3. Review employee identity, address, and bank details.
4. Review income, deduction, and employer contribution lines.
5. Print using `IRP5 Employee Certificate`.

Expected result:

- Certificate is linked to the correct EMP501 where applicable.
- Submitted certificates render to PDF.
- Long certificate numbers do not overlap critical text.
- Missing statutory data is visible for practitioner review.

### Test 14: SA Salary Slip Print Format

Steps:

1. Open a submitted Salary Slip.
2. Print using `SA Salary Slip`.

Expected result:

- Earnings, deductions, company contributions, statutory amounts, gross pay, net pay, and company details are readable.
- No old app references appear.

### Test 15: Payroll Reports

Steps:

1. Run Payroll Register.
2. Run EMP201 Report.
3. Run Statutory Submissions Summary.
4. Run Department Cost Analysis.
5. Run Retirement Fund Deductions.

Expected result:

- Reports open without errors.
- Filters work for company and period.
- Report totals agree with submitted payroll records.

## Reports And Print Formats To Review

Reports:

- Payroll Register
- EMP201 Report
- Department Cost Analysis
- Statutory Submissions Summary
- Retirement Fund Deductions
- HRMS Salary Register
- HRMS Income Tax Computation
- General Ledger

Print formats:

- SA Salary Slip
- IRP5 Employee Certificate
- IRP5-it3 Certificate

## Common Mistakes And Troubleshooting

- If Salary Slip does not calculate, check Salary Structure Assignment and Income Tax Slab.
- If PAYE is zero unexpectedly, check taxable earnings, rebates, and tax slab.
- If UIF is missing, check Payroll Settings and salary component mapping.
- If SDL is missing, check company contribution rows.
- If EMP201 is incomplete, check submitted Salary Slips and SARS payroll code mappings.
- If EMP501 blocks submission, complete missing EMP201 months or IRP5 certificate references.
- If IRP5 PDF is incomplete, review Company, Employee, Address, Salary Component, and certificate line data.
- If GL does not post correctly, review salary component account rows for the company.

## Practitioner Responsibility

Payroll practitioners must validate every statutory rate, employee classification, PAYE value, UIF value, SDL value, ETI value, EMP201 value, EMP501 value, IRP5 / IT3(a) certificate, and GL posting before filing or payment. ZA Local supports calculation and review; it does not remove practitioner responsibility.

