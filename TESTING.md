# Testing Guide for ZA Local

This app uses a mix of Frappe server tests, repository hygiene checks, and targeted data-loading validation.

## Main Test Commands

Run the app test suite:

```bash
bench --site your-site.local run-tests --app za_local
```

Run the legacy data-loading validator:

```bash
bench --site your-site.local execute za_local.test_data_loading.run_all_tests
```

Run Ruff locally:

```bash
ruff check .
```

## What the Current Suite Covers

### Frappe server tests

- DocType metadata smoke tests for shipped localization DocTypes
- repository hygiene checks:
  - no active duplicate SA print-format JSON docs
  - no tracked `.pyc` or `.backup` artifacts in the app tree
  - standard JSON docs are syntactically valid
- guarded payroll journal-entry cleanup behavior

### Data-loading validation

`za_local.test_data_loading` still validates the seed data shape and loading assumptions for:

- payroll period data
- salary components and earnings components
- tax rebates and medical credits
- income tax slabs
- CSV-based master data inputs

## CI Expectations

The versioned GitHub Actions workflow is designed to:

- lint the repo with Ruff
- run server-side tests on ERPNext v15 and v16
- keep standard-doc and repository hygiene regressions visible in pull requests

## Manual UI Verification

After automated tests pass, verify the key admin flow in the Desk:

1. Open `SA Overview`
2. Confirm the onboarding checklist appears
3. Open `ZA Local Setup`
4. Review `South Africa VAT Settings`
5. Open `SA Payroll` and verify tax/payroll setup links
6. Confirm the in-app help page opens from the workspace

## When to Re-run Validation

Re-run the suite after changes to:

- `hooks.py`
- `sa_setup/install.py`
- `sa_setup/setup_wizard.py`
- custom fields or property setters
- workspace/sidebar/onboarding JSON
- print formats or standard docs
- payroll/VAT defaults and seed data

## Notes

- The setup wizard assumes a South-Africa-only site model.
- Active print formats are canonicalized under module-scoped standard-doc paths.
- Legacy root print-format JSONs are archived for reference and should not be reactivated as a second source of truth.

