# SA COIDA: Injuries, Claims & Annual Return

The **SA COIDA** module supports the Compensation for Occupational Injuries and Diseases Act: recording workplace injuries, managing OID claims, and producing the annual Return of Earnings (W.As.8) working paper with the per-employee earnings cap applied.

## 1. COIDA Settings

Open **COIDA Settings** (per company) and capture:

- **COIDA Registration Number** and **Compensation Fund reference**.
- **Assessment year** and **submission deadline**.
- **Industry rates** — in the *COIDA Industry Rate* table, the industry class/subclass and the **assessment rate** (per R100 of earnings) the Compensation Fund assigned.

The company's COIDA registration number can also be set on the [Company record](../foundation-setup-both-tracks/company-registration).

## 2. Workplace injuries

Record each incident in **Workplace Injury**: employee, injury date, type, location, description, expected recovery, and flags for whether leave is required, an OID claim is required, and medical attention was provided. Leave days can be tracked from here.

## 3. OID claims

Where a claim is warranted, create an **OID Claim** linked to the Workplace Injury: claim date, status (Pending, Submitted, Under Review, Approved, Rejected, Paid), compensation amount and payment date. Attach medical evidence via the **OID Medical Report** child records (practitioner, diagnosis, recovery estimate, costs). This gives you a complete claim file for the Compensation Fund.

## 4. COIDA Annual Return (Return of Earnings)

The annual return calculates the assessment on employee earnings for the assessment year (1 March to end February), capped per employee.

1. Go to **COIDA Annual Return → New**. Set the **Company** and the **assessment year / from–to dates**.
2. **Fetch earnings.** In the **full suite**, the return aggregates each employee's submitted salary-slip earnings for the year. In the **ERPNext-only track**, capture earnings figures manually.
3. **Per-employee cap.** Earnings are capped per employee at the COIDA annual earnings cap from the statutory rate pack (for example R688,000 for 2026-2027 — confirm the current cap), so high earners are limited correctly.
4. **Assessment.** The return computes the assessment = capped total earnings × the industry assessment rate.
5. **Review and file.** Check the employee count, capped earnings and director earnings, then export/print for submission to the Compensation Fund. `za_local` produces the working paper; submission is manual.

## Reconciliation

Cross-check the return's total earnings against the Payroll Register (full suite) for the assessment year, after the per-employee cap. Confirm the assessment rate matches the Compensation Fund's notice for the company's industry class.

## Next

See the [Reference & Operations](../reference-operations/custom-fields-reference) section for the custom-field reference, the annual update procedure, and troubleshooting.
