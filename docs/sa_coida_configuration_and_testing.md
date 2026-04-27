# SA COIDA Configuration and Testing Practitioner Guide

This guide explains how to configure, test, and validate the SA COIDA module in ZA Local.

## Purpose And Scope

SA COIDA supports Compensation Fund setup records, industry assessment rates, annual return working papers, workplace injury records, OID claims, and OID medical reports.

SA COIDA does not submit directly to the Compensation Fund or eCOID. The supported process is prepare, review, export or print evidence where required, and file manually through the relevant external process.

## Prerequisites

Before configuring SA COIDA:

- Company exists.
- Fiscal year exists.
- Employees exist.
- Payroll Salary Slips are submitted if the annual return should fetch payroll-backed earnings.
- COIDA registration and Compensation Fund reference details are available.
- Industry assessment rates have been confirmed by the practitioner.
- HRMS leave features are configured if workplace injury leave automation will be used.
- The practitioner has access to COIDA Settings, COIDA Annual Return, Workplace Injury, OID Claim, and Employee records.

## Required Master Data And Settings

Review or create:

- COIDA Settings.
- COIDA Industry Rate rows.
- Fiscal Year.
- Submitted Salary Slips for the assessment period where payroll-backed annual return values are required.
- Workplace Injury records.
- OID Claim records.
- OID Medical Report records.

## Configuration Tutorial

### 1. Configure COIDA Settings

1. Open `COIDA Settings`.
2. Capture COIDA registration number.
3. Capture Compensation Fund reference number.
4. Capture assessment year.
5. Capture submission deadline.
6. Add industry rate rows.
7. Save.

Validation:

- Industry rates are numeric and greater than or equal to zero.
- Registration and reference numbers are available for practitioner review.

### 2. Configure COIDA Industry Rate

1. Open `COIDA Industry Rate`.
2. Create the applicable industry class.
3. Capture industry description.
4. Capture assessment rate percentage.
5. Save.

Validation:

- The industry class can be selected on the COIDA Annual Return.
- The assessment rate matches the practitioner-confirmed current rate.

### 3. Prepare Payroll Evidence

If using payroll-backed annual returns:

1. Confirm Salary Slips are submitted for the assessment period.
2. Confirm Salary Slips are for the correct company.
3. Confirm directors and ordinary employees are correctly classified in Employee records.
4. Confirm payroll values have already been reviewed.

Validation:

- COIDA Annual Return can fetch employee count and earnings from submitted Salary Slips.

### 4. Create COIDA Annual Return

1. Open `COIDA Annual Return`.
2. Create a new return.
3. Select company.
4. Select fiscal year.
5. Confirm from date and to date.
6. Select industry class.
7. Click `Fetch Employee Data` if payroll-backed values are required.
8. Review employee count, total annual earnings, director earnings, assessment rate, and assessment fee.
9. Save.
10. Submit only after practitioner review.

Validation:

- Date range aligns to the selected fiscal year.
- Assessment fee equals total annual earnings multiplied by the assessment rate percentage.
- Status updates after submission.

### 5. Capture Workplace Injury

1. Open `Workplace Injury`.
2. Select company and employee.
3. Capture injury date.
4. Capture injury type, location, and description.
5. Indicate whether leave is required.
6. Indicate whether an OID claim is required.
7. Save.
8. Submit when reviewed.

Validation:

- Injury date cannot be in the future.
- Expected recovery date cannot be before injury date.
- Leave days calculate where recovery date is available.
- If HRMS leave is not available, injury tracking still remains usable.

### 6. Create And Manage OID Claim

1. Open `OID Claim` or create it from Workplace Injury.
2. Confirm linked Workplace Injury.
3. Confirm employee, company, injury date, injury type, and injury location.
4. Capture claim date.
5. Submit claim when ready.
6. Update claim status as the external process progresses:
   - Pending
   - Submitted
   - Under Review
   - Approved
   - Rejected
   - Paid
7. Capture compensation amount and payment date when paid.

Validation:

- Claim date cannot be before injury date.
- Payment date cannot be before claim date.
- Linked Workplace Injury status updates as claim status changes.

### 7. Capture OID Medical Report

1. Open the OID Claim.
2. Add or create OID Medical Report records.
3. Capture medical practitioner, report date, diagnosis, recovery information, and cost details where applicable.
4. Save.

