# South African Chart of Accounts - Setup Guide

## Overview

The South African Chart of Accounts is a complete accounting structure that includes all standard ERPNext accounts plus South African-specific tax accounts required for SARS compliance. The chart is automatically loaded during setup or can be loaded manually.

---

## How It Works

### Setup Process

The Chart of Accounts can be loaded in three ways:

#### 1. **Automatic Loading (Setup Wizard)**

**When**: During ERPNext's first-time setup wizard

**Process**:
1. User creates company and selects "South Africa" as country
2. ERPNext setup wizard completes
3. ZA Local setup wizard automatically runs
4. Chart of Accounts loads (if enabled in setup options)

**Location**: `za_local/setup/setup_wizard.py` → `setup_za_localization()`

**Behavior**:
- If company has **no accounts** → Loads **complete SA chart**
- If company **already has accounts** (standard chart) → Adds **only SA tax accounts** to existing structure

#### 2. **Manual Loading (ZA Local Setup)**

**When**: User manually runs ZA Local Setup

**Process**:
1. Navigate to: **Setup > ZA Local Setup > New**
2. Select company
3. Enable **"Load Chart of Accounts"** checkbox (enabled by default)
4. Click **Save**

**Location**: `za_local/setup/install.py` → `run_za_local_setup()`

**Behavior**: Same as automatic loading

#### 3. **Company Creation (Chart Selection)**

**When**: User creates company manually

**Process**:
1. Navigate to: **Accounting > Company > New**
2. Select "South Africa" as country
3. In Chart of Accounts dropdown, select **"South Africa - Standard Chart of Accounts"**
4. Save company

**Location**: ERPNext core → Chart discovery via `za_local/hooks.py`

**Behavior**: Loads complete SA chart when company is saved

---

## Chart Loading Logic

The system uses smart loading to avoid overwriting existing accounts:

```python
if company has 0 accounts:
    → Load complete SA Chart of Accounts
else:
    → Add only SA-specific tax accounts to existing chart
    → Creates parent groups if needed (Tax Liabilities, Tax Assets)
    → Skips accounts that already exist
```

**File**: `za_local/accounts/setup_chart.py` → `load_sa_chart_of_accounts()`

---

## File Locations

### Chart Definition
- **File**: `za_local/accounts/chart_of_accounts/za_south_africa_chart_template.json`
- **Purpose**: Complete Chart of Accounts structure in JSON format

### Setup Code
- **File**: `za_local/accounts/setup_chart.py`
- **Functions**:
  - `load_sa_chart_of_accounts()` - Main loading function
  - `_add_sa_tax_accounts()` - Adds tax accounts to existing chart
  - `_get_or_create_account()` - Creates accounts if they don't exist

### Integration Points
- **Setup Wizard**: `za_local/setup/setup_wizard.py` → `setup_za_localization()`
- **Manual Setup**: `za_local/setup/install.py` → `run_za_local_setup()`
- **Chart Discovery**: `za_local/hooks.py` → `extend_charts_for_country()`

### DocType Configuration
- **File**: `za_local/setup/doctype/za_local_setup/za_local_setup.json`
- **Field**: `load_chart_of_accounts` (Checkbox, default enabled)

---

## Accounts Included

### Standard ERPNext Accounts

#### Assets
- **Current Assets**:
  - Bank Accounts (group)
  - Cash In Hand → Cash
  - Accounts Receivable → Debtors
  - Stock Assets → Stock In Hand
  - Loans and Advances (Assets) → Employee Advances
  - Securities and Deposits → Earnest Money
  - Tax Assets (group) → VAT Paid - Purchases

- **Fixed Assets**:
  - Capital Equipment
  - Electronic Equipment
  - Furniture and Fixtures
  - Office Equipment
  - Plants and Machineries
  - Buildings
  - Software
  - Accumulated Depreciation
  - CWIP Account (Capital Work in Progress)

- **Other Assets**:
  - Investments (group)
  - Temporary Accounts → Temporary Opening

#### Liabilities
- **Current Liabilities**:
  - Accounts Payable → Creditors, Payroll Payable
  - Stock Liabilities → Stock Received But Not Billed, Asset Received But Not Billed
  - **Tax Liabilities** (group) → See SA-Specific Accounts below
  - Loans (Liabilities) → Secured Loans, Unsecured Loans, Bank Overdraft Account

- **Long Term Liabilities** (group)

#### Equity
- Share Capital
- Capital Stock
- Dividends Paid
- Opening Balance Equity
- Retained Earnings
- Revaluation Surplus
- Reserves (group)

#### Income
- **Direct Income**:
  - Sales
  - Service

- **Indirect Income** (group)

#### Expenses
- **Direct Expenses**:
  - Stock Expenses → Cost of Goods Sold, Expenses Included In Asset Valuation, Expenses Included In Valuation, Stock Adjustment

