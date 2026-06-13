# Post-Install Verification

Run these checks immediately after installing (or migrating) so you start configuration on a known-good base. If any check fails, re-run `bench --site <site> migrate` and `bench --site <site> clear-cache`, then re-check.

## 1. The app and workspaces are present

- Open the Frappe desk. You should see an **SA Localisation** app tile.
- Confirm these workspaces exist in the sidebar: **SA Overview**, **SA VAT**, **SA Labour**, **SA COIDA**, and — only if HRMS is installed — **SA Payroll**.

## 2. Custom fields are applied

Spot-check a few standard DocTypes:

- **Company** → there should be a *South African Registration* section with VAT number, PAYE/UIF/SDL reference numbers, COIDA registration, SETA and bargaining council fields.
- **Customer** → a VAT vendor checkbox and company registration field.
- **Item Group** → an *Is Capital Goods* checkbox.
- With HRMS: **Employee** → South African Details, Tax Certificate and Employment Equity sections; **Salary Component** → SARS payroll code, payroll treatment, PAYE inclusion %, and UIF/SDL/COIDA applicability checkboxes.

If fields are missing, the custom-field sync did not complete — re-run `bench migrate`.

## 3. Print formats are installed

Go to **Print Format** list and filter by name "SA". You should see the SA invoice/order/note formats. With HRMS you also get the SA Salary Slip and IRP5 formats.

## 4. SARS payroll codes are seeded

Open the **SARS Payroll Code** list. It should contain income, deduction and employer-contribution codes (e.g. 3601, 4102, 4141). These drive IRP5 line grouping.

## 5. Statutory rate packs resolve (full suite)

The payroll engine reads date-effective rate packs from `za_local/sa_setup/data/statutory_rates_*.json`. To confirm the current tax year resolves, run:

```bash
bench --site <site> console
```

```python
from za_local.utils.statutory_rates import get_rate_pack
get_rate_pack(frappe.utils.today())["tax_year"]
```

It should print the active tax year (for example `2026-2027`). If it raises *"No South African statutory rate pack is configured"*, the pack for that date is missing — see [Annual Statutory Update](../reference-operations/annual-statutory-update).

## 6. ETI slabs and travel rates are seeded (full suite)

Open the **ETI Slab** and **Travel Allowance Rate** lists. Each configured tax year should have records, seeded from the statutory packs.

## Ready

With these checks passing, proceed to [Foundation Setup](../foundation-setup-both-tracks/company-registration).
