# SA Labour Configuration and Testing Practitioner Guide

This guide explains how to configure, test, and validate the SA Labour module in ZA Local.

## Purpose And Scope

SA Labour provides practitioner support for South African labour administration. It covers SETA records, bargaining council references, sectoral wage references, industry-specific contributions, business trip calculations, Workplace Skills Plan records, Annual Training Report records, skills development records, and Employment Equity reports.

SA Labour does not submit WSP, ATR, Employment Equity, or bargaining council returns electronically. It provides structured data, working papers, and review reports for practitioner use.

## Prerequisites

Before configuring SA Labour:

- Company, departments, designations, and employees exist.
- Employee demographic and Employment Equity fields are available.
- HRMS is installed if employee, leave, or expense workflows will be used.
- Expense Claim Types exist if Business Trip expense claim automation will be enabled.
- The practitioner has access to Employee, Labour masters, Business Trip, WSP, ATR, Skills Development Record, and Employment Equity reports.

## Required Master Data And Settings

Review or create:

- SETA records.
- Bargaining Council records.
- Sectoral Minimum Wage records.
- Industry Specific Contribution records.
- Business Trip Settings.
- Business Trip Regions.
- Employee Employment Equity fields.
- Workplace Skills Plan records.
- Annual Training Report records.
- Skills Development Records.

## Configuration Tutorial

### 1. Configure Employee Labour Fields

Open each Employee and review:

- Race.
- Gender.
- Disability status.
- Occupational level.
- Department.
- Designation.
- Employment status.

Validation:

- Employment Equity reports can group employees by occupational level and race.
- Missing employee fields are corrected before report submission.

### 2. Configure SETA Records

1. Open `SETA`.
2. Create the SETA applicable to the company.
3. Capture SETA name, code, and description.
4. Save.

Validation:

- SETA can be referenced in skills planning and practitioner working papers.

### 3. Configure Bargaining Council Records

1. Open `Bargaining Council`.
2. Create the applicable bargaining council.
3. Capture registration or reference details where available.
4. Save.

Validation:

- The record is available for sector or employee review.

### 4. Configure Sectoral Minimum Wage

1. Open `Sectoral Minimum Wage`.
2. Create the sector, role, or category.
3. Capture effective date.
4. Capture hourly, weekly, or monthly rate as applicable.
5. Save.

Validation:

- The effective date and sector are clear.
- The practitioner has confirmed current statutory or bargaining council rates.

### 5. Configure Industry Specific Contributions

1. Open `Industry Specific Contribution`.
2. Create contribution records for sector-specific deductions or employer contributions.
3. Capture contribution type, rate, and effective dates.
4. Save.

Validation:

- The record supports payroll or practitioner review where applicable.

### 6. Configure Business Trip Settings

1. Open `Business Trip Settings`.
2. Set mileage allowance rate.
3. Set mileage expense claim type.
4. Set meal or allowance expense claim type.
5. Set incidental expense claim type.
6. Decide whether submitted Business Trips should create Expense Claims automatically.
7. Save.

Validation:

- Mileage calculations use the configured rate.
- Expense Claim automation is enabled only when expense types and approvers are ready.

### 7. Configure Business Trip Regions

1. Open `Business Trip Region`.
2. Create local and foreign travel regions where required.
3. Capture daily allowance rate.
4. Capture incidental allowance rate.
5. Save.

Validation:

- Regions can be selected on Business Trip allowance rows.

### 8. Configure Workplace Skills Plan

1. Open `Workplace Skills Plan`.
2. Create a plan for the company and year.
3. Add planned training rows.
4. Capture planned learners, intervention type, and budget.
5. Save.

Validation:

- Total planned training budget agrees with row values.
- The plan status is suitable for practitioner review.

### 9. Configure Annual Training Report

1. Open `Annual Training Report`.
2. Create a report for the company and year.
3. Add completed training rows.
4. Capture actual learners, training dates, and actual spend.
5. Save.

Validation:

- Actual spend agrees with row values.
- Completed training can be compared to the Workplace Skills Plan.

### 10. Configure Skills Development Records

1. Open `Skills Development Record`.
2. Select employee.
3. Capture training intervention details.
4. Capture training cost.
5. Capture disability or B-BBEE support details where applicable.
6. Save.

Validation:

- Training cost cannot be negative.
- Date ranges are valid.
- Any B-BBEE support metric is treated as practitioner-support evidence, not a certified score.

## Desk Test Cases

### Test 1: SETA Master Setup

