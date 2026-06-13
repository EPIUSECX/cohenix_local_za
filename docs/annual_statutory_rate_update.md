# Annual Statutory Rate Update Runbook

This runbook describes how to roll the `za_local` statutory rate data forward to a new South African tax year. Most rates are data-driven, so a normal year requires editing JSON files and adding a holiday list, with no code changes.

The SA tax year runs **1 March to the last day of February**. The "year of assessment" is the calendar year in which the tax year ends, e.g. the **2026-2027** tax year (1 March 2026 to 28 February 2027) has year of assessment **2027**, and its files are suffixed `_2027`.

## When to run

After National Treasury's annual Budget (usually late February) and once SARS publishes the new PAYE tables, rebates, thresholds and the updated Budget Tax Guide. Some figures are gazetted separately and on different dates (see "Watch list" below); confirm each before relying on it.

## Step 1 — Add the statutory rate pack (single source of truth)

The rate pack drives all date-effective calculations (PAYE, UIF, SDL, ETI, medical credits, travel, subsistence, retirement, COIDA, lump-sum tax).

1. Copy the most recent pack in `za_local/sa_setup/data/`, e.g. `statutory_rates_2027.json` → `statutory_rates_2028.json`.
2. Update the metadata block: `tax_year`, `year_of_assessment`, `effective_from`, `effective_to`, `source_reference`, and keep `is_active: 1`.
3. Update the values that changed (see the watch list). Leave structurally stable values as-is.
4. Recompute the PAYE `base_tax` (cumulative tax) for each bracket. For a bracket, `base_tax = base_tax_of_previous_bracket + (previous_bracket_width × previous_bracket_rate)`. The `amount_over` value equals the bracket's lower bound.

The loader (`za_local/utils/statutory_rates.py`) globs `statutory_rates_*.json` automatically and selects the pack whose `effective_from`/`effective_to` window contains the payroll date. No registration step is needed.

## Step 2 — Add the supporting fixtures

In the same `za_local/sa_setup/data/` directory, add the matching files for the new year (copy the previous year's file and adjust):

- `tax_slabs_<YYYY>.json` — Income Tax Slab for the year (used by the Desk-reviewable tax slab).
- `tax_rebates_<YYYY>.json` — rebates and medical tax credits for the `Tax Rebates and Medical Tax Credit` Single.
- `payroll_period_<YYYY>.json` — the payroll period dates.
- `holiday_list_<YYYY>.json` — South African public holidays for the calendar year(s) the tax year spans. **Check for any once-off public holidays declared for that year** (e.g. election days).

ETI slabs and travel allowance rates are seeded automatically from the rate pack on install/migrate (`seed_statutory_rate_packs` in `za_local/sa_setup/install.py`) — you do not maintain separate ETI/travel files.

## Step 3 — Clear the cache and verify

The rate pack loader is cached with `lru_cache`. On a running site the cache is cleared automatically by `seed_statutory_rate_packs` during `bench migrate`; if testing interactively, call `za_local.utils.statutory_rates.clear_rate_pack_cache()`.

Run the compliance tests:

```bash
bench --site <site> run-tests --module za_local.tests.test_sa_payroll_compliance_2027
bench --site <site> run-tests --module za_local.tests.test_sa_payroll_compliance_prior_years
```

Add a new `test_sa_payroll_compliance_<YYYY>.py` (copy the latest one) asserting the new year's headline values: primary rebate, UIF cap, a couple of PAYE bracket computations, the ETI band amounts, the COIDA cap, and JSON validity. This is the cheapest guard against a transcription error.

## Watch list — figures that change and must be confirmed each year

These are gazetted on varying dates and from different authorities. Do not assume they carried forward:

- **PAYE brackets, rebates, thresholds** — SARS Budget Tax Guide. (Note: brackets were *not* adjusted for 2024-2025 and 2025-2026.)
- **Medical scheme tax credits** — SARS.
- **ETI band amounts and thresholds** — gazetted via the Taxation Laws Amendment Act; the amounts increased from 1 April 2025. Confirm both the amounts and the effective month.
- **UIF monthly remuneration cap** — Department of Employment & Labour (held at R17,712 since June 2021, but verify).
- **Prescribed reimbursive travel rate per km** — SARS notice.
- **Subsistence allowance daily amounts** (incidental-only; meals and incidentals) — SARS notice.
- **COIDA annual earnings cap** — Department of Employment & Labour notice (separate assessment-year cycle).
- **Retirement lump-sum / severance tax tables** — change infrequently (last reset 1 March 2023); confirm the exemption and brackets.

## Note on backfilled prior-year packs

`statutory_rates_2025.json` (2024-2025) and `statutory_rates_2026.json` (2025-2026) were backfilled so prior-year recalculations resolve. Their PAYE brackets, rebates, thresholds and medical credits are sourced from the repo's vetted prior-year data; the annually-gazetted figures listed in each file's `verification_notes.verify_before_use` block were carried forward and should be confirmed against the original SARS/DEL gazettes before being relied upon for historical recalculation.
