# Tax Directives & Final Settlements

Lump-sum payments — severance, retirement lump sums, and some leave payouts — are taxed under a separate SARS regime and usually require a **Tax Directive**. `za_local` supports this through the Tax Directive DocType and a structured final-settlement process.

## When a Tax Directive is needed

A SARS tax directive is required for lump-sum amounts such as severance/retrenchment benefits and retirement fund lump sums, and for certain other once-off payments. The directive tells you the exact tax to withhold, and its **directive number** must appear on the employee's IRP5.

## 1. Capture the Tax Directive

Apply for the directive on SARS eFiling, then record it in `za_local`:

1. Go to **Tax Directive → New**.
2. Set the **Employee**, **Company** and **directive type** (Severance, Leave Payout, Retirement Lump Sum, or Combination).
3. Enter the **directive number** and date issued by SARS.
4. Capture the directive amounts and the tax SARS specified.

## 2. Process the final settlement

When an employee leaves:

1. Use **Employee Separation** to drive the final-settlement salary slip where available.
2. The final pay is processed on a salary slip with the components **separated**: Notice Pay, Leave Payout, Severance Benefit, and Tax on Lump Sum.
3. Lump-sum tax is calculated using the **lump-sum benefit tax table** from the statutory rate pack (with the cumulative exemption applied). The severance component is treated per its SA payroll treatment (e.g. excluded from UIF/SDL).
4. The **Tax Directive number** is referenced so it carries through to the IRP5.

> Without a referenced Tax Directive, the EMP501 readiness checks will flag employees who received lump sums. Capture the directive before finalising year-end.

## 3. Leave encashment

For leave paid out outside a full termination, `za_local` provides a **Leave Encashment SA** process. Use it to process the leave payout with correct SA tax treatment, separate from the final-settlement flow.

## 4. Verify on the certificate

On the employee's [IRP5](irp5-it3), confirm the lump-sum income appears under the correct SARS code, the **directive number** is shown, and the tax matches the directive. Then include the certificate in the [EMP501](emp501).

## Checklist for a leaver

- [ ] Tax Directive obtained from SARS and captured.
- [ ] Final salary slip with separated notice pay / leave payout / severance / lump-sum tax.
- [ ] Lump-sum tax matches the directive.
- [ ] Employee status updated; last working day recorded.
- [ ] IRP5 generated with the directive number.

## Section complete

That completes the full-suite payroll lifecycle. Continue with the [SA Labour](../sa-labour-coida/sa-labour) and [SA COIDA](../sa-labour-coida/sa-coida) modules, or the [Reference & Operations](../reference-operations/custom-fields-reference) section.
