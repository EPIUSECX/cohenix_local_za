# Employee Master & SA Details

The **Employee** record drives PAYE, ETI eligibility, the IRP5 certificate and Employment Equity reporting. `za_local` adds several South African sections to it. Capture these accurately — most downstream calculations and certificates read from here.

## 1. Employee Types

First create the **Employee Type** records you need (e.g. Permanent, Temporary, Contractor) so they can be selected on each employee.

## 2. Standard fields

For each **Employee** set the usual HRMS fields: name, company, department, designation, **date of joining**, and status.

## 3. South African Details

| Field | Why it matters |
|---|---|
| ID Number | 13-digit SA ID. Used on the IRP5 and for ETI age checks. |
| Employee Type | Link to the Employee Type. |
| Hours per Month | Used for **ETI** proration (e.g. 160 for full-time). |
| Special Economic Zone | Affects ETI eligibility where applicable. |
| Nationality | Country link. |
| Working Hours per Week | BCEA overtime context. |
| Has Children / Has Other Employments | Leave and PAYE-directive scenarios. |
| Number of Dependants | Drives the medical scheme tax credit. |
| Payroll Payable Bank Account | The bank account net pay is paid from/to. |

## 4. Tax Certificate section (for IRP5)

| Field | Notes |
|---|---|
| Identity Type | SA ID, Passport, Asylum Seeker, Permit, etc. |
| Income Tax Reference Number | The employee's SARS tax number (ITN). |
| Passport Country of Issue | If not on an SA ID. |
| Nature of Person | Individual, Director, Trust Beneficiary, Labour Broker, Personal Service Provider, Foreign Employee, etc. |
| Residential Address / Postal Address | Required on the IRP5. Capture in SA address format. |
| Not Paid Electronically | Tick if the employee is not paid by EFT. |
| Bank Account Type / Holder Name / Holder Relationship | For electronic payment and certificate banking details. |

## 5. Employment Equity section

For EE reporting (EEA2/EEA4) and skills development:

- **Race**, **Occupational Level**, **Is Disabled**, **Highest Qualification**.

These feed the Employment Equity reports in the [SA Labour](../sa-labour-coida/sa-labour) module. Capture them even if EE filing is not immediate — back-filling later is tedious.

## ETI eligibility at a glance

An employee typically qualifies for ETI when they: are **18–29** years old (from the ID number), have a valid **SA ID** (or qualifying SEZ status), have been employed **24 months or less** in the current job, and earn **below the ETI remuneration ceiling**. The salary-slip engine evaluates eligibility per month and computes the ETI from the ETI Slab; the *Hours per Month* field prorates it for part-month or part-time work.

## Verify before payroll

For each employee about to be paid, confirm: ID number, income tax reference number, a submitted **Salary Structure Assignment** with the correct Income Tax Slab, number of dependants (if on medical aid), and bank details. Missing data here is the most common cause of payroll and IRP5 errors.

## Next

You are ready to run payroll: [Payroll Entry & Salary Slips](../full-suite-running-payroll/payroll-entry-salary-slips).