- **Indirect Expenses**:
  - Administrative Expenses (group)
  - Commission on Sales
  - Depreciation
  - Entertainment Expenses
  - Freight and Forwarding Charges
  - Legal Expenses
  - Marketing Expenses
  - Miscellaneous Expenses
  - Office Maintenance Expenses
  - Office Rent
  - Postal Expenses
  - Print and Stationery
  - Round Off
  - **Salary** (for salary expense tracking)
  - Sales Expenses (group)
  - Telephone Expenses
  - Travel Expenses
  - Utility Expenses
  - Write Off
  - Exchange Gain/Loss
  - Gain/Loss on Asset Disposal
  - Impairment

---

### South African-Specific Accounts

#### Tax Liabilities (Current Liabilities → Tax Liabilities)

**VAT Accounts**:
- **VAT Collected - Sales** (Output VAT)
  - Account Type: Tax
  - Purpose: VAT collected on sales (15% standard rate)

- **VAT Payable - SARS**
  - Account Type: Tax
  - Purpose: Net VAT owed to SARS (Output VAT - Input VAT)

**Payroll Tax Accounts**:
- **PAYE Payable - SARS**
  - Account Type: Tax
  - Purpose: PAYE deductions to be paid to SARS

- **UIF Employee Contribution**
  - Account Type: Tax
  - Purpose: UIF employee portion (1% capped at R177.12)

- **UIF Employer Contribution**
  - Account Type: Tax
  - Purpose: UIF employer portion (1% capped at R177.12)

- **SDL Payable - SARS**
  - Account Type: Tax
  - Purpose: Skills Development Levy (1% of gross pay)

**COIDA Account**:
- **COIDA Payable**
  - Account Type: Tax
  - Purpose: Compensation for Occupational Injuries and Diseases Act contributions

#### Tax Assets (Current Assets → Tax Assets)

- **VAT Paid - Purchases** (Input VAT)
  - Account Type: Tax
  - Purpose: VAT paid on purchases

---

## Account Usage

### For ERPNext Core
- All standard accounts for general accounting, inventory, fixed assets, etc.

### For Payroll (HRMS)
- **Payroll Payable** (under Accounts Payable) - Required for payroll payment processing
- **Salary** (under Indirect Expenses) - Required for salary expense tracking
- **PAYE Payable - SARS** - For PAYE deductions
- **UIF Employee Contribution** - For UIF employee deductions
- **UIF Employer Contribution** - For UIF employer contributions
- **SDL Payable - SARS** - For SDL contributions

### For VAT Compliance
- **VAT Collected - Sales** - Output VAT on sales
- **VAT Paid - Purchases** - Input VAT on purchases
- **VAT Payable - SARS** - Net VAT payable to SARS

### For COIDA Compliance
- **COIDA Payable** - For COIDA contributions

---

## Account Naming

The chart uses **South African-specific naming** aligned with SA laws and legislation:

- **"Tax Liabilities"** (not "Duties and Taxes") - SA accounting standard naming
- All tax accounts include **"SARS"** references where appropriate
- Account names match SA payroll and tax terminology

**Note**: The code supports both "Tax Liabilities" (SA naming) and "Duties and Taxes" (standard naming) for backward compatibility when adding tax accounts to existing standard charts.

---

## Verification

To verify the Chart of Accounts has loaded:

1. Navigate to: **Accounting > Chart of Accounts**
2. Filter by your company
3. Check for:
   - All standard account groups (Assets, Liabilities, Equity, Income, Expenses)
   - **Tax Liabilities** group under Current Liabilities
   - All SA tax accounts (VAT, PAYE, UIF, SDL, COIDA)
   - **Tax Assets** group under Current Assets
   - **VAT Paid - Purchases** under Tax Assets

---

## Troubleshooting

### Chart Not Loading
- Check that "Load Chart of Accounts" is enabled in ZA Local Setup
- Verify company country is set to "South Africa"
- Check if company already has accounts (chart will add tax accounts only)

### Missing Tax Accounts
- If standard chart was loaded first, tax accounts should be added automatically
- If missing, manually run ZA Local Setup again with "Load Chart of Accounts" enabled
- Or manually create accounts under Tax Liabilities / Tax Assets groups

### Account Naming Conflicts
- Code supports both "Tax Liabilities" and "Duties and Taxes" naming
- If standard chart uses "Duties and Taxes", tax accounts will be added there
- New companies will use "Tax Liabilities" (SA naming)

---

## Summary

- **Complete Chart**: Includes all standard ERPNext accounts plus SA-specific tax accounts
- **Smart Loading**: Full chart if empty, adds tax accounts if standard chart exists
- **SA-Specific Naming**: Uses "Tax Liabilities" and SARS references per SA legislation
- **All Required Accounts**: ERPNext, Payroll, HR, and SA compliance accounts included
- **Automatic**: Loads during setup wizard or can be loaded manually

