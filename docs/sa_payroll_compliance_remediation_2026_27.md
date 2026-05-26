# SA Payroll Compliance Remediation Verification 2026/27

Validation date: 2026-05-26

Site: `development.cohenix`

App: `za_local` 3.4.2 on branch `version-16`, base commit `ccb8687` with local compliance remediation changes.

Compliance reference: `/workspace/South Africa Payroll Tax Guide 2026-27 (1).pdf`

## Confirmed Implementation

- Added a versioned `2026-2027` statutory rate pack with effective dates, source reference, and active flag.
- Added date-effective statutory lookup utilities for PAYE brackets, rebates, medical credits, UIF, SDL, ETI, travel allowance, retirement deduction caps, COIDA caps, and severance/lump-sum tax.
- Seeded 2026/27 ETI slabs and travel allowance rates from the statutory pack.
- Made setup/migrate idempotently seed statutory packs, SARS payroll codes, salary components, salary component classifications, and retirement fund types.
- Added Salary Component payroll treatment fields for SARS code mapping, PAYE inclusion, UIF, SDL, COIDA, reimbursement, and variable-pay treatment.
- Added default treatments for ordinary remuneration, PAYE, UIF, SDL, retirement funds, medical aid, overtime, commission, bonus, fixed travel allowance, reimbursive travel, reimbursements, severance, leave payout, and notice pay.
- Updated Salary Slip calculations to use classification-backed PAYE inclusion, UIF, SDL, COIDA, ETI, retirement cap, fixed travel, and reimbursive travel treatment.
- Updated final settlement handling to require a Tax Directive for severance/lump-sum payroll submission, use the 2026/27 lump-sum table, split final payslip components, and calculate UIF on normal termination remuneration.
- Updated COIDA annual return logic to aggregate by employee and apply the 2026/27 R688,000 annual earnings cap per employee.
- Hardened Payroll Entry state handling and removed broad `frappe.throw` suppression during salary slip creation.
- Hardened EMP201 PAYE aggregation to include ordinary PAYE and lump-sum/directive PAYE from submitted slips only.
- Hardened EMP501 submission readiness checks for employer references, EMP201 period coverage, IRP5 coverage, SARS code completeness, directive numbers, employee statutory readiness, and certificate internal totals.
- Kept direct SARS/eCOID electronic submission disabled. Records remain manual filing working papers.
- Updated repository hygiene expectations so `SA Overview` is not treated as a Workspace Sidebar fixture.
- Added practitioner annual update guidance.

## Confirmed Test Evidence

Commands run:

```sh
bench --site development.cohenix migrate
bench --site development.cohenix execute za_local.sa_setup.install.seed_statutory_rate_packs
bench --site development.cohenix execute za_local.sa_setup.install.seed_salary_component_classifications
bench --site development.cohenix run-tests --app za_local --module za_local.tests.test_sa_payroll_compliance_2027
bench --site development.cohenix run-tests --app za_local
```

Results:

- Migration completed successfully.
- Re-running statutory pack seeding completed without duplicate errors.
- Re-running salary component classification seeding completed without duplicate errors.
- Focused 2026/27 compliance tests passed: 8/8.
- Full `za_local` test suite passed: 73 unit tests and 8 repository-hygiene tests.

Database spot checks:

- Salary Component custom payroll treatment fields present: 7 expected fields.
- 2026/27 ETI slabs present and submitted: first 12 months and second 12 months.
- 2026/27 travel allowance rate present: R4.95/km reimbursive rate and 80% fixed allowance PAYE inclusion.
- Salary components with SA payroll classifications present.

## Previous Failures Addressed

| Previous failure | Remediation status |
|---|---|
| ETI 2026/27 missing or using old slabs | Fixed with rate pack lookup and 2026/27 ETI slab seeding. |
| R6,000 first-12-month ETI expected R1,125 but actual R0 | Fixed and covered by automated test. |
| Fixed travel allowance taxed at 100% by default | Fixed to 80% default PAYE inclusion, with override support. |
| Reimbursive travel treatment not protected | Fixed helper treats prescribed-rate travel as non-taxable when no fixed allowance applies. |
| UIF employee mismatch for prorated remuneration | Salary Slip statutory adjustment now recalculates employee and employer UIF from the same capped classified basis. |
| SDL and COIDA bases included non-taxable items | Bases now use component classifications and exclude non-taxable reimbursements. |
| COIDA annual cap missing | Fixed by employee-level annual cap aggregation. |
| Severance used placeholder tax logic | Replaced with 2026/27 lump-sum table support and directive requirement. |
| Final payslip unavailable from settlement | Implemented final Salary Slip generation with separate final-pay components. |
| Payroll Entry draft docstatus with Submitted status | Hardened save/submit/cancel status consistency and removed broad exception suppression. |
| Repository hygiene expected removed `sa_overview.json` fixture | Fixed hygiene tests to require only the active module workspace sidebars. |

## Confirmed Limits And Assumptions

- Direct SARS, EMP501 BRS XML, IRP5 bulk XML, and eCOID electronic submission remain unsupported by design in this pass.
- The implementation is manual filing-ready working-paper support, not automated statutory submission.
- Statutory rules outside the supplied 2026/27 guide are not inferred. They require practitioner confirmation before implementation.
- A new statutory pack must be added and signed off for each future tax year before March payroll is processed.

## Conclusion

Based on the supplied 2026/27 guide, migration success, idempotent seed checks, and passing automated compliance tests, the app is now manual filing-ready for the implemented South African payroll scenarios, subject to practitioner review and annual statutory pack updates.
