# SA Labour: SETA, Skills, EE & Travel

The **SA Labour** module covers skills development, Employment Equity reporting, sectoral wage references, bargaining-council context and business-trip management. It works in both tracks, though Employment Equity reports are most useful when employee data is captured (full suite).

## Master & reference data

| DocType | Purpose |
|---|---|
| **SETA** | Sector Education and Training Authorities. Linked from the Company. Seeded list available. |
| **Bargaining Council** | Sectoral bargaining councils, with industry-specific contributions. |
| **Industry Specific Contribution** | Sector contributions/levies tied to a bargaining council, with rate and effective dates. |
| **Sectoral Minimum Wage** | Minimum wage references by sector/role/category. |
| **Business Trip Settings** | Company-wide travel configuration (mileage rate, expense-claim types, auto-create expense claim). |
| **Business Trip Region** | Regions with daily and incidental allowance rates (seeded list available). |

Set the company's **SETA** and **Bargaining Council** on the Company record ([Company & SA Registration](../foundation-setup-both-tracks/company-registration)).

## Skills development (WSP / ATR)

For SETA skills reporting:

1. **Workplace Skills Plan (WSP)** — capture planned training for the year (interventions, planned learners, budget) against the fiscal year.
2. **Annual Training Report (ATR)** — capture training actually completed (learners, dates, spend).
3. **Skills Development Record** — record individual employee training interventions, including disability and B-BBEE support flags.

These support the mandatory and discretionary grant submissions to the SETA.

## Employment Equity reports

Driven by the employee's EE fields (race, gender, occupational level, disability):

| Report | Purpose |
|---|---|
| **EE Workforce Profile** | Workforce composition by race, gender, occupational level and disability. |
| **EEA2 Income Differentials** | Income differential analysis for EE compliance. |
| **EEA4 Employment Equity Plan** | Numerical targets and progress. |

Accurate [Employee EE fields](../full-suite-employees/employee-master) are the prerequisite for meaningful output.

## Business trips & travel

**Business Trip** captures an employee's travel: allowances by region and days, journeys (transport mode, distance, mileage at the configured rate), accommodation and other expenses, producing a grand total. With *auto-create expense claim* enabled in Business Trip Settings, an Expense Claim is generated and linked back to the trip. Mileage uses the configured per-kilometre rate (see [Payroll Prerequisites & Settings](../full-suite-payroll-foundations/payroll-prerequisites-settings)) or the Travel Allowance Rate from the statutory pack.

## Next

Configure the [SA COIDA](sa-coida) module if the employer is registered with the Compensation Fund.
