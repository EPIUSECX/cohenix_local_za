# Statutory Rate Data

South African payroll depends on rates that change annually: PAYE brackets, rebates, medical tax credits, the UIF cap, the SDL rate, ETI bands, the reimbursive travel rate, the retirement-deduction cap, the COIDA earnings cap and the lump-sum tax tables.

## Two layers: the rate pack and the Desk records

`za_local` keeps rates in **date-effective statutory rate packs** — JSON files at `za_local/sa_setup/data/statutory_rates_<YYYY>.json`, one per tax year. The payroll engine (`za_local.utils.statutory_rates`) resolves the correct pack for each payroll date, so calculations always use the rates in force on that date rather than hard-coded numbers.

From these packs the app also seeds **Desk-reviewable records** so practitioners can see and audit the values:

- **Income Tax Slab** — PAYE brackets for the year.
- **Tax Rebates and Medical Tax Credit** — primary/secondary/tertiary rebates and medical scheme credits.
- **ETI Slab** — Employment Tax Incentive bands (first 12 months / second 12 months).
- **Travel Allowance Rate** — reimbursive rate per km and fixed-allowance inclusion.

## What to verify per tax year

1. **Income Tax Slab** — open the slab for the active year (e.g. `South Africa 2026-2027`). Confirm the bracket thresholds and rates and the effective-from date (1 March of the tax year).

2. **Tax Rebates and Medical Tax Credit** — confirm the primary/secondary/tertiary rebates and the main-member / first-dependant / additional-dependant medical credits for the year.

3. **ETI Slab** — confirm the first-12-months and second-12-months bands and amounts.

4. **Travel Allowance Rate** — confirm the reimbursive rate per km for the year.

5. **Rate pack resolves** — in the console, `get_rate_pack(<a date in the year>)["tax_year"]` returns the expected year.

## Linking the tax slab to employees

Each employee's **Salary Structure Assignment** carries an **Income Tax Slab** link. It must point at the slab for the tax year of the payroll period being processed. If you process across a tax-year boundary, create a new assignment from 1 March linked to the new year's slab. See [Salary Structures & Assignments](salary-structures).

## Prior tax years

The app ships rate packs for recent prior years as well, so back-dated calculations (a prior-year EMP501 or a re-issued IRP5) resolve instead of failing. Some annually-gazetted figures in prior-year packs are carried forward and flagged for verification in the pack's `verification_notes` — confirm those against the original SARS/Department of Employment & Labour notices before relying on historical recalculations.

## Rolling forward to a new year

When a new Budget is announced, add the new year's rate pack and supporting records. The full procedure is in [Annual Statutory Update](../reference-operations/annual-statutory-update).

## Next

Review the [SARS Payroll Codes](sars-payroll-codes) that drive IRP5 grouping.
