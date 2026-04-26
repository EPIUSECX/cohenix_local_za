# South Africa COIDA Configuration and Testing

This guide documents the current `za_local` SA COIDA setup flow and the sandbox evidence captured on `development.cohenix`.

SA COIDA supports Compensation Fund setup records, industry assessment rates, annual return working papers, workplace injury recording, and OID claim tracking. It does not submit directly to the Compensation Fund.

## Statutory Context

- Employers submit annual Return of Earnings information to the Compensation Fund.
- The ROE assessment period runs from 1 March to the end of February.
- The return includes employer details, number of employees, nature of business, and employee earnings up to the applicable Compensation Fund maximum.
- The employer remains responsible for ensuring ROE data is accurate and complete.

Reference source:

- Department of Employment and Labour guide: https://www.labour.gov.za/DocumentCenter/Pages/COID_How_To_Submit_Earnings_Statements_to_the_Compensation_Fund.aspx

## Setup Flow

1. Confirm the company is configured and payroll salary slips are submitted for the assessment period.
2. Open `COIDA Settings`.
3. Capture:
   - COIDA Registration Number
   - Compensation Fund reference number
   - assessment year
   - submission deadline
4. Add one or more `COIDA Industry Rate` rows:
   - industry class
   - industry description
   - assessment rate percentage
5. Create `COIDA Annual Return` for the company, fiscal year, date range, and industry class.
6. Run `Fetch Employee Data`.
7. Review:
   - employee count
   - total annual earnings
   - director earnings
   - assessment rate
   - assessment fee
8. Submit the return once the working paper has been reviewed.
9. Capture workplace injuries as `Workplace Injury`.
10. If an injury requires a Compensation Fund claim, create or auto-create an `OID Claim`.
11. Add medical reports and update the OID claim through `Submitted`, `Approved`, and `Paid` as the claim progresses.

## Sandbox Evidence

The sandbox test configured company `Cohenix` for fiscal year `2026-2027`.

COIDA settings:

- Registration Number: `9900012345`
- Reference Number: `CF-SANDBOX-001`
- Assessment Year: `2026-2027`
- Industry class `8810`: Office administrative services at `0.72%`
- Industry class `9512`: Computer support services at `0.38%`

Annual return result:

- COIDA Annual Return: `COIDA-Cohenix-2026-2027`
- Status after submit: `Submitted`
- Employees fetched from submitted Salary Slips: `6`
- Total annual earnings: R5,483,500.00
- Director earnings: R1,110,000.00
- Assessment rate: `0.72%`
- Assessment fee: R39,481.20

Workplace injury and OID claim result:

- Workplace Injury: `INJ-HR-EMP-00005-2026-00002`
- OID Claim: `OID-HR-EMP-00005-2026-00003`
- Medical reports captured: `1`
- Claim status after lifecycle test: `Paid`
- Compensation amount: R3,500.00
- Payment date: `2026-04-20`
- Linked injury status after paid claim: `Closed`

## What Was Fixed During Testing

- `COIDA Industry Rate` validation now uses `assessment_rate`, matching the DocType field.
- `COIDA Settings` validation now uses numeric conversion for assessment rates.
- `Workplace Injury` now passes company and injury location into generated OID Claims.
- OID Claim lifecycle fields can now be updated after submission:
   - claim date
   - claim status
   - compensation amount
   - payment date
- Submitted COIDA Annual Returns now persist their lifecycle status as `Submitted`.

## Verification Commands

Compile COIDA code:

```bash
python -m compileall za_local/sa_coida
```

Run migration after metadata changes:

```bash
bench --site development.cohenix migrate
```

The sandbox staging script asserted:

- COIDA assessment fee equals annual earnings multiplied by the configured assessment rate.
- COIDA Annual Return status persists as `Submitted`.
- OID Claim can move to `Paid` after submission.
- Workplace Injury is linked to the generated OID Claim.

## Practitioner Notes

- COIDA rates and thresholds should be confirmed against current Compensation Fund notices before filing.
- `COIDA Annual Return` is a working-paper record. The supported process is prepare, review, and manually file through the Compensation Fund/eCOID process.
- Salary Slip data must be submitted in HRMS before `Fetch Employee Data` can produce a payroll-backed return.
- If HRMS leave features are available, workplace injury leave can be linked to Leave Applications; otherwise the injury and OID claim workflow remains usable without leave automation.