Steps:

1. Create a SETA record.
2. Save.
3. Reopen the record.

Expected result:

- SETA record saves and remains searchable.

### Test 2: Bargaining Council Setup

Steps:

1. Create a Bargaining Council record.
2. Save.
3. Reopen the record.

Expected result:

- Bargaining Council record saves and can be referenced for labour review.

### Test 3: Sectoral Minimum Wage Setup

Steps:

1. Create a Sectoral Minimum Wage record.
2. Enter sector, role, effective date, and rate.
3. Save.

Expected result:

- The record has a clear effective date and rate.
- The practitioner can compare employee pay against the reference.

### Test 4: Industry Specific Contribution Setup

Steps:

1. Create an Industry Specific Contribution.
2. Enter contribution type, rate, and effective dates.
3. Save.

Expected result:

- Contribution record is available for practitioner review.

### Test 5: Business Trip Allowance Calculation

Steps:

1. Configure Business Trip Settings.
2. Configure a Business Trip Region.
3. Create a Business Trip.
4. Add allowance rows.
5. Save.

Expected result:

- Daily allowance and incidental totals calculate correctly.
- Grand total includes allowances.

### Test 6: Business Trip Mileage Calculation

Steps:

1. Add a journey using private car.
2. Enter distance.
3. Save.

Expected result:

- Mileage rate is fetched from settings.
- Mileage claim equals distance multiplied by mileage rate.

### Test 7: Accommodation And Other Expenses

Steps:

1. Add accommodation rows.
2. Add other expense rows.
3. Save.

Expected result:

- Accommodation total equals accommodation rows.
- Other expense total equals other expense rows.
- Grand total includes both.

### Test 8: Optional Expense Claim Creation

Steps:

1. Enable auto-create Expense Claim if the company uses it.
2. Ensure Expense Claim Types exist.
3. Submit Business Trip.

Expected result:

- Expense Claim is created only when settings and ERPNext master data allow it.
- If not enabled, Business Trip remains a working paper.

### Test 9: Workplace Skills Plan

Steps:

1. Create a Workplace Skills Plan.
2. Add planned training rows.
3. Save.

Expected result:

- Planned budget total is calculated.
- Plan can be reviewed before training delivery.

### Test 10: Annual Training Report

Steps:

1. Create an Annual Training Report.
2. Add completed training rows.
3. Save.

Expected result:

- Actual spend total is calculated.
- Completed training can be compared to planned training.

### Test 11: Skills Development Record

Steps:

1. Create a Skills Development Record for an employee.
2. Enter date, intervention, provider, and cost.
3. Save.

Expected result:

- Record saves when dates and costs are valid.
- Negative costs or invalid date ranges are rejected where validation applies.

### Test 12: Employee Employment Equity Fields

Steps:

1. Open Employee.
2. Complete Employment Equity fields.
3. Save.

Expected result:

- Employee can be included in Employment Equity reports.

### Test 13: EE Workforce Profile

Steps:

1. Open `EE Workforce Profile`.
2. Filter by company.
3. Run.

Expected result:

- Report opens without errors.
- Rows group employees according to available Employment Equity fields.

### Test 14: EEA2 Income Differentials

Steps:

1. Open `EEA2 Income Differentials`.
2. Filter by company.
3. Run.

Expected result:

- Report opens without errors.
- Income differential values are based on available payroll and employee data.

### Test 15: EEA4 Employment Equity Plan

Steps:

1. Open `EEA4 Employment Equity Plan`.
2. Filter by company.
3. Run.

Expected result:

- Report opens without errors.
- Missing setup is clearly indicated if Employee custom fields are not available.

## Reports To Review

- EE Workforce Profile
- EEA2 Income Differentials
- EEA4 Employment Equity Plan

## Common Mistakes And Troubleshooting

- If Employment Equity reports are empty, review Employee race, occupational level, disability, gender, and status fields.
- If Business Trip totals are zero, confirm allowance, journey, accommodation, and expense rows were entered.
- If mileage does not calculate, confirm transport mode is private car and mileage settings exist.
- If Expense Claim creation fails, confirm HRMS/ERPNext expense claim setup, expense types, approver, and permissions.
- If WSP or ATR totals do not agree, review child table rows and saved values.

## Practitioner Responsibility

Practitioners must confirm current labour rates, SETA requirements, bargaining council rules, Employment Equity classifications, and submission rules before using the data externally. ZA Local provides structured records and reports, not external portal submission or statutory certification.

