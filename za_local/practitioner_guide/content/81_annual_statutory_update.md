# Annual Statutory Update

South African rates change annually. This is the procedure to roll `za_local` forward to a new tax year. A normal year is data-only — adding JSON files and a holiday list, with no code changes. (The authoritative version ships in the app at `docs/annual_statutory_rate_update.md`.)

Remember: the tax year runs **1 March to end February**, and files are suffixed with the **year of assessment** (the calendar year the tax year ends).

## When to run

After the annual Budget (usually late February) and once SARS publishes the new PAYE tables, rebates, thresholds and Budget Tax Guide. Some figures are gazetted separately and on different dates — see the watch list.

## Step 1 — Add the statutory rate pack

The rate pack is the single source of truth for date-effective calculations.

1. Copy the latest `za_local/sa_setup/data/statutory_rates_<YYYY>.json` to the new year.
2. Update `tax_year`, `year_of_assessment`, `effective_from`, `effective_to`, `source_reference`, keep `is_active: 1`.
3. Update the values that changed; recompute each PAYE bracket's cumulative `base_tax` (= previous bracket's base + previous width × previous rate); `amount_over` equals the bracket's lower bound.

The loader globs `statutory_rates_*.json` and picks the pack whose effective window contains the payroll date — no registration step.

## Step 2 — Add supporting fixtures

In the same folder, add for the new year: `tax_slabs_<YYYY>.json`, `tax_rebates_<YYYY>.json`, `payroll_period_<YYYY>.json`, and `holiday_list_<YYYY>.json` (include any once-off public holidays). ETI slabs and travel rates seed automatically from the rate pack.

## Step 3 — Migrate, clear cache, verify

```bash
bench --site <site> migrate
bench --site <site> clear-cache
```

Then in the console confirm the new year resolves:

```python
from za_local.utils.statutory_rates import get_rate_pack
get_rate_pack("<a date in the new tax year>")["tax_year"]
```

Add a `test_sa_payroll_compliance_<YYYY>.py` (copy the latest) asserting the new year's headline values — the cheapest guard against a transcription error.

## Watch list — confirm each year

- PAYE brackets, rebates, thresholds (SARS Budget Tax Guide).
- Medical scheme tax credits.
- ETI band amounts and thresholds, **and their effective month**.
- UIF monthly remuneration cap.
- Prescribed reimbursive travel rate per km.
- Subsistence daily amounts.
- COIDA annual earnings cap (separate assessment-year cycle).
- Retirement lump-sum / severance tax tables.

## After updating

Update each employee's **Salary Structure Assignment** from 1 March to link the new year's **Income Tax Slab**, so PAYE uses the new brackets from the new tax year's first run.
