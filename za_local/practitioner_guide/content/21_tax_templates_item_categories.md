# Tax Templates & Item VAT Categories

This is where VAT actually gets applied to documents. You define reusable tax templates for sales and purchases, then classify items so the right rate is picked up automatically.

> **Shortcut:** the **Apply Recommended VAT Setup** action on [South Africa VAT Settings](vat-settings) creates the standard SA sales and purchase templates (and item tax templates) for you and maps them to the VAT201 classifications. Run it first, then use this page to understand, review and assign what it created — or to add templates for scenarios it doesn't cover.

## 1. Sales & Purchase Taxes and Charges Templates

Create ERPNext **Sales Taxes and Charges Template** and **Purchase Taxes and Charges Template** records for each VAT scenario you transact. Common templates:

**Sales:**

- Standard-rated local sales — 15% to VAT Output
- Zero-rated local sales — 0% (input still claimable upstream)
- Export (zero-rated) — 0%
- Exempt sales — 0%, non-creditable

**Purchases:**

- Standard-rated local purchases — 15% to VAT Input
- Capital goods purchases — 15% to VAT Input (classified as capital input on VAT201)
- Purchases with non-deductible VAT — special treatment / 0%

For each template set:

| Field | Value |
|---|---|
| Title | Descriptive, e.g. "RSA Standard Rated Sales 15%" |
| Company | The company |
| Tax row → Type | Actual (or On Net Total as appropriate) |
| Tax row → Account Head | VAT Output (sales) or VAT Input (purchases) |
| Tax row → Rate | 15 or 0 |

Set the most-used template as **Default** so it auto-applies on new documents.

## 2. Item VAT category / zero-rated handling

`za_local` keeps ERPNext's zero-rated item contract aligned with its VAT categories. On the **Item**, set the VAT treatment (standard, zero-rated, exempt, capital goods, imported goods, etc.) so the correct classification flows to invoices and the VAT201 return. When you change an item's VAT treatment, the app's `Item` validation syncs the zero-rated flag automatically.

On **Item Group**, the *Is Capital Goods* checkbox (added by `za_local`) marks groups whose purchases should be classified as **capital input** on the VAT201 — set this for asset/equipment item groups.

> Item Tax Templates can be used to override the document template at line level for mixed-rate items. Keep them consistent with the item's VAT category to avoid VAT201 "needs review" rows later.

## 3. Apply on transactions

When raising a Sales or Purchase Invoice, pick the matching tax template. The SA invoice controller calculates VAT and records the classification used by the VAT201 return. Use the SA print formats (next page) for compliant tax-invoice output.

## Next

Configure the [Customer & Supplier VAT Fields](customer-supplier-vat) that drive validation and vendor classification.
