# South Africa Labour Configuration and Testing

This guide documents the current `za_local` SA Labour setup flow and the sandbox evidence captured on `development.cohenix`.

SA Labour is a practitioner support module for labour masters, travel/allowance working papers, skills planning, training records, sectoral wage references, and employment-equity reports. It does not submit WSP, ATR, or EE reports electronically to a SETA or the Department of Employment and Labour.

## Statutory Context

- The Department of Employment and Labour announced the 2026 National Minimum Wage as R30.23 per ordinary hour from 1 March 2026.
- The NMW flyer for 2026 gives monthly equivalents of R5,239.46 for a 40-hour week and R5,894.40 for a 45-hour week.
- SETAs approve Workplace Skills Plans and Annual Training Reports as part of skills development grant processes.
- Employment Equity reporting depends on correct employee demographic and occupational-level data.

Reference sources:

- Department announcement: https://www.labour.gov.za/Media-Desk/Media-Statements/Pages/Minister-of-Employment-and-Labour%2C-Meth-increases-the-statutory-National-Minimum-Wage-to-R30%2C23-per-hour.aspx
- 2026 NMW flyer: https://www.labour.gov.za/DocumentCenter/Publications/Basic%20Conditions%20of%20Employment/National%20Minimum%20Wage%20flyer%202026.pdf
- SETA guide: https://www.labour.gov.za/DocumentCenter/Pages/Basic-Guide-to-Sector-Education-and-Training-Authorities-%28SETAs%29.aspx
- Employment Equity reporting notice: https://www.labour.gov.za/department-of-employment-and-labour-calls-on-designated-employers-to-submit-their-annual-employment-equity-%28ee%29-reports-in

## Setup Flow

1. Confirm the company, fiscal year, employees, departments, and designations are correct in ERPNext/HRMS.
2. Populate the ZA employee custom fields used by labour reports:
   - `za_race`
   - `za_occupational_level`
   - `za_is_disabled`
3. Create or review `SETA` records for the company's sector.
4. Create or review `Bargaining Council` records where the employer falls under a council.
5. Configure `Business Trip Settings`:
   - mileage allowance rate
   - mileage expense claim type
   - meal expense claim type
   - incidental expense claim type
   - whether submitted business trips should create Expense Claims automatically
6. Configure `Business Trip Region` rows with local travel allowance and incidental rates.
7. Create `Sectoral Minimum Wage` reference rows for sectors and position categories.
8. Create `Industry Specific Contribution` rows for sector-specific provident fund, union, levy, or bargaining council deductions.
9. Capture `Workplace Skills Plan` rows before training is delivered.
10. Capture `Annual Training Report` rows after training is completed.
11. Capture `Skills Development Record` rows for employee-level training and B-BBEE skills-development evidence.
12. Run the Employment Equity reports and reconcile against employee master data:
   - `EE Workforce Profile`
   - `EEA2 Income Differentials`
   - `EEA4 Employment Equity Plan`

## Sandbox Evidence

The sandbox test configured company `Cohenix` for fiscal year `2026-2027`.

Master data staged:

- SETA: `Services SETA Sandbox`
- Bargaining Council: `Sandbox Services Bargaining Council`
- Industry Specific Contribution: `Sandbox Provident Fund Levy`
- Sectoral Minimum Wage reference: `Hospitality-General Worker-2026-03-01`
- Business Trip Regions: `Johannesburg`, `Durban`
- Employees updated with race, disability, occupational level, department, and designation values

Business Trip result:

- Business Trip: `BTR-2026-00002`
- Status after submit: `Submitted`
- Allowances: R1,400.00
- Incidentals: R150.00
- Mileage: R2,821.50
- Receipt claims: R3,200.00
- Accommodation: R2,400.00
- Other expenses: R180.00
- Grand total: R10,151.50

Skills and training results:

- Workplace Skills Plan budget: R147,000.00 across 3 planned interventions
- Annual Training Report actual spend: R94,000.00 across 3 completed interventions
- Skills Development Record BEE points: 25.83 for a disabled-learner training scenario

Employment Equity reports:

- `EE Workforce Profile`: 4 rows returned
- `EEA2 Income Differentials`: 5 rows returned
- `EEA4 Employment Equity Plan`: 4 rows returned

## What Was Fixed During Testing

- `Workplace Skills Plan` now points to the correct child table, `Wsp Training Detail`.
- WSP and ATR now calculate budget/spend from child rows and expose a `Prepared` status.
- ATR training rows now use ordinary fields instead of an accidental self-referencing table field.
- `Sectoral Minimum Wage` and `Industry Specific Contribution` now have deterministic autoname rules.
- Skills development records now validate dates, reject negative cost values, and calculate BEE points as a practitioner-support metric.
- Submitted Business Trips now persist their lifecycle status as `Submitted`.

## Verification Commands

Compile Labour code:

```bash
python -m compileall za_local/sa_labour
```

Run migration after metadata changes:

```bash
bench --site development.cohenix migrate
```

The sandbox staging script asserted:

- Business Trip total equals R10,151.50.
- WSP budget equals R147,000.00.
- ATR actual spend equals R94,000.00.
- Employment Equity reports return rows from the staged employee data.

## Practitioner Notes

- Keep statutory rates current. The sandbox sectoral minimum wage record is test data; practitioners should configure the applicable current statutory, sectoral, or bargaining-council rate.
- WSP and ATR are working-paper/supporting-record doctypes. They do not replace SETA portal submissions.
- Employment Equity reports depend entirely on the correctness of employee demographic and occupational-level fields.
- Business Trip expense-claim automation is optional. If enabled, ERPNext Expense Claim Types must exist before submission.
