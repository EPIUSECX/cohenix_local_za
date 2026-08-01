# Testing Guide for ZA Local

ZA Local combines Frappe server tests, static/repository checks, and staged end-to-end payroll and statutory scenarios. Passing tests is necessary engineering evidence; it is not tax, payroll, banking, SARS, Compensation Fund, or legal signoff.

## Supported test baseline

- Frappe Framework, ERPNext and Frappe HR/HRMS v16
- Python 3.10 or later (the current CI job uses the version declared in its workflow)
- MariaDB and Redis services required by the bench
- A dedicated test site with the same app versions as the target deployment

Never run tests or E2E staging against a production site. Take a database/files backup before migration or destructive acceptance testing.

## Static checks

From the app directory:

```bash
ruff check .
git diff --check
```

## Server tests

Run the complete suite on a dedicated site:

```bash
bench --site za-local-e2e.test run-tests --app za_local --lightmode
```

Run a focused module while developing:

```bash
bench --site za-local-e2e.test run-tests \
  --app za_local \
  --module za_local.tests.test_statutory_workflow_regressions \
  --lightmode
```

The suite covers statutory calculations, document-controller behavior, permission gates, scheduler registration, setup/fixture integrity, repository hygiene, and selected workflow regressions. Tests that use mocks are not a substitute for the staged lifecycle scenarios below.

## Legacy seed-data validator

The read/validation helper checks payroll-period, salary-component, rebate, medical-credit, slab and CSV seed shapes:

```bash
bench --site za-local-e2e.test execute za_local.test_data_loading.run_all_tests
```

Review its output; do not treat a successful shape check as confirmation that current statutory values are legally correct.

## Disposable-site E2E staging

`za_local.tests.e2e_data` creates and submits test records and commits them. Its guard requires developer mode and a site name containing `e2e`. These commands are intentionally mutating and must only be used on a disposable site restored from a known snapshot.

Run the stages in dependency order:

```bash
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_foundation
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_payroll_masters
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_monthly_payroll
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_payroll_year_to_date
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_interim_statutory_reconciliation
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_coida_assessment
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_timesheet_payroll
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_vat_cycle
bench --site za-local-e2e.test execute za_local.tests.e2e_data.stage_eft_payment_batch
```

After each stage, verify the returned record names and inspect the documents in Desk. A failed or partial stage should be diagnosed on a restored snapshot rather than repeatedly applied to an unknown state.

## Manual acceptance matrix

### Migration and setup

1. Restore a recent production backup to staging.
2. Record app versions and current customizations.
3. Run `bench --site <staging> migrate`, build assets and clear cache in a maintenance window.
4. Review migration output and Error Log; verify custom fields, workspaces, statutory rate coverage and company-specific settings.
5. Run `ZA Local Setup` as System Manager only for deliberately selected data sets. Review warnings and the records created or updated.
6. Repeat the migration on the same staging snapshot to check idempotency before approving production deployment.

### Payroll

Verify ordinary monthly, timesheet/hourly, additional salary, recurring additional salary, retirement contribution, medical scheme credit, ETI, fringe benefit, leave/termination, loan repayment and back-dated scenarios. Reconcile Salary Slips, Payroll Entry, GL, Payroll Payable, EMP201, certificates and EMP501 working papers.

### Payments

Generate an FNB Online Banking Enterprise CSV only from a submitted Payroll Payment Batch. Confirm role access, private-file storage, source hash, employee bank details, control total and a low-value bank acceptance upload. ABSA, Nedbank and Standard Bank formats are not supported.

### VAT and sales

Test standard, zero-rated, exempt, mixed-rate, credit-note, debit-note, capital and import scenarios. Reconcile posted tax rows to VAT reports, GL and the VAT201 working paper. Verify the no-invoice/abridged/full-invoice thresholds on a ZAR basis and inspect every issued print format.

### COIDA and labour

Test the exact 1 March-to-February COIDA year, component classification, per-employee cap, company/class industry rate, injury-to-claim workflow, medical reports and role restrictions. Validate Employment Equity, WSP/ATR and labour outputs against source records and current external requirements.

### External filing and statutory review

ZA Local does not generate a SARS BRS payroll-import file or submit VAT201, EMP201, EMP501, IRP5/IT3(a), COIDA, WSP/ATR or Employment Equity returns to external authorities. Validate and capture working-paper figures through the approved external channel. Retain submission receipts and payment confirmations outside the app record as required by the employer's control framework.

## Release evidence

Retain:

- commit and app-version identifiers;
- backup/restore evidence and migration logs;
- static and server-test output;
- E2E scenario results and reconciliations;
- practitioner-approved statutory source references;
- sample print/PDF review evidence;
- bank acceptance evidence for FNB OBE CSV;
- role/permission test results; and
- documented unresolved limitations and go-live decision.

Re-run the relevant checks after changes to hooks, controllers, setup/migration, custom fields, permissions, statutory rate packs, reports, print formats, bank exports or seed data.