Validation:

- Medical reports remain linked to the claim.
- Reports support claim review evidence.

## Desk Test Cases

### Test 1: COIDA Settings Setup

Steps:

1. Open COIDA Settings.
2. Enter registration number, reference number, assessment year, and deadline.
3. Save.

Expected result:

- Settings save successfully.
- Values are available for annual return preparation.

### Test 2: COIDA Industry Rate Setup

Steps:

1. Create COIDA Industry Rate.
2. Enter industry class and assessment rate.
3. Save.

Expected result:

- Industry rate saves.
- Rate can be used on COIDA Annual Return.

### Test 3: COIDA Annual Return Creation

Steps:

1. Create COIDA Annual Return.
2. Select company and fiscal year.
3. Select industry class.
4. Save.

Expected result:

- Return dates align with fiscal year.
- Assessment rate is available.

### Test 4: Fetch Employee Data

Steps:

1. Submit payroll Salary Slips for the assessment period.
2. Open COIDA Annual Return.
3. Click `Fetch Employee Data`.

Expected result:

- Employee count is populated.
- Total annual earnings are populated.
- Director earnings populate where director employees are identifiable.

### Test 5: Assessment Fee Calculation

Steps:

1. Enter total annual earnings.
2. Enter assessment rate.
3. Save.

Expected result:

- Assessment fee equals annual earnings multiplied by assessment rate percentage.

### Test 6: Annual Return Submission Status

Steps:

1. Review annual return.
2. Submit.

Expected result:

- Status changes to Submitted.
- Submission date is captured where supported.

### Test 7: Workplace Injury Date Validation

Steps:

1. Create Workplace Injury with future injury date.
2. Try to save.

Expected result:

- Save is blocked.
- Practitioner must enter a valid injury date.

### Test 8: Workplace Injury With Leave Requirement

Steps:

1. Create Workplace Injury.
2. Set injury date and expected recovery date.
3. Mark leave as required.
4. Save.

Expected result:

- Leave days calculate from injury date to expected recovery date.
- If HRMS leave is configured, linked leave can be created on submit.

### Test 9: Workplace Injury Without HRMS Leave Dependency

Steps:

1. Create Workplace Injury on a site where leave automation is not available or not configured.
2. Mark leave as required.
3. Save.

Expected result:

- Injury record remains usable.
- Leave automation is skipped or clearly messaged.

### Test 10: OID Claim Creation

Steps:

1. Create Workplace Injury requiring a claim.
2. Submit or create OID Claim manually.

Expected result:

- OID Claim links to Workplace Injury.
- Employee, company, and injury details agree.

### Test 11: OID Claim Lifecycle

Steps:

1. Submit OID Claim.
2. Update status to Approved.
3. Enter compensation amount.
4. Update status to Paid.
5. Enter payment date.

Expected result:

- Claim status updates.
- Compensation amount and payment date save.
- Linked injury status updates according to claim progress.

### Test 12: OID Medical Report

Steps:

1. Open OID Claim.
2. Add OID Medical Report.
3. Save.

Expected result:

- Medical report is linked to the claim.
- Claim review evidence is available.

## Working Papers And Records To Review

SA COIDA currently uses working-paper DocTypes rather than script reports:

- COIDA Settings
- COIDA Industry Rate
- COIDA Annual Return
- Workplace Injury
- OID Claim
- OID Medical Report

Also review:

- Submitted Salary Slips for annual earnings.
- Employee records for director classification.
- General payroll reports where earnings reconciliation is required.

## Common Mistakes And Troubleshooting

- If employee data does not fetch, confirm Salary Slips are submitted and within the annual return period.
- If assessment fee is zero, confirm total earnings and assessment rate.
- If director earnings are missing, review Employee designation/classification.
- If OID Claim cannot save, check injury date, claim date, and linked employee.
- If leave automation does not run, confirm HRMS leave setup, leave type, approver, and employee leave allocation.
- If linked injury status does not update, review claim status and save the submitted claim update.

## Practitioner Responsibility

Practitioners must confirm COIDA registration details, Compensation Fund reference details, assessment rates, earnings values, director earnings, injury evidence, claim evidence, and final external submissions. ZA Local provides working papers and workflow tracking, not Compensation Fund filing or statutory certification.

