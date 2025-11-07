# Complete Implementation Guide - za_local for Frappe HR

**Last Updated**: November 7, 2025 (2025-2026 Tax Year)  
**Estimated Setup Time**: 15 minutes for basic setup, 2-4 hours for complete configuration with test data

---

## Table of Contents

1. [Introduction & Prerequisites](#1-introduction--prerequisites)
2. [Installation](#2-installation)
3. [Initial Company Setup](#3-initial-company-setup)
4. [Tax Configuration](#4-tax-configuration)
5. [Payroll Setup](#5-payroll-setup)
6. [Leave Management Setup](#6-leave-management-setup)
7. [Employment Equity Setup](#7-employment-equity-setup)
8. [Employee Configuration](#8-employee-configuration)
9. [Processing Monthly Payroll](#9-processing-monthly-payroll)
10. [Fringe Benefits Management](#10-fringe-benefits-management)
11. [Monthly Tax Compliance](#11-monthly-tax-compliance)
12. [Annual Tax Reconciliation](#12-annual-tax-reconciliation)
13. [Employment Equity Reporting](#13-employment-equity-reporting)
14. [Skills Development & BEE](#14-skills-development--bee)
15. [Employee Termination Workflow](#15-employee-termination-workflow)
16. [COIDA Management](#16-coida-management)
17. [VAT Management](#17-vat-management)
18. [Sectoral Compliance](#18-sectoral-compliance)
19. [Reports & Analytics](#19-reports--analytics)
20. [Advanced Features](#20-advanced-features)
21. [Common Workflows Quick Reference](#21-common-workflows-quick-reference)
22. [Troubleshooting & FAQs](#22-troubleshooting--faqs)
23. [Compliance Calendar](#23-compliance-calendar)
24. [Best Practices](#24-best-practices)
25. [Support & Resources](#25-support--resources)

---

## 1. Introduction & Prerequisites

### What is za_local?

**za_local** is a comprehensive South African localization application for Frappe HR and ERPNext that provides complete compliance with SARS, BCEA, Employment Equity Act, and Skills Development Act requirements.

### Who Should Use This Guide?

- **HR Managers** - Setting up and managing the entire HR system
- **Payroll Officers** - Processing monthly payroll and tax submissions
- **System Administrators** - Installing and configuring the application
- **Finance Managers** - Reconciling payroll and tax obligations

### What za_local Provides

✅ **SARS Tax Compliance**
- Automatic PAYE, UIF, SDL calculations
- ETI (Employment Tax Incentive) eligibility and calculations
- EMP201 monthly submissions
- EMP501 annual reconciliations
- IRP5 employee tax certificates
- Tax directive management
- UIF U19 declarations

✅ **BCEA Labour Law Compliance**
- 6 BCEA-compliant leave types
- 12 South African public holidays
- Notice period calculations (tenure-based)
- Severance pay calculations
- Leave payout on termination
- Medical certificate requirements

✅ **Employment Equity & BEE**
- Complete EE classification (race, disability, level)
- EEA2 Income Differentials reporting
- EEA4 Employment Equity Plan
- Workforce demographic profiles
- Skills Development tracking
- WSP/ATR submissions to SETA
- BEE points calculation

✅ **Advanced Features**
- Comprehensive fringe benefits (8 types)
- CO2-based company car taxation
- Employee termination workflows
- Final settlement calculations
- EFT file generation (4 banks)
- SARS XML exports (e-Filing)
- NAEDO debit orders
- Sectoral minimum wages
- Bargaining council compliance

### System Requirements

**Required:**
- Frappe Framework v14 or v15
- ERPNext v14 or v15 (installed)
- HRMS app v15 (installed)
- Python 3.10+
- MariaDB 10.3+

**Recommended:**
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- Ubuntu 20.04 or 22.04 LTS

### Estimated Setup Time

- **Basic Installation** (with integrated wizard): 15 minutes
- **Manual Configuration** (if needed): 1-2 hours
- **Complete Setup with Test Data**: 2-4 hours
- **First Live Payroll**: Allow 4-6 hours for verification

> 💡 **Quick setup tip**: The integrated setup wizard reduces initial setup time from 2-4 hours to just 15 minutes by automatically loading all essential defaults.

---

## 2. Installation

### Step 1: Get the Application

```bash
# Navigate to your bench directory
cd /path/to/frappe-bench

# Get za_local from your repository
bench get-app https://github.com/your-org/za_local.git

# Or if already downloaded
bench get-app /path/to/za_local
```

### Step 2: Install on Your Site

```bash
# Install the app on your site
bench --site your-site.local install-app za_local

# This will:
# - Create all DocTypes
# - Add custom fields to Employee, Company, etc.
# - Setup default configurations
# - Create 6 BCEA leave types
# - Load South African Holiday Lists (2024 and 2025)
# - Add the South Africa module with Tax & Compliance and Payroll workspaces to the sidebar navigation
```

### Step 3: Complete za_local Setup

za_local integrates into ERPNext's setup wizard. When you select **"South Africa"** as your country during ERPNext setup, the za_local setup page appears automatically.

**For initial installations:**
- Setup runs automatically after ERPNext wizard
- Select which defaults to load (all recommended enabled)
- Click Save to complete

**For Existing Installations:**
1. Navigate to: **Setup > ZA Local Setup > New**
2. Select your company
3. Choose which defaults to load:

**Recommended Selections:**
- ✅ Create Default Salary Components (PAYE, UIF, SDL, COIDA)
- ✅ Create Earnings Components (Basic, Housing, Transport, etc.)
- ✅ Load 2025-2026 Income Tax Slab (8 SARS brackets including 0% band)
- ✅ Load Tax Rebates & Medical Credits (with 2025-2026 Payroll Period)
- ✅ Load South African Holiday List (2024 and 2025)
- ✅ Load Business Trip Regions (16 regions with SARS-compliant rates)

**Optional Selections:**
- ⬜ Load SETA List (if using Skills Development)
- ⬜ Load Bargaining Councils (if applicable to your industry)

The setup loads:
1. ✅ Statutory salary components (PAYE, UIF, SDL)
2. ✅ Common earnings components (Basic Salary, allowances, bonuses)
3. ✅ 2024-2025 SARS tax brackets
4. ✅ South African Holiday Lists for 2024 and 2025 (12 public holidays per year)
4. ✅ Current tax rebates and medical credits
5. ✅ Business trip regions with SARS-compliant rates

### Step 4: Verify Installation

**Check 1: Custom Fields**
1. Navigate to **Employee** DocType
2. Scroll to confirm these tabs/sections are present:
   - SA Registration Details (ID Number, Employee Type)
   - Employment Equity Tab (Race, Disability, Occupational Level)
   - Travel Allowance section

**Check 2: Modules & Workspace**
- Verify the sidebar shows the updated module and workspaces:
- **South Africa** (module) with two workspaces:
  - **Tax & Compliance** – SARS filings, VAT, COIDA, and statutory tools
  - **Payroll** – Payroll configuration, benefits, travel, payments, and reports
- **SA Tax**
- **SA VAT**
- **COIDA**
- **SA EE** (Employment Equity)

> 💡 **Tip**: The **South Africa > Payroll** workspace provides quick access to all payroll configuration, transactions, benefits, business trips, payments, and reports. The **South Africa > Tax & Compliance** workspace groups EMP submissions, VAT, COIDA, and other statutory tools.

**Check 3: Leave Types**
1. Go to **HR > Leave Type**
2. Verify these exist:
   - Annual Leave (SA)
   - Sick Leave (SA)
   - Family Responsibility Leave (SA)
   - Maternity Leave (SA)
   - Study Leave (SA)
   - Unpaid Leave (SA)

**Success Indicator:** You should see a message: "✓ South African custom fields created successfully"

### Troubleshooting Installation

**Issue: Module not showing**
```bash
bench --site your-site.local clear-cache
bench restart
```

**Issue: Custom fields not appearing**
```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

**Issue: Permission errors**
```bash
bench --site your-site.local set-admin-password yourpassword
# Then re-login
```

---

## 3. Initial Company Setup

**Time Required:** 15-20 minutes

### Navigate to Company

1. Go to **Setup > Company**
2. Open your company record

### Configure Statutory Registration Numbers

#### PAYE Registration Number 
- **Field**: `tax_id`
- **Format**: 10 digits (e.g., 7000000000)
- **Where to find**: SARS eFiling profile or company SARS certificate
- **Example**: `7001234567`
> **Important**: This number is used for all EMP201, EMP501, and IRP5 submissions

Scroll to the **South African Registration Details** section and fill in:

#### UIF Reference Number
- **Field**: `za_uif_reference_number`
- **Format**: 8 or 9 digits
- **Where to find**: UIF registration certificate
- **Example**: `U12345678`

#### SDL Reference Number
- **Field**: `za_sdl_reference_number`  
- **Format**: Variable length
- **Where to find**: SETA registration or SARS
- **Example**: `SDL123456`

#### COIDA Registration Number
- **Field**: `za_coida_registration_number`
- **Format**: Variable length  
- **Where to find**: Compensation Fund certificate
- **Example**: `W012345678`
- **Note**: Only required if you have employees covered by COIDA

#### VAT Number (if registered)
- **Field**: `za_vat_number`
- **Format**: 10 digits (usually company registration + 3 digits)
- **Where to find**: SARS VAT registration certificate
- **Example**: `4123456789`
- **Note**: Only for VAT-registered companies

### Additional Configuration

#### SETA Selection
- **Field**: `za_seta`
- **Options**: Select your Skills Education Training Authority
- **Common SETAs**:
  - BANKSETA (Banking)
  - MICT SETA (ICT)
  - SERVICES SETA (General services)
  - W&R SETA (Wholesale & Retail)
  - CHIETA (Chemical Industries)
  - FOODBEV SETA (Food & Beverages)

> **Why this matters**: Required for WSP/ATR submissions and BEE compliance

#### Bargaining Council (if applicable)
- **Field**: `za_bargaining_council`
- **Type**: Link to Bargaining Council DocType
- **When needed**: If your company is registered with a bargaining council
- **Example**: Metal and Engineering Industries Bargaining Council

#### Sectoral Determination (if applicable)
- **Field**: `za_sectoral_determination`
- **Options**:
  - Domestic Workers
  - Farm Workers
  - Private Security
  - Hospitality
  - Wholesale/Retail
  - Other

> **Why this matters**: Determines minimum wage requirements and special contributions

### Save and Verify

Click **Save** and verify all registration numbers are correctly entered.

**Success Indicator:** No validation errors, all statutory numbers saved

---

## 4. Tax Configuration

**Time Required:** 30-45 minutes

> **⚠️ Important**:  
> Critical bug fixes were applied to tax rebate and medical credit calculations. The field names in the code now correctly match the DocType schemas:
> - Tax Rebates: Uses `tax_rebates_rate` table with `primary`, `secondary`, `tertiary` fields
> - Medical Credits: Uses `medical_tax_credit` table with `one_dependant`, `two_dependant`, `additional_dependant` fields
> 
> When updating an existing site, ensure you run `bench migrate` to apply these fixes.

### Step 1: Configure Tax Rebates and Medical Tax Credits

#### Navigate to Tax Rebates
1. Go to **Tax Rebates and Medical Tax Credit**
2. This is a Single DocType (only one record exists)
3. Click to open the existing record

#### Tax Rebates Configuration

The Tax Rebates and Medical Tax Credit DocType contains a **Tax Rebates Rate** child table with the following fields:

| Rebate Type | Field Name | 2025-2026 Value | Age Requirement |
|-------------|------------|-----------------|-----------------|
| Primary | `primary` | R17,235 | All taxpayers |
| Secondary | `secondary` | R9,444 | Age 65+ |
| Tertiary | `tertiary` | R3,145 | Age 75+ |

> **Important**: Rebates are **cumulative** - a 75-year-old receives Primary + Secondary + Tertiary = R29,824 total

**How to Configure:**
1. Open **Tax Rebates and Medical Tax Credit** (Single DocType)
2. In the **Tax Rebates Rate** table, add a row:
   - **Payroll Period**: 2025-2026
   - **Primary**: 17235
   - **Secondary**: 9444
   - **Tertiary**: 3145
3. **Save**

> **How it works**: System automatically calculates age from SA ID Number or Date of Birth

#### Medical Tax Credit Rates

Navigate to the **Medical Tax Credit** child table (note: NOT "Medical Tax Credit Rates"):

| Field Name | Description | Monthly Amount | Annual Amount |
|------------|-------------|----------------|---------------|
| `one_dependant` | Main Member Only | R364 | R4,368 |
| `two_dependant` | Main + First Dependant | R728 | R8,736 |
| `additional_dependant` | Each Additional | R246 | R2,952 |

**Configuration:**
1. In the **Medical Tax Credit** table (child table), click **Add Row**
2. **Payroll Period**: 2025-2026
3. **One Dependant**: 364
4. **Two Dependant**: 728
5. **Additional Dependant**: 246
6. **Save**


### Step 2: Setup ETI (Employment Tax Incentive) Slabs

#### Navigate to ETI Slab
1. Go to **SA Tax > ETI Slab**
-2. Click **Add ETI Slab**

#### Create First 12 Months ETI Slab

**Basic Details:**
- **Naming Series**: ETI-.YYYY.-.####.
- **Title**: "ETI 2025-2026 First 12 Months"
- **Start Date**: 2025-03-01
- **Minimum Age**: 18
- **Maximum Age**: 29
- **Hours in a Month**: 160

**ETI Slab Details Table:**

| From Amount | To Amount | ETI Amount | Percentage |
|-------------|-----------|------------|------------|
| 0 | 2,000 | 0 | 50% |
| 2,001 | 4,500 | 1,000 | 0% |
| 4,501 | 6,500 | 1,000 (declining) | -50% |
| 6,501 | 999,999 | 0 | 0% |

**Formula Explanation:**
- **R0 - R2,000**: ETI = 50% of monthly remuneration
- **R2,001 - R4,500**: ETI = R1,000 flat
- **R4,501 - R6,500**: ETI = R1,000 - (0.5 × (Remuneration - R4,500))
- **Above R6,500**: No ETI

#### Create Second 12 Months ETI Slab

**Basic Details:**
- **Title**: "ETI 2025-2026 Second 12 Months"
- **Start Date**: 2025-03-01
- **Minimum Age**: 18
- **Maximum Age**: 29
- **Hours in a Month**: 160

**ETI Slab Details Table:**

| From Amount | To Amount | ETI Amount | Percentage |
|-------------|-----------|------------|------------|
| 0 | 2,000 | 0 | 25% |
| 2,001 | 4,500 | 500 | 0% |
| 4,501 | 6,500 | 500 (declining) | -25% |
| 6,501 | 999,999 | 0 | 0% |

**Formula Explanation:**
- **R0 - R2,000**: ETI = 25% of monthly remuneration
- **R2,001 - R4,500**: ETI = R500 flat
- **R4,501 - R6,500**: ETI = R500 - (0.25 × (Remuneration - R4,500))
- **Above R6,500**: No ETI

### Step 3: Verify Tax Year Configuration

The system uses the South African tax year (March 1 to February 28/29). Verify:

1. **Income Tax Slab** DocType has current year rates
2. Tax year format: "South Africa 2025-2026"
3. Slabs are active (not disabled)
4. Effective from: 2025-03-01

**2025-2026 Tax Slabs** (SARS Gazetted Rates): https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/

| Taxable Income (Annual) | Rate | Tax Calculation |
|-------------------------|------|-----------------|
| **R0 - R95,750** | **0%** | **R0** (Tax threshold) |
| R95,751 - R237,100 | 18% | 18% of amount above R95,750 |
| R237,101 - R370,500 | 26% | R25,443 + 26% of amount above R237,100 |
| R370,501 - R512,800 | 31% | R60,127 + 31% of amount above R370,500 |
| R512,801 - R673,000 | 36% | R104,240 + 36% of amount above R512,800 |
| R673,001 - R857,900 | 39% | R161,912 + 39% of amount above R673,000 |
| R857,901 - R1,817,000 | 41% | R234,023 + 41% of amount above R857,900 |
| R1,817,001+ | 45% | R627,164 + 45% of amount above R1,817,000 |

**Tax-Free Thresholds** (after rebates):
- **Under age 65**: R95,750
- **Age 65-74**: R148,217
- **Age 75+**: R165,689

> **Note**: The 0% band from R0-R95,750 is included to account for the below 65 age threshold. Over age 65 and over age 75 calculation thresholds not currently catered for. 
> These are loaded automatically from `tax_slabs_2025.json`

### Success Indicator

- ✅ Tax rebates configured
- ✅ Medical tax credits set
- ✅ Both ETI slabs created (First 12 + Second 12 months)
- ✅ Tax slabs verified for current year

---

## 5. Payroll Setup

**Time Required:** 45-60 minutes

### Step 1: Verify Salary Components

The setup wizard creates these automatically, but verify they exist:

#### Navigate to Salary Components
Go to **Salary Payout > Salary Component**

#### Required Components

**1. PAYE (Pay As You Earn)**
- **Component Type**: Deduction
- **Is Tax Applicable**: No (it IS the tax)
- **Is Income Tax Component**: Yes (enable this flag)
- **Condition**: Always applies
- **Accounts**: Link to PAYE Payable account

**2. UIF (Unemployment Insurance Fund)**
- **Component Type**: Deduction  
- **Is Tax Applicable**: No
- **Rate**: 1% of gross (employee portion)
- **Max Amount**: R177.12 per month (1% of R17,712)
- **Condition**: `base <= 17712 ? base * 0.01 : 177.12`
- **Accounts**: Link to UIF Payable account

> **Important**: UIF has a maximum income threshold of R17,712/month

**3. UIF Employer Contribution**
- **Component Type**: Company Contribution
- **Rate**: 1% of gross (employer portion)
- **Max Amount**: R177.12 per month
- **Condition**: Same as employee UIF
- **Accounts**: Link to UIF Payable account

**4. SDL (Skills Development Levy)**
- **Component Type**: Company Contribution
- **Is Tax Applicable**: No
- **Rate**: 1% of gross salary
- **No Maximum**: Applies to full gross
- **Condition**: `base * 0.01`
- **Accounts**: Link to SDL Payable account

### Step 2: Configure Payroll Settings

#### Navigate to Payroll Settings
Go to **Payroll Settings**

#### South Africa Settings

**Calculate Annual Taxable Amount Based On:**
- Select: **Salary Payout > Payroll Period**
- Why: Ensures PAYE calculated on annual equivalent

**Disable ETI Calculation:**
- Leave unchecked (unless you don't qualify for ETI)

#### Link Salary Components

Scroll to **South African Statutory Components** section:

1. **PAYE Salary Component**: Select "PAYE"
2. **UIF Employee Salary Component**: Select "UIF Employee Contribution"
3. **UIF Employer Salary Component**: Select "UIF Employer Contribution"
4. **SDL Salary Component**: Select "SDL Contribution"
5. **COIDA Salary Component**: Select "COIDA" (if using)

### Step 3: Create Salary Structures

#### Navigate to Salary Structure
Go to **Salary Payout > Salary Structure**

#### Example: Standard Monthly Salary

**Basic Details:**
- **Name**: "SA Standard Monthly Salary"
- **Company**: Your company
- **Payroll Frequency**: Monthly
- **Is Active**: Yes

**Earnings Table:**

| Component | Condition | Amount Based On | Amount |
|-----------|-----------|-----------------|--------|
| Basic Salary | Always | Fixed Amount | (employee specific) |
| Housing Allowance | Optional | Fixed Amount | (employee specific) |
| Travel Allowance | Optional | Fixed Amount | (employee specific) |

**Deductions Table:**

| Component | Condition | Formula/Condition |
|-----------|-----------|-------------------|
| PAYE | Always | Automatic (system calculated) |
| UIF | Always | `gross_pay * 0.01 if gross_pay * 0.01 < 177.12 else 177.12` |
| SDL | Always | `gross_pay * 0.01` |
| Retirement Fund | If applicable | `base * 0.075` (example: 7.5%) |

**Company Contributions Table:**

Note: In HRMS with ZA Local, the Salary Structure includes a child table `company_contribution` (DocType: `Company Contribution`). Each row supports `Condition`, `Amount based on formula`, and `Formula`, mirroring Salary Component behavior.

Important: `Salary Component.type` includes a third option — `Company Contribution` — alongside `Earning` and `Deduction`. Use this type on Salary Components for UIF Employer, SDL, and similar employer-side items. UI filters in Salary Structure and reports use `type = "Company Contribution"` (not a legacy checkbox).

| Component | Condition | Formula |
|-----------|-----------|---------|
| UIF Employer | Always | `gross_pay * 0.01 if gross_pay * 0.01 < 177.12 else 177.12` |
| SDL | Always | `gross_pay * 0.01` |
| Retirement Fund Employer | If applicable | `base * 0.10` (example: 10%) |

> **Pro Tip**: Create multiple salary structures for different employee categories (monthly, weekly, executive, etc.)

### Step 4: Create Retirement Funds (if applicable)

#### Navigate to Retirement Fund
Go to **Retirement Fund**

The setup wizard creates defaults, but you can customize:

**Example: Company Pension Fund**
- **Fund Name**: "Company Pension Fund"
- **Fund Type**: Pension
- **Employee Contribution %**: 7.5%
- **Employer Contribution %**: 10.0%
- **Tax Deductible Limit**: 27.5% (of taxable income, max R350,000/year)
- **Fund Administrator**: (optional)
- **Policy Number**: (optional)



### Step 5: Setup Travel Allowance Rates

#### Navigate to Travel Allowance Rate
Go to **Travel Allowance Rate**

**SARS 2024 Rates:**

| Travel Type | Rate per KM | Taxable Portion |
|-------------|-------------|-----------------|
| Reimbursive | R4.25 | 0% (tax-free) |
| Fixed/Company Car | 80/20 split | 80% taxable |

**Create Rate Record:**
- **Effective From**: 2024-03-01
- **Reimbursive Rate per KM**: R4.25
- **Fixed Allowance Rate**: 0.80 (80% taxable)
- **Company**: Your company

> **How it works**: Reimbursive travel (with logbook) is tax-free. Fixed allowances are 80% taxable, 20% exempt.

### Success Indicator

- ✅ All 4 salary components verified (PAYE, UIF x2, SDL)
- ✅ Payroll Settings configured with linked components
- ✅ At least 1 Salary Structure created
- ✅ Retirement Fund(s) created (if applicable)
- ✅ Travel Allowance Rate configured

---

## 6. Leave Management Setup

**Time Required:** 20-30 minutes

The setup wizard automatically creates 6 BCEA-compliant leave types. This section covers verification and customization.

### Step 1: Verify BCEA Leave Types

#### Navigate to Leave Types
Go to **HR > Leave Type**

#### Verify These 6 Leave Types Exist:

**1. Annual Leave (SA)**
- **Max Leaves Allowed**: 21 days per year
- **Applicable After**: 1 month (as per BCEA)
- **Earned Leave**: Yes
- **Encashment**: Allowed on termination
- **Allow Negative**: No
- **Medical Certificate Required**: No

> **BCEA**: Employees entitled to 21 consecutive days per year or 1 day per 17 days worked

**2. Sick Leave (SA)**
- **Max Leaves Allowed**: 36 days per 3-year cycle
- **Applicable After**: 1 month
- **Allow Negative**: No
- **Medical Certificate Required After**: 2 days (customizable)
- **Consecutive Days**: 3 days per occasion without certificate

> **BCEA**: 6 weeks (36 days) sick leave in a 36-month cycle from date of employment. Allocate 36 days for a 3-year period starting from the employee's date of joining.

**3. Family Responsibility Leave (SA)**
- **Max Leaves Allowed**: 3 days per year
- **Applicable After**: 4 months
- **Allow Negative**: No
- **Applicable Gender**: All
- **Conditions**: 
  - When child is born
  - When child is sick
  - Death of spouse, parent, child, sibling

> **BCEA**: 3 days per year for employees working > 4 days/week for > 4 months

**4. Maternity Leave (SA)**
- **Max Leaves Allowed**: 120 days (4 months)
- **Applicable After**: Immediately
- **Allow Negative**: No
- **Applicable Gender**: Female
- **Encashment**: Not allowed
- **Consecutive**: Must be taken consecutively
- **When**: Can start 4 weeks before expected birth

> **BCEA**: 4 consecutive months maternity leave

**5. Study Leave (SA)**
- **Max Leaves Allowed**: Company policy (e.g., 5-10 days)
- **Applicable After**: 6 months (typical)
- **Allow Negative**: No
- **Encashment**: Not allowed
- **Condition**: For approved study/exam purposes

**6. Unpaid Leave (SA)**
- **Max Leaves Allowed**: Unlimited (company policy)
- **Is Unpaid Leave**: Yes
- **Allow Negative**: Yes (can go negative)
- **Applicable After**: Immediately
- **Impact**: No salary for days taken

### Step 2: Customize Leave Types (Optional)

For each leave type, you can customize:

#### Medical Certificate Requirements
1. Open **Sick Leave (SA)**
2. Set **`za_medical_certificate_required_after`**: 2 days
3. **Save**

> **How it works**: System will validate if medical certificate is attached for sick leave > 2 days

#### Gender-Specific Leave
1. **Maternity Leave**: Set **`za_applicable_gender`**: Female
2. **Paternity Leave** (if you create it): Set to Male

#### Leave Encashment
1. For **Annual Leave (SA)**
2. Check **Allow Encashment**
3. Set **Encashment Threshold Days**: 5 (don't allow encashing if < 5 days)

### Step 3: Setup SA Public Holidays

The setup wizard now loads Holiday Lists for both the current and next tax years (e.g., "South Africa 2024" and "South Africa 2025"), each with 12 public holidays.

#### Verify Holiday Lists
Go to **HR > Holiday List** and open:
- "South Africa 2024" (From: 2024-01-01, To: 2024-12-31)
- "South Africa 2025" (From: 2025-01-01, To: 2025-12-31)

Each list should contain these 12 holidays:

| Date | Holiday Name | Type |
|------|--------------|------|
| January 1 | New Year's Day | Fixed |
| March 21 | Human Rights Day | Fixed |
| April 19 | Good Friday | Variable (Easter-based) |
| April 22 | Family Day | Variable (Easter-based) |
| April 27 | Freedom Day | Fixed |
| May 1 | Workers' Day | Fixed |
| June 16 | Youth Day | Fixed |
| August 9 | National Women's Day | Fixed |
| September 24 | Heritage Day | Fixed |
| December 16 | Day of Reconciliation | Fixed |
| December 25 | Christmas Day | Fixed |
| December 26 | Day of Goodwill | Fixed |

> **Sunday Fallback**: If a public holiday falls on Sunday, it's observed on Monday

#### Verify for Current Year

1. Check that holidays are created for current year
2. Verify dates (especially Easter-based holidays)
3. If missing, re-run the ZA Local Setup wizard with "Load South African Holiday List" checked

### Step 4: (Optional) Customize Holiday Lists

If you need separate lists per site/region or weekly offs:

1. Go to **HR > Holiday List**
2. Duplicate "South Africa 2024" / "South Africa 2025"
3. Adjust weekly offs or add regional holidays
4. Assign in **Company > Default Holiday List**

### Step 5: Configure Leave Policies (Optional)

> **Note**: Leave Policy is a template/reference document only. It does NOT automatically create leave allocations. You must still create individual Leave Allocation documents for each employee (see Step 7 in Employee Configuration section).

#### Create Leave Policy
Go to **HR > Leave Policy**

**Example: Standard SA Leave Policy**
- **Policy Name**: "SA Standard Leave Policy"

**Leave Policy Grants Table:**

| Leave Type | Allocation | Effective After |
|------------|-----------|-----------------|
| Annual Leave (SA) | 21 days per year | 1 month |
| Sick Leave (SA) | 36 days per 3-year cycle | 1 month |
| Family Responsibility Leave (SA) | 3 days per year | 4 months |

> **BCEA Requirement**: Sick leave entitlement is **36 days over a 36-month (3-year) cycle** starting from the employee's date of joining. When creating Leave Allocation for each employee, use their date of joining as the From Date and 3 years later as the To Date.

### Success Indicator

- ✅ 6 BCEA leave types verified
- ✅ 12 SA public holidays created for current year
- ✅ Holiday List created and assigned to company
- ✅ Leave Policy created (optional)

---

## 7. Employment Equity Setup

**Time Required:** 15-20 minutes

### Step 1: Understanding EE Classifications

Employment Equity Act requires tracking employee demographics for reporting to the Department of Labour.

#### Navigate to Employee Custom Fields

The za_local app adds these fields to **Employee** DocType:

**Employment Equity Tab:**
- `za_race`: Race classification
- `za_is_disabled`: Disability indicator
- `za_disability_type`: Type of disability (if applicable)
- `za_is_foreign_national`: Foreign national indicator
- `za_occupational_level`: Job level classification

### Step 2: Race Categories

As per Employment Equity Act, employees are classified into:

| Code | Category | Description |
|------|----------|-------------|
| A | African | Black South Africans |
| C | Coloured | Mixed ancestry |
| I | Indian | Indian or Asian descent |
| W | White | White South Africans |
| O | Other | Foreign nationals or unspecified |

**Field**: `za_race`  
**Type**: Select dropdown  
**Required for**: EEA2, EEA4, and Workforce Profile reports

> **Important**: This data is confidential and used only for statutory EE reporting

### Step 3: Occupational Levels

As per EEA4 report format:

| Level | Description | Examples |
|-------|-------------|----------|
| Top Management | CEO, MD, Executive Directors | CEO, MD |
| Senior Management | Senior managers, GMs | GM, Senior Director |
| Professionally Qualified | Professionals, specialists | Doctors, Engineers, Accountants |
| Skilled Technical | Technicians, junior management | Team Leaders, Supervisors |
| Semi-Skilled | Clerks, sales, secretarial | Admin Clerks, Sales Reps |
| Unskilled | Labourers, cleaners | Cleaners, Messengers |
| Temporary Employees | Fixed-term, contract | Temporary staff |
| Non-Permanent | Contractors, consultants | Freelancers |

**Field**: `za_occupational_level`  
**Type**: Select dropdown  
**Required for**: EEA4 report

### Step 4: Configure Company SETA

#### Navigate to Company
Go to **Setup > Company** > Your company

**SETA Selection:**
- **Field**: `za_seta`
- **Options**: Dropdown of all SETAs

**Common SETAs:**
- **BANKSETA**: Banking sector
- **CHIETA**: Chemical industries
- **FOODBEV SETA**: Food and beverages
- **MICT SETA**: Media, IT, telecoms
- **SERVICES SETA**: Services sector
- **W&R SETA**: Wholesale and retail

> **Why this matters**: Required for WSP/ATR submissions and BEE reporting

**Save** the company record.

### Step 5: Enable EE Fields in Employee Form

When creating or editing employees, ensure these fields are filled:

1. **Navigate to**: Employee DocType
2. **Find tab**: "Employment Equity"
3. **Ensure visible**: All EE fields should be visible

If not visible:
1. Go to **Customize Form**
2. Search for Employee
3. Find EE fields
4. Ensure **Hidden** is unchecked
5. **Update**

### Step 6: Skills Development Tracking (Optional Setup)

For BEE compliance, you may want to track skills development:

#### Create Skills Development Categories

Common categories:
- Learnerships
- Bursaries
- Internships
- Skills Programmes
- Short Courses

This will be used when recording training in **Skills Development Record** DocType.

### Success Indicator

- ✅ EE custom fields verified on Employee DocType
- ✅ Race and Occupational Level dropdowns understood
- ✅ Company SETA configured
- ✅ Ready to classify employees for EE reporting

---

## 8. Employee Configuration

**Time Required:** 10-15 minutes per employee

### Step 1: Add an Employee Profile

#### Navigate to Employee
Go to **HR > Employee > Add**

### Step 2: Basic Information

**Standard HRMS Fields:**
1. **First Name**: Employee's first name
2. **Last Name**: Employee's surname
3. **Gender**: Male/Female/Other
4. **Date of Birth**: DD-MM-YYYY
5. **Date of Joining**: Employment start date
6. **Company**: Your company
7. **Department**: Employee's department
8. **Designation**: Job title
9. **Employment Type**: Permanent/Contract/Temporary

### Step 3: South African Specific Fields

#### SA Registration Section

**SA ID Number** (`za_id_number`)
- **Format**: 13 digits (YYMMDDGGGGSACZ)
- **Example**: 9001015009087
- **Validation**: System validates checksum
- **Purpose**: Used for PAYE, UIF, and ETI calculations

> **Pro Tip**: System auto-calculates date of birth and gender from ID number

**Employee Type** (`za_employee_type`)
- **Required**: Yes
- **Options**: Create Employee Type records first
- **Common types**:
  - Permanent Employee
  - Temporary Employee
  - Contract Employee
  - Part-Time Employee
  - Executive

**Hours Per Month** (for ETI pro-rating)
- **Field**: `za_hours_per_month`
- **Standard**: 160 hours (for monthly employees)
- **Part-time**: Actual hours worked
- **Purpose**: ETI pro-rating for part-time employees

#### Employment Equity Tab

**Race** (`za_race`)
- **Required for EE reporting**: Yes
- **Options**: African, Coloured, Indian, White, Other
- **Confidential**: Yes

**Disability** (`za_is_disabled`)
- **Type**: Checkbox
- **If checked**: Fill in `za_disability_type`
- **Purpose**: EE reporting and reasonable accommodation

**Occupational Level** (`za_occupational_level`)
- **Required for EEA4**: Yes
- **Options**: 8 levels (from Top Management to Non-Permanent)
- **Based on**: Job level and responsibilities

**Foreign National** (`za_is_foreign_national`)
- **Type**: Checkbox
- **When**: Employee is not SA citizen/resident
- **Impact**: Excluded from certain reports

### Step 4: Payroll Configuration

#### Bank Details Section

**Bank Account for Salary** (`za_payroll_payable_bank_account`)
- **Type**: Link to Bank Account DocType
- **Required**: Yes (for EFT payments)
- **Setup**: 
  1. Go to **Accounting > Bank Account > New**
  2. **Account Name**: Employee name
  3. **Account Type**: Employee
  4. **Bank**: Employee's bank
  5. **Branch Code**: 6 digits
  6. **Account Number**: Employee's account number
  7. **Account Type**: Savings/Cheque
  8. **Save** and link to employee

#### Retirement Fund

**Retirement Fund** (`za_retirement_fund`)
- **Type**: Link to Retirement Fund DocType
- **Required**: If participating in company fund
- **Contribution %**: Auto-set from fund, can override

> **Note**: Currently reference data only, does not affect calculation. Salary component requires adding with relevant percentage formula. 

#### Travel Allowance

**Travel Allowance Type** (`za_travel_allowance_type`)
- **Options**:
  - Reimbursive (with logbook) - Tax-free
  - Fixed Allowance - 80% taxable
  - Company Car - 80% taxable (CO2-based)
  - None

> **Note**: Currently reference data only, does not affect calculation. Salary component requires adding with relevant percentage formula. 

### Step 5: Configure Employee Private Benefits (Medical Aid Dependants and Retirement Fund)

**Purpose**: Track medical aid dependants for tax credit calculations and retirement fund participation for reference.

#### Navigate to Employee Private Benefit

1. From **Employee** form, click **Create > Employee Private Benefit**
2. OR search for "Employee Private Benefit" and create a record

#### What Affects Payroll vs What Doesn't

**✅ AFFECTS PAYROLL:**
- **Medical Aid Dependant** (`medical_aid_dependant`): Automatically reduces PAYE tax
  - Enter number of dependants (excluding main member)
  - Example: Employee + Spouse + 2 Children = enter **3**
  - Tax credit: 0 deps = R364/month, 1 dep = R728/month, 2+ deps = R728 + (R246 × additional)

**❌ DOES NOT AFFECT PAYROLL:**
- **Private Medical Aid** (`private_medical_aid`): Reference field only (not used in calculations)
- **Retirement Fund** (`retirement_fund`): Link to Retirement Fund master data (reference only)
- **Retirement Fund Contribution** (`annuity_amount`): Reference field only (doesn't add to payslip automatically)
  - Retirement fund deductions must be added manually as salary components in Salary Structure
  - Applies to all fund types: Pension Fund, Provident Fund, Retirement Annuity, or Preservation Fund

#### Quick Setup

1. **Employee**: Select employee
2. **Effective From**: Date when benefit starts
3. **Medical Aid Dependant**: Enter number (0 = main member only, 1 = + spouse, 2+ = + children)
4. **Retirement Fund**: (Optional) Select the retirement fund (Pension, Provident, Retirement Annuity, or Preservation Fund)
5. **Retirement Fund Contribution** (`annuity_amount`): (Optional) Enter monthly contribution amount
6. **Save** and **Submit**

> **Note**: Only the `medical_aid_dependant` field affects payroll calculations. All other fields are for reference/record-keeping only. The Retirement Fund link helps track which fund the employee is associated with (regardless of fund type), but contribution amounts must still be configured in Salary Structure.

### Step 6: Assign Salary Structure

#### Navigate to Salary Structure Assignment
1. From Employee form, click **Create > Salary Structure Assignment**
2. Or go to **Payroll > Salary Structure Assignment > New**

**Configuration:**
- **Employee**: Select the employee
- **Salary Structure**: Select structure (e.g., "SA Standard Monthly Salary")
- **From Date**: Effective date
- **Base**: Monthly base salary (e.g., R25,000)
- **Company**: Auto-filled from employee

**Earnings:**
- System auto-fills from salary structure
- Customize amounts if needed (e.g., housing allowance, travel allowance)

**Deductions:**
- PAYE: Calculated automatically
- UIF: Calculated automatically
- SDL: Calculated automatically
- Retirement Fund: Based on %

**Submit** the Salary Structure Assignment

### Step 7: Allocate Leaves

> **Important**: Leave allocations must be created individually for each employee. The dates are NOT automatically populated from Leave Policy. You must manually enter the dates based on each employee's date of joining.

#### From Employee Form:
Click **Create > Leave Allocation**

**For Annual Leave (SA):**
1. **Leave Type**: Select "Annual Leave (SA)"
2. **From Date**: Start of calendar year (e.g., 2024-01-01)
3. **To Date**: End of calendar year (e.g., 2024-12-31)
4. **Leaves Allocated**: 21 days
5. **Description**: "2024 Annual Leave Allocation"
6. **Submit**

**For Sick Leave (SA) - BCEA Compliant:**
1. **Leave Type**: Select "Sick Leave (SA)"
2. **From Date**: **Employee's date of joining** (check the Employee record - this is the key date!)
   - Example: If employee joined on 2024-01-15, use 2024-01-15
3. **To Date**: **Exactly 3 years (36 months) from date of joining**
   - Example: If date of joining is 2024-01-15, use 2027-01-14 (one day before 3-year anniversary)
   - Tip: Use date calculator or add 1095 days to date of joining
4. **Leaves Allocated**: 36 days
5. **Description**: "Sick Leave 3-Year Cycle (2024-01-15 to 2027-01-14)"
6. **Submit**

**For Family Responsibility Leave (SA):**
1. **Leave Type**: Select "Family Responsibility Leave (SA)"
2. **From Date**: Start of calendar year (e.g., 2024-01-01)
3. **To Date**: End of calendar year (e.g., 2024-12-31)
4. **Leaves Allocated**: 3 days
5. **Description**: "2024 Family Responsibility Leave"
6. **Submit**

> **How to Find Employee's Date of Joining**: 
> - Open the Employee record
> - Look for the **"Date of Joining"** field in the Basic Information section
> - Use this exact date as the **From Date** for the Sick Leave allocation
> - Calculate **To Date** as 3 years later (same date, 3 years forward)

### Step 8: Verify Employee Setup

**Checklist:**
- ✅ SA ID Number entered and validated
- ✅ Employee Type assigned
- ✅ Race and Occupational Level set (for EE)
- ✅ Bank Account linked
- ✅ Salary Structure Assignment created and submitted
- ✅ Leave allocations created
- ✅ Employee Private Benefit created (if medical aid or retirement fund applicable)
- ✅ Retirement Fund assigned (if applicable)

### Success Indicator

Navigate to Employee > Click **Dashboard**

You should see:
- Salary Structure Assignment (Active)
- Leave Balances showing
- Bank Account linked

---

## 9. Processing Monthly Payroll

**Time Required:** 1-2 hours (first time), 30-45 minutes (subsequent months)

### Complete Monthly Payroll Workflow

This is the most important process. Follow these steps carefully each month.

### Step 1: Pre-Payroll Checks (Day -2)

**Before creating payroll, verify:**

1. **All employees active**: Check Employee list, filter by Status = Active
2. **Salary Structure Assignments current**: No pending changes
3. **Leave applications submitted**: All approved leave for the period
4. **Additional salaries created**: Bonuses, allowances, deductions
5. **Tax directives active**: Any directives issued for the period
6. **Fringe benefits updated**: Company cars, housing, etc.

**Timesheet Check (if applicable):**
- Ensure all timesheets submitted and approved
- Project allocations correct

### Step 2: Create Payroll Entry

#### Navigate to Payroll Entry
Go to **Payroll > Payroll Entry > Add**

**Basic Details:**
1. **Company**: Your company
2. **Payroll Frequency**: Monthly
3. **Branch**: (optional) Select if processing for specific branch
4. **Department**: (optional) Select if processing for specific department

**Posting Details:**
1. **Posting Date**: Last day of month (e.g., 2024-01-31)
2. **Payment Account**: Bank account for salary payments

**Period:**
1. **Start Date**: First day of month (e.g., 2024-01-01)
2. **End Date**: Last day of month (e.g., 2024-01-31)
3. **Payroll Payable Account**: Salary Payable liability account
4. **Cost Center**: (optional) For cost allocation

**Save** (don't submit yet)

### Step 3: Get Employees

Click the **Get Employees** button

System will:
- Fetch all active employees
- Filter by selected branch/department (if specified)
- Show employee count
- Display in **Employees** table

**Verify:**
- Employee count matches expectation
- All expected employees in list
- No terminated employees included

### Step 4: Calculate Salary Slips

Click **Create Salary Slips** button

**What happens:**
- System creates individual salary slip for each employee
- Calculates PAYE based on:
  - Annual taxable income
  - Tax rebates (age-based)
  - Medical tax credits
  - Previous months' tax paid
- Calculates UIF (1%, capped at R177.12)
- Calculates SDL (1%)
- Calculates ETI (if eligible):
  - Age 18-29
  - Employment start date < 24 months ago
  - Remuneration within ETI brackets
- Applies fringe benefit taxation:
  - Company car (CO2-based)
  - Housing benefit
  - Low-interest loans
  - Other benefits

**Progress:**
- Shows progress bar
- "X salary slips created"

### Step 5: Review Salary Slips

**For each employee (or sample):**

1. Go to **Payroll > Salary Slip**
2. Filter by **Payroll Entry** = current month's entry
3. Open individual salary slips

**Review Earnings:**
- Basic Salary: Correct amount
- Allowances: Housing, travel, etc.
- Fringe Benefits: Company car, housing (taxable values)

**Review Deductions:**
- PAYE: Reasonable amount (check calculation)
- UIF: 1% of gross (max R177.12)
- SDL: 1% of gross
- Retirement Fund: Correct percentage
- Other deductions: Correct

**Review Company Contributions:**
- UIF Employer: 1% of gross (max R177.12)
- SDL Employer: 1% of gross
- Retirement Fund Employer: Correct percentage

**Review ETI (if applicable):**
- Check eligible employees (age 18-29, < 24 months)
- Verify ETI amount calculated correctly:
  - First 12 months: R500-R1,000
  - Second 12 months: R250-R500

> **Common Issues to Check:**
> - PAYE too high? Check if tax directives applied
> - UIF zero? Check if gross > R17,712
> - ETI zero? Verify age and employment start date

### Step 6: Apply Tax Directives (if any)

If employees have active tax directives:

1. **Tax Directive** DocType should be created and submitted
2. **Status**: Active
3. **Effective From/To**: Covers current payroll period
4. **Directive Type**: Reduced Tax Rate / Fixed Amount / Garnishee Order

**System automatically applies** tax directives during salary slip calculation.

**Verify:**
- Open salary slip for employee with tax directive
- Check PAYE reduced according to directive
- Check remarks showing directive applied

### Step 7: Make Manual Adjustments (if needed)

**For individual adjustments:**

1. Open salary slip
2. Click **Edit** (if not submitted)
3. Modify specific components:
   - Add earnings
   - Adjust deductions
   - Add one-time payments
4. **Save**

> **Warning**: Manual changes will be lost if you "Get Employees" again. Make changes BEFORE creating salary slips, using **Additional Salary** DocType.

### Step 8: Submit Payroll Entry

**Final Checks:**
1. All salary slips reviewed
2. Total gross pay matches budget
3. Total net pay reasonable
4. Bank account balance sufficient

**Submit Payroll Entry:**
1. Go back to Payroll Entry
2. Click **Submit**
3. Confirm submission

**What happens:**
- Payroll Entry locked
- Salary slips locked
- Journal entries created (if auto-posting enabled)

### Step 9: Generate Payroll Payment Batch

For EFT bank payments:

1. Go to **South Africa > Payroll > Payroll Payment Batch > Create**
2. **Payroll Entry**: Select current month's entry
3. **Payment Date**: Salary payment date (e.g., 25th of month)
4. **Bank Account**: Company bank account for payments
5. **Bank Format**: Standard Bank (or ABSA/FNB/Nedbank)
6. **Save**

Click **Generate EFT File** button

**System creates:**
- Fixed-width EFT file in selected bank format
- Header record with batch totals
- Beneficiary record for each employee
- Trailer record with totals

**Download File:**
- Click download link
- Save as: `EFT_PAYROLL-2024-01_20240125.txt`
- Upload to bank portal for processing

### Step 10: Post Journal Entries

**If auto-posting enabled:**
- Journal entries created automatically on Payroll Entry submission

**If manual posting:**

1. Go to **Accounting > Journal Entry > Create**
2. **Posting Date**: Last day of month
3. **Reference**: Payroll Entry name

**Accounting Entries Table:**

| Account | Debit | Credit | Cost Center |
|---------|-------|--------|-------------|
| Salary Expense | R250,000 | | Operations |
| PAYE Payable | | R45,000 | |
| UIF Payable (Employee) | | R2,000 | |
| UIF Payable (Employer) | R2,000 | R2,000 | |
| SDL Payable | R2,500 | R2,500 | |
| Retirement Fund Payable | | R15,000 | |
| Salary Payable | | R188,000 | |

> **Note**: Amounts are examples only

**Submit** Journal Entry

### Step 11: Generate EMP201 Submission

**For SARS monthly submission:**

1. Go to **SA Tax > EMP201 Submission > Create**
2. **Company**: Your company
3. **Period**: January 2024 (or current month)
4. **From Date**: 2024-01-01
5. **To Date**: 2024-01-31
6. **Save**

Click **Fetch from Salary Slips** button

**System calculates:**
- Total PAYE: Sum of all PAYE deductions
- Total UIF: Employee + Employer UIF
- Total SDL: Sum of SDL
- Total ETI: Sum of all ETI (reduces PAYE payable)

**Net Amount Payable to SARS** = PAYE + UIF + SDL - ETI

**Review and Submit:**
1. Verify totals match payroll
2. **Submit** EMP201 Submission
3. **Report** EMP201 Submission Report

**Payment to SARS:**
- **Due Date**: 7th of following month (e.g., February 7th)
- **Pay**: Net amount via SARS eFiling or bank

### Step 12: Pay Employees

**Using EFT file:**
1. Login to bank portal
2. Upload EFT file generated in Step 9
3. Verify batch totals
4. Authorize payment
5. Schedule for payment date

**Payment Date:**
- Typically 25th of month
- Or last working day of month
- Must be consistent with employment contracts

**Record Payment in ERPNext:**
1. Go to **Accounting > Payment Entry > Create**
2. **Payment Type**: Pay
3. **Party Type**: Employee (or bulk payment)
4. **Paid From**: Bank account
5. **Paid To**: Salary Payable
6. **Amount**: Total net pay
7. **Reference**: Payroll Entry name
8. **Submit**

### Success Indicator

**Completed Checklist:**
- ✅ Payroll Entry created and submitted
- ✅ All salary slips reviewed and accurate
- ✅ Tax directives applied (if any)
- ✅ Payroll Payment Batch created
- ✅ EFT file generated and uploaded to bank
- ✅ Journal entries posted
- ✅ EMP201 Submission created
- ✅ Employees paid on time
- ✅ SARS payment scheduled (by 7th of next month)

**Monthly Payroll Complete! 🎉**

---

## 10. Fringe Benefits Management

**Time Required:** 15-30 minutes per benefit

Fringe benefits are taxable perks provided to employees. za_local supports 8 types with automatic taxation.

### Step 1: Understanding Fringe Benefits

**What are Fringe Benefits?**
Non-cash benefits provided by employer that have taxable value per SARS rules.

**Supported Benefits:**
1. Company Car (CO2 emissions-based)
2. Housing (company-owned or rental)
3. Low-Interest Loans (below official rate)
4. Cellphone (private use portion)
5. Fuel Card (private kilometers)
6. Bursaries (employee or dependents)
7. Other custom benefits

### Step 2: Company Car Benefit

Most common and complex fringe benefit.

#### Navigate to Company Car Benefit
Go to **South Africa > Payroll > Company Car Benefit > Create**

**Basic Details:**
- **Employee**: Select employee
- **Company**: Auto-filled
- **Vehicle Registration**: XX-123-GP
- **Make and Model**: Toyota Corolla 1.6

**Vehicle Details:**
- **Purchase Date**: 2023-06-01
- **Purchase Price**: R350,000
- **Current Value**: R320,000

**CO2 Emissions (Critical for taxation):**
- **CO2 Emissions (g/km)**: 120 (from vehicle spec)
- **Emissions Category**: System calculates:
  - 0-120 g/km: 1.0x multiplier
  - 121-160 g/km: 1.25x multiplier
  - 161-200 g/km: 1.5x multiplier
  - 201+ g/km: 1.75x multiplier

**Period:**
- **From Date**: 2024-01-01
- **To Date**: 2024-12-31 (or leave blank for ongoing)

**Click Calculate** button

**Monthly Taxable Value Formula:**
```
Base Value = Purchase Price or Current Value (lower of two)
Monthly Value = (Base Value × 3.5%) ÷ 12
CO2 Multiplier = Based on emissions category
Taxable Value = Monthly Value × CO2 Multiplier
```

**Example:**
- Purchase Price: R350,000
- Current Value: R320,000 (use this - lower)
- Base calculation: R320,000 × 3.5% = R11,200/year
- Monthly: R11,200 ÷ 12 = R933
- CO2 Emissions: 120 g/km = 1.0x multiplier
- **Monthly Taxable Value: R933**

**Submit** the Company Car Benefit

**Integration with Payroll:**
- System automatically adds R933 to employee's taxable income
- Increases PAYE deduction
- Shows as "Company Car Benefit" in salary slip earnings

### Step 3: Housing Benefit

#### Navigate to Housing Benefit
Go to **South Africa > Payroll > Housing Benefit > Create**

**Basic Details:**
- **Employee**: Select employee
- **Property Address**: 123 Main Street, Johannesburg
- **Housing Type**: Company-owned / Rental

**Rental Details:**
- **Monthly Rental Value**: R15,000
- **Owned By**: Company / Third Party
- **Electricity Contribution**: R1,500 (if company pays)
- **Water Contribution**: R500 (if company pays)

**Click Calculate** button

**Monthly Taxable Value Formula:**
```
If Company-Owned:
  Taxable Value = Market Rental Value
  
If Rental (paid by company):
  Taxable Value = Rental Amount

Plus:
  + Electricity (if paid by company)
  + Water (if paid by company)
```

**Example:**
- Rental: R15,000
- Electricity: R1,500
- Water: R500
- **Monthly Taxable Value: R17,000**

**Submit** Housing Benefit

**SARS Rules:**
- Lower of: actual rent vs fair market rental
- Utilities add to taxable value if provided free

### Step 4: Low-Interest Loan Benefit

When company loans money to employee at rate below SARS official rate.

#### Navigate to Low Interest Loan Benefit
Go to **South Africa > Payroll > Low Interest Loan Benefit > Create**

**Loan Details:**
- **Employee**: Select employee
- **Loan Amount**: R100,000
- **Loan Start Date**: 2024-01-01
- **Interest Rate**: 5% (actual rate charged)
- **Official Interest Rate**: 10.25% (SARS prescribed rate)

**Click Calculate** button

**Monthly Interest Benefit Formula:**
```
Annual Benefit = (Official Rate - Actual Rate) × Loan Amount
Monthly Benefit = Annual Benefit ÷ 12
```

**Example:**
- Loan Amount: R100,000
- Official Rate: 10.25%
- Actual Rate: 5%
- Difference: 5.25%
- Annual Benefit: R100,000 × 5.25% = R5,250
- **Monthly Interest Benefit: R437.50**

**Submit** Low Interest Loan Benefit

### Step 5: Cellphone Benefit

#### Navigate to Cellphone Benefit
Go to **South Africa > Payroll > Cellphone Benefit > New**

**Cellphone Details:**
- **Employee**: Select employee
- **Device Make/Model**: iPhone 14 Pro
- **Contract Value**: R1,500/month
- **Business Use Percentage**: 60%
- **Private Use Percentage**: 40% (auto-calculated)

**Click Calculate** button

**Monthly Taxable Value Formula:**
```
Taxable Value = Contract Value × Private Use %
```

**Example:**
- Contract: R1,500/month
- Private Use: 40%
- **Monthly Taxable Value: R600**

**Submit** Cellphone Benefit

### Step 6: Fuel Card Benefit

#### Navigate to Fuel Card Benefit
Go to **South Africa > Payroll > Fuel Card Benefit > New**

**Fuel Card Details:**
- **Employee**: Select employee
- **Card Number**: 1234-5678-9012
- **Monthly Limit**: R5,000
- **Private KM per Month**: 500 km
- **Fuel Rate per Liter**: R23.50
- **Vehicle Fuel Consumption**: 7.5 L/100km

**Click Calculate** button

**Monthly Taxable Value Formula:**
```
Private Liters = (Private KM ÷ 100) × Consumption Rate
Private Cost = Private Liters × Fuel Rate per Liter
Taxable Value = Private Cost
```

**Example:**
- Private KM: 500 km
- Consumption: 7.5 L/100km
- Private Liters: (500 ÷ 100) × 7.5 = 37.5 liters
- Fuel Rate: R23.50/L
- **Monthly Taxable Value: R881.25**

**Submit** Fuel Card Benefit

### Step 7: Bursary Benefit

#### Navigate to Bursary Benefit
Go to **South Africa > Payroll > Bursary Benefit > New**

**Bursary Details:**
- **Employee**: Select employee
- **Beneficiary Type**: Employee / Dependent
- **Beneficiary Name**: (if dependent) Child's name
- **Institution**: University of Cape Town
- **Course Name**: Bachelor of Commerce
- **Academic Year**: 2024
- **Bursary Amount**: R60,000

**Tax Treatment:**
- **Employee bursaries**: Fully taxable
- **Dependent bursaries**: First R5,000/year tax-free, balance taxable

**Click Calculate Taxable Amount** button

**Example (Dependent):**
- Bursary Amount: R60,000
- Tax-Free Portion: R5,000
- **Taxable Amount: R55,000**
- **Monthly Taxable Value: R4,583**

**Submit** Bursary Benefit

### Step 8: Link Benefits to Employee

All benefits automatically link to employee via the `employee` field.

**View Employee's Benefits:**
1. Open Employee record
2. Scroll to **Connections** section
3. See all linked fringe benefits

### Step 9: Verify Benefits in Salary Slip

**Process payroll as normal** (see Section 9)

**In Salary Slip, verify:**
- **Earnings** section shows:
  - Company Car Benefit: R933
  - Housing Benefit: R17,000
  - Cellphone Benefit: R600
  - Fuel Card Benefit: R881
  - Low-Interest Loan Benefit: R438
  - Bursary Benefit: R4,583

**Total Fringe Benefits: R24,435** added to taxable income

**Impact on PAYE:**
- Gross Salary: R35,000
- Fringe Benefits: R24,435
- **Total Taxable Income: R59,435**
- PAYE calculated on R59,435 (higher tax)

### Success Indicator

- ✅ Fringe benefits created for applicable employees
- ✅ Monthly taxable values calculated correctly
- ✅ Benefits appear in salary slips
- ✅ PAYE increased appropriately
- ✅ Benefits tracked for IRP5 reporting

---

## 11. Monthly Tax Compliance

**Time Required:** 30-45 minutes per month

### Step 1: Create EMP201 Submission

**Due Date:** 7th of following month

#### Navigate to EMP201 Submission
Go to **SA Tax > EMP201 Submission > New**

**Period Details:**
- **Company**: Your company
- **Period**: Select month (e.g., "January 2024")
- **From Date**: First day of month (2024-01-01)
- **To Date**: Last day of month (2024-01-31)

**Save** (don't submit yet)

### Step 2: Fetch Data from Salary Slips

Click **Fetch from Salary Slips** button

**System automatically calculates:**

**Employee PAYE:**
- Sums all PAYE deductions from submitted salary slips
- **Example**: R45,000

**Employee UIF:**
- Sums all UIF deductions (1%, max R177.12 per employee)
- **Example**: R2,000

**Employer UIF:**
- Sums all UIF employer contributions (1%, max R177.12 per employee)
- **Example**: R2,000

**SDL:**
- Sums all SDL deductions/contributions (1% of gross)
- **Example**: R2,500

**ETI:**
- Sums all ETI amounts for eligible employees
- **Example**: R12,000 (reduces amount payable to SARS)

### Step 3: Review Totals

**EMP201 Summary:**

| Line Item | Description | Amount |
|-----------|-------------|--------|
| 1 | Employee's Tax (PAYE) | R45,000 |
| 2 | Employees' UIF Contributions | R2,000 |
| 3 | Employer's UIF Contributions | R2,000 |
| 4 | Skills Development Levy (SDL) | R2,500 |
| 5 | Employment Tax Incentive (ETI) | -R12,000 |
| **Total** | **Net Amount Payable** | **R39,500** |

**Verify:**
- Totals match payroll reports
- ETI applied as credit (reduces payment)
- No manual adjustments needed (usually)

### Step 4: Submit EMP201

1. Click **Submit** button
2. Confirm submission
3. **Status** changes to "Submitted"

**Document is now locked** and ready for SARS submission.

### Step 5: Pay SARS

**Payment Methods:**

**Option 1: SARS eFiling**
1. Login to [SARS eFiling](https://www.sarsefiling.co.za)
2. Go to **Returns > Employer Returns**
3. Select **EMP201 - Monthly**
4. Enter manually from EMP201 Submission:
   - Line 1: PAYE
   - Line 2: Employee UIF
   - Line 3: Employer UIF
   - Line 4: SDL
   - Line 5: ETI (as negative)
5. Submit return
6. Make payment via eFiling

**Option 2: Bank Payment**
1. Get SARS payment reference (from eFiling or SARS)
2. Use company bank account
3. Pay to SARS banking details
4. **Reference**: PAYE number + period (e.g., 7001234567-202401)

**Due Date:** 7th of following month (e.g., February 7th for January payroll)

**Late Payment Penalty:** 10% of amount due

### Step 6: Record Payment in System

1. Go to **Accounting > Payment Entry > New**
2. **Payment Type**: Pay
3. **Posting Date**: Payment date
4. **Party Type**: Supplier (or create "SARS" as supplier)
5. **Party**: SARS
6. **Paid To**: PAYE Payable (liability account)
7. **Paid From**: Bank Account
8. **Amount**: R39,500 (net payable)
9. **Reference Number**: SARS payment reference
10. **Submit**

### Step 7: Tax Directives Management

**What are Tax Directives?**
Official SARS instructions to adjust employee's PAYE deduction.

**Common Types:**
- Reduced tax rate (e.g., for multiple employers)
- Garnishee orders (court-ordered deductions)
- Fixed amount deductions

#### Create Tax Directive

1. Go to **SA Tax > Tax Directive > New**
2. **Employee**: Select employee
3. **Directive Number**: SARS reference number
4. **Directive Type**: Select type
5. **Effective From**: Start date
6. **Effective To**: End date
7. **Tax Rate Override**: (if applicable) New tax rate %
8. **Fixed Amount**: (if applicable) Monthly amount
9. **Attachment**: Upload SARS directive PDF
10. **Submit**

**How it Works:**
- System automatically checks for active tax directives during payroll
- Adjusts PAYE calculation according to directive
- Shows in salary slip remarks: "Tax Directive TD-2024-001 applied"

**Example:**
- Employee has second job
- SARS issues directive: "Reduce tax by 20%"
- Normal PAYE: R5,000
- With directive: R4,000
- **Saving**: R1,000/month

### Success Indicator

- ✅ EMP201 Submission created for each month
- ✅ Totals verified against payroll
- ✅ EMP201 submitted to SARS (via eFiling)
- ✅ SARS payment made by 7th of following month
- ✅ Payment recorded in accounting system
- ✅ Tax directives created and active (if applicable)

---

## 12. Annual Tax Reconciliation

**Time Required:** 4-6 hours (once per year)

**When:** 
- **IRP5 Generation**: April-May (for previous tax year ending February, due May 31)
- **EMP501 Interim**: September-October (for March-August period, due October 31)
- **EMP501 Final**: April-May (for full tax year March-February, due May 31)

### Step 1: Generate IRP5 Certificates

**What is IRP5?**
Annual employee tax certificate showing all income and deductions.

**Due Date:** May 31st (submit to SARS)

#### Single Employee IRP5

1. Go to **SA Tax > IRP5 Certificate > New**
2. **Employee**: Select employee
3. **Tax Year**: 2024-2025
4. **Period From**: 2024-03-01
5. **Period To**: 2025-02-28
6. **Company**: Your company
7. **Save**

Click **Generate from Salary Slips** button

**System calculates:**

**Income Section:**
- **Code 3701**: Remuneration (all gross salary)
- **Code 3702**: Travel allowance
- **Code 3703**: Reimbursive travel
- **Code 3810**: Commission
- **Code 3713**: Fringe benefits (company car, housing, etc.)

**Deductions Section:**
- **Code 4001**: Employee's tax (PAYE)
- **Code 4002**: UIF contributions
- **Code 4005**: Retirement fund contributions

**Company Contributions:**
- **Code 4006**: Medical aid employer contributions
- **Code 4116**: Retirement fund employer contributions

**Employer Details:**
- PAYE Number
- Company Name
- SDL Number
- UIF Reference

**Submit** IRP5 Certificate

#### Bulk Generate IRP5s

For all employees at once:

1. Go to **SA Tax > IRP5 Certificate**
2. Click **Menu > Bulk Generate IRP5s**
3. **Tax Year**: 2024-2025
4. **Company**: Your company
5. **Click Generate**

**System creates IRP5 for each employee** with salary slips in the period.

**Progress:**
- Shows progress: "Generating 1 of 50..."
- "50 IRP5 certificates generated successfully"

### Step 2: Review and Finalize IRP5s

**For each IRP5 (or sample):**

1. Open IRP5 Certificate
2. **Verify Employee Details:**
   - ID Number correct
   - Name and initials correct
   - Employment dates accurate

3. **Verify Income Totals:**
   - Total remuneration matches annual payroll
   - Fringe benefits correctly included
   - All allowances captured

4. **Verify Deductions:**
   - Total PAYE paid matches EMP201 submissions
   - UIF totals correct
   - Retirement fund contributions accurate

5. **Verify Company Contributions:**
   - Medical aid employer contributions
   - Retirement fund employer contributions

**Common Issues:**
- Missing months (employee started mid-year)
- Incorrect PAYE (check if tax directives applied)
- Fringe benefits not included (check if benefits created)

**Submit** each IRP5 after verification

### Step 3: Generate EMP501 Reconciliation

**What is EMP501?**
Annual reconciliation of all EMP201 submissions and IRP5 certificates.

**Due Dates:**
- **Interim**: October 31st (March 1 - August 31 period)
- **Final**: May 31st (March 1 - February 28/29, full tax year)

#### Create EMP501

**For Interim Reconciliation (March-August):**

1. Go to **SA Tax > EMP501 Reconciliation > New**
2. **Company**: Your company
3. **Tax Year**: 2024-2025
4. **Reconciliation Type**: Interim
5. **From Date**: 2024-03-01 (auto-populated)
6. **To Date**: 2024-08-31 (auto-populated)
7. **Save**

**For Final Reconciliation (Full Tax Year):**

1. Go to **SA Tax > EMP501 Reconciliation > New**
2. **Company**: Your company
3. **Tax Year**: 2024-2025
4. **Reconciliation Type**: Final
5. **From Date**: 2024-03-01 (auto-populated)
6. **To Date**: 2025-02-28 (auto-populated)
7. **Save**

Click **Fetch from EMP201 and IRP5** button

**System consolidates:**

**Part A: Consolidated EMP201 Submissions**
*(Note: EMP201 is submitted monthly. EMP501 reconciliations consolidate these monthly submissions.)*
- **For Interim EMP501**: Sums 6 monthly EMP201 submissions (March-August)
- **For Final EMP501**: Sums all 12 monthly EMP201 submissions (March-February)
- Total PAYE, UIF, SDL, ETI for the selected reconciliation period

**Part B: Consolidated IRP5 Certificates**
- **For Interim EMP501**: Sums IRP5 certificates for March-August period only
- **For Final EMP501**: Sums all IRP5 certificates for the full tax year
- Total remuneration, PAYE, UIF, retirement for the selected reconciliation period

**Reconciliation:**
- Compares Part A vs Part B
- Identifies discrepancies
- Calculates over/under payment

### Step 4: Review EMP501 Totals

**EMP501 Summary:**

| Description | EMP201 Total | IRP5 Total | Variance |
|-------------|--------------|------------|----------|
| Remuneration | R6,000,000 | R6,000,000 | R0 |
| PAYE | R900,000 | R900,000 | R0 |
| UIF (Employee) | R24,000 | R24,000 | R0 |
| UIF (Employer) | R24,000 | R24,000 | R0 |
| SDL | R60,000 | - | R0 |
| ETI | -R144,000 | - | R0 |

**Ideal Outcome:** Zero variance

**If Variance Exists:**
- Investigate cause (missing EMP201, incorrect IRP5, etc.)
- Make corrections
- Re-generate EMP501

### Step 5: Export EMP501 for SARS

**CSV Export Method:**

1. Open EMP501 Reconciliation (submitted)
2. Click **Export CSV** button
3. Download `EMP501_2024-2025_Company.csv`

**Or XML Export:**

1. Click **Generate XML** button
2. Download `EMP501_2024-2025_Company.xml`
3. XML includes all employee details and amounts

### Step 6: Submit to SARS eFiling

**Via SARS eFiling Portal:**

1. Login to [SARS eFiling](https://www.sarsefiling.co.za)
2. Go to **Returns > Employer Returns**
3. Select **EMP501 - Annual Reconciliation**
4. **Tax Year**: 2024-2025
5. **Upload CSV or XML** (or enter manually)
6. **Review totals** on SARS system
7. **Submit** return
8. **Receive acknowledgment** from SARS

**Or Bulk IRP5 Submission:**

1. In SARS eFiling
2. Go to **Employer Returns > IRP5/IT3(a) Bulk Submission**
3. **Upload XML** with all IRP5s
4. SARS processes bulk submission
5. Receive confirmation

### Step 7: Handle Discrepancies

**Common Discrepancies:**

**Issue 1: EMP201 total ≠ IRP5 total**
- **Cause**: Employee left mid-year, final payroll not included
- **Fix**: Create final salary slip, re-generate IRP5

**Issue 2: SARS shows different PAYE amount**
- **Cause**: Previous tax year adjustments
- **Fix**: Check prior year IRP5s, make correction submission

**Issue 3: ETI claimed but not approved by SARS**
- **Cause**: Employee doesn't meet eligibility criteria
- **Fix**: Review ETI logs, remove ineligible ETI, re-submit EMP501

### Success Indicator

- ✅ IRP5 certificates generated for all employees
- ✅ All IRP5s verified and submitted
- ✅ EMP501 reconciliation created
- ✅ Zero variance between EMP201 and IRP5 totals
- ✅ EMP501 Interim submitted to SARS (by October 31 for March-August period)
- ✅ EMP501 Final submitted to SARS (by May 31 for full tax year)
- ✅ SARS acknowledgment received
- ✅ No outstanding queries from SARS

**Annual Tax Reconciliation Complete! 🎉**

---

## 13. Employment Equity Reporting

**Time Required:** 2-3 hours (annually)

**When:** January (for previous year ending December 31)

**Due Date:** January 15th (to Department of Labour)

### Step 1: Ensure All Employees Classified

Before running EE reports, verify all employees have EE data:

#### Check Employee Classifications

1. Go to **HR > Employee**
2. Filter: **Status** = Active
3. For each employee, verify:
   - `za_race`: Set (African/Coloured/Indian/White/Other)
   - `za_is_disabled`: Set (checked if disabled)
   - `za_occupational_level`: Set (8 EEA categories)
   - `za_is_foreign_national`: Set (if applicable)

**If Missing:**
- Open employee record
- Navigate to **Employment Equity Tab**
- Fill in all required fields
- **Save**

> **Important**: Data is confidential and used only for statutory reporting

### Step 2: Run EEA2 Income Differentials Report

**What is EEA2?**
Report showing salary disparities across race and gender groups.

#### Navigate to Report
Go to **SA EE > Reports > EEA2 Income Differentials**

**Filters:**
- **Company**: Your company
- **Date**: 2024-12-31 (year-end date)
- **Department**: (optional) Specific department

Click **Run**

**Report Shows:**

| Occupational Level | Race | Gender | Avg Salary | Min Salary | Max Salary | Count |
|--------------------|------|--------|------------|------------|------------|-------|
| Top Management | African | Male | R150,000 | R120,000 | R180,000 | 2 |
| Top Management | White | Male | R160,000 | R140,000 | R180,000 | 3 |
| Senior Management | African | Female | R95,000 | R85,000 | R105,000 | 4 |
| ... | ... | ... | ... | ... | ... | ... |

**Analysis:**
- Identify pay gaps between race/gender groups at same level
- Highlight areas needing equity intervention
- Track progress year-over-year

**Export:**
- Click **Export** > **Excel**
- Save as: `EEA2_Income_Differentials_2024.xlsx`

### Step 3: Run EEA4 Employment Equity Plan Report

**What is EEA4?**
Workforce breakdown by occupational level, race, and gender.

#### Navigate to Report
Go to **SA EE > Reports > EEA4 Employment Equity Plan**

**Filters:**
- **Company**: Your company  
- **As on Date**: 2024-12-31
- **Include Foreign Nationals**: No (typically excluded)

Click **Run**

**Report Format (EEA4 Table):**

| Level | Male-A | Male-C | Male-I | Male-W | Female-A | Female-C | Female-I | Female-W | Total |
|-------|--------|--------|--------|--------|----------|----------|----------|----------|-------|
| Top Mgmt | 2 | 0 | 1 | 3 | 1 | 0 | 0 | 1 | 8 |
| Senior Mgmt | 5 | 2 | 3 | 8 | 4 | 1 | 2 | 5 | 30 |
| Professionally Qualified | 12 | 5 | 8 | 15 | 10 | 4 | 6 | 12 | 72 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **Total** | 45 | 20 | 25 | 60 | 38 | 15 | 20 | 45 | **268** |

**Legend:**
- A = African
- C = Coloured
- I = Indian
- W = White

**Shows:**
- Workforce demographic distribution
- Representation at each level
- Identifies under-represented groups

**Export:**
- Click **Export** > **Excel**
- Save as: `EEA4_Employment_Equity_Plan_2024.xlsx`

### Step 4: Run EE Workforce Profile Report

**What is this?**
Complete demographic snapshot of workforce.

#### Navigate to Report
Go to **SA EE > Reports > EE Workforce Profile**

**Filters:**
- **Company**: Your company
- **Date**: 2024-12-31

Click **Run**

**Report Shows:**

**By Race:**
- African: 83 (31%)
- Coloured: 35 (13%)
- Indian: 45 (17%)
- White: 105 (39%)
- **Total: 268**

**By Gender:**
- Male: 150 (56%)
- Female: 118 (44%)

**By Disability:**
- Disabled: 12 (4.5%)
- Non-Disabled: 256 (95.5%)

**By Occupational Level:**
- Top Management: 8 (3%)
- Senior Management: 30 (11%)
- Professionally Qualified: 72 (27%)
- Skilled Technical: 95 (35%)
- Semi-Skilled: 48 (18%)
- Unskilled: 15 (6%)

**Foreign Nationals:**
- South African: 253 (94%)
- Foreign: 15 (6%)

**Export:**
- Click **Export** > **PDF** (or Excel)
- Save as: `EE_Workforce_Profile_2024.pdf`

### Step 5: Prepare EEA Forms for Department of Labour

**Required Forms:**

**EEA2: Statement of Remuneration**
- Use data from EEA2 report
- Fill in official EEA2 form (from DoL)
- Show income differentials

**EEA4: Workforce Profile**
- Use data from EEA4 report
- Fill in official EEA4 form
- Show demographic breakdown

**EEA1: Cover Form**
- Company details
- BBBEE certificate status
- Contact person
- Reporting period

**EEA13: Consultation**
- Proof of consultation with employees/unions
- Meeting minutes
- Employee input on EE plan

### Step 6: Submit to Department of Labour

**Submission Methods:**

**Option 1: Online (Preferred)**
1. Visit [DoL Employment Equity Portal](https://www.labour.gov.za)
2. Register company (if first time)
3. Login with credentials
4. Navigate to **EE Reports**
5. Upload EEA1, EEA2, EEA4, EEA13
6. Submit electronically
7. Receive acknowledgment reference

**Option 2: Manual Submission**
1. Print all completed forms
2. Sign and date
3. Mail to:
   ```
   The Director-General
   Department of Employment and Labour
   Private Bag X117
   Pretoria, 0001
   ```
4. Or hand-deliver to nearest Labour Centre

**Due Date:** January 15th (for period ending December 31)

### Step 7: Develop Employment Equity Plan

Based on reports, create action plan:

**Identify Gaps:**
- Under-represented groups at senior levels
- Pay disparities between race/gender groups
- Low representation of people with disabilities

**Set Targets:**
- Increase African representation in senior management by 10%
- Achieve 50% female representation in professionally qualified roles
- Recruit 2% people with disabilities

**Interventions:**
- Targeted recruitment programs
- Skills development for under-represented groups
- Mentorship programs
- Reasonable accommodation for disabilities

**Document in EEA Plan**

### Success Indicator

- ✅ All employees classified with race, gender, disability, level
- ✅ EEA2 Income Differentials report generated
- ✅ EEA4 Employment Equity Plan report generated
- ✅ EE Workforce Profile report generated
- ✅ Official EEA forms completed (EEA1, EEA2, EEA4, EEA13)
- ✅ Submitted to Department of Labour by January 15
- ✅ Acknowledgment received from DoL
- ✅ Employment Equity Plan updated for new year

---

## 14. Skills Development & BEE

**Time Required:** 3-4 hours (annually for WSP/ATR)

**When:** WSP due April 30, ATR due April 30 (following year)

### Step 1: Record Skills Development Activities

Throughout the year, track all training:

#### Navigate to Skills Development Record
Go to **SA EE > Skills Development Record > New**

**For Each Training Event:**

**Training Details:**
- **Employee**: Select employee
- **Training Type**: Select
  - Learnership
  - Apprenticeship
  - Skills Programme
  - Short Course
  - Bursary
  - Internship
  - Other
- **Training Provider**: Name of institution/provider
- **Course Name**: e.g., "Advanced Excel"
- **NQF Level**: 1-10 (if applicable)

**Period:**
- **Start Date**: 2024-06-01
- **End Date**: 2024-06-03 (3-day course)
- **Status**: Planned / In Progress / Completed / Cancelled

**Cost Details:**
- **Training Cost**: R5,000
- **Paid By**: Company / Employee / Bursary
- **Cost Center**: Training & Development

**BEE Classification:**
- **Race**: Auto-filled from employee
- **Gender**: Auto-filled from employee
- **Disability**: Auto-filled from employee
- **Type of Beneficiary**: Employee / Unemployed / Other

**Save and Submit**

**Repeat** for every training event throughout the year.

### Step 2: Prepare Workplace Skills Plan (WSP)

**What is WSP?**
Annual plan submitted to SETA outlining planned training for upcoming year.

**Due Date:** April 30th (for upcoming financial year)

#### Navigate to Workplace Skills Plan
Go to **SA EE > Workplace Skills Plan > New**

**Plan Details:**
- **Company**: Your company
- **SETA**: Auto-filled from company (e.g., MICT SETA)
- **Plan Year**: 2025 (upcoming year)
- **From Date**: 2025-04-01
- **To Date**: 2026-03-31
- **Status**: Draft

**WSP Training Details Table:**

For each planned training:

| Employee/Group | Course | NQF Level | Type | Start Date | Duration | Cost | Beneficiaries |
|----------------|--------|-----------|------|------------|----------|------|---------------|
| IT Department | Cisco CCNA | 5 | Skills Programme | 2025-06-01 | 3 months | R80,000 | 5 |
| Sales Team | Sales Techniques | 3 | Short Course | 2025-07-15 | 5 days | R25,000 | 10 |
| Interns | Graduate Programme | 6 | Learnership | 2025-01-01 | 12 months | R150,000 | 3 |

**Totals:**
- **Total Planned Training**: R255,000
- **Total Beneficiaries**: 18
- **Percentage of Payroll**: 1.2%

> **BEE Requirement**: Skills development spend should be minimum 1% of payroll for B-BBEE Level 4 or higher

**Consultation:**
- Checkbox: "Consulted with employees/union"
- Attach: Meeting minutes or consultation record

**Submit** for internal approval

### Step 3: Submit WSP to SETA

**Submission Process:**

**Option 1: SETA Online Portal**
1. Visit your SETA's website (e.g., www.mict seta.org.za)
2. Login with company credentials
3. Navigate to **WSP Submission**
4. Fill in online form or upload CSV
5. Submit electronically
6. Receive acknowledgment

**Option 2: Manual Submission**
1. Export WSP to PDF
2. Print and sign
3. Submit to SETA office
4. Request receipt stamp

**Grants Available:**
- **Mandatory Grant**: 20% of SDL paid (for compliant submissions)
- **Discretionary Grant**: Available for specific projects (apply separately)

**Example:**
- SDL Paid: R30,000
- Mandatory Grant (20%): R6,000
- Can use for skills development

### Step 4: Track Training Completion

Throughout the year:

1. Update Skills Development Records with **Status**: "Completed"
2. Attach certificates
3. Record actual costs
4. Note any deviations from plan

### Step 5: Prepare Annual Training Report (ATR)

**What is ATR?**
Report on actual training completed in past year (retrospective).

**Due Date:** April 30th (for previous financial year)

#### Navigate to Annual Training Report
Go to **SA EE > Annual Training Report > New**

**Report Details:**
- **Company**: Your company
- **SETA**: Auto-filled from company
- **Report Year**: 2024 (previous year)
- **From Date**: 2024-04-01
- **To Date**: 2025-03-31
- **Status**: Draft

Click **Fetch Completed Training** button

**System pulls all Skills Development Records with:**
- Status: Completed
- End Date within report period
- Automatically populates ATR Training Completed table

**ATR Training Completed Table:**

| Employee | Course | NQF Level | Type | Completed Date | Cost | Race | Gender | Disability |
|----------|--------|-----------|------|----------------|------|------|--------|------------|
| John Doe | Excel Advanced | 4 | Short Course | 2024-06-03 | R5,000 | African | Male | No |
| Jane Smith | Leadership | 5 | Skills Programme | 2024-09-15 | R15,000 | Coloured | Female | No |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Summary Totals:**
- **Total Training Spend**: R320,000
- **Total Employees Trained**: 45
- **Percentage of Payroll**: 1.6%
- **Black Beneficiaries**: 32 (71%)
- **Female Beneficiaries**: 23 (51%)
- **People with Disabilities**: 2 (4%)

**BEE Points Calculation:**
- Skills Development Spend (% of payroll): 5 points
- Priority Group Training: 3 points
- Disabled Employees Trained: 2 points
- **Total BEE Points Earned**: 10 / 20

**Submit** ATR

### Step 6: Submit ATR to SETA

**Same process as WSP:**
1. Export ATR to required format
2. Submit via SETA portal or manually
3. Await approval

**SETA Reviews:**
- Verifies training completed as planned
- Approves grants
- Processes reimbursements

**Grant Payments:**
- Mandatory Grant paid (if compliant)
- Discretionary Grant applications reviewed
- Funds received in company bank account

### Step 7: Calculate BEE Skills Development Scorecard

**B-BBEE Skills Development Element:**

| Indicator | Weight | Target | Achieved | Points |
|-----------|--------|--------|----------|--------|
| Skills spend as % of payroll | 40% | 6% | 1.6% | 10.67/20 |
| Skills spend on Black people | 40% | 85% | 71% | 13.33/20 |
| Disabled learners | 20% | 0.3% | 0.4% | 20/20 |
| **Total** | **100%** | - | - | **44/60** |

**Compliance Level:** Level 6 (needs improvement)

**Recommendations:**
- Increase skills spend to 3-6% of payroll
- Focus on black employees (target 85%)
- Maintain disabled learner targets

### Success Indicator

- ✅ All training activities recorded in Skills Development Record
- ✅ WSP created and submitted to SETA (by April 30)
- ✅ ATR created and submitted to SETA (by April 30)
- ✅ SETA acknowledgments received
- ✅ Mandatory Grant claimed and received
- ✅ BEE points calculated for verification

---

## 15. Employee Termination Workflow

### Overview

za_local provides comprehensive support for BCEA-compliant employee terminations including notice periods, severance pay calculations, leave payouts, and UIF declarations.

### Termination Types

1. **Resignation** - Employee initiated
2. **Dismissal - Misconduct** - Employer initiated (poor performance/conduct)
3. **Dismissal - Operational** - Retrenchment/business reasons
4. **Mutual Agreement** - Both parties agree
5. **End of Contract** - Fixed-term contract expires

### Step 1: Create Employee Separation

**Navigate to:** HR > Employee Separation > New

#### Required Information
- **Employee**: Select employee leaving
- **Resignation Letter Date**: Date notice was received
- **Relieving Date**: Last day of employment
- **Reason for Leaving**: Resignation/Dismissal/Retrenchment
- **Termination Type**: Select from list above

#### Automatic BCEA Calculations

za_local automatically calculates:

**Notice Periods (BCEA Section 37):**
- **< 6 months service**: 1 week notice
- **6 months - 1 year**: 2 weeks notice
- **> 1 year service**: 4 weeks notice

**Severance Pay (BCEA Section 41):**
- **Retrenchment**: 1 week per year of service
- **Tax-free portion**: First R500,000
- **Taxable portion**: Above R500,000 at special rates

**Leave Payout:**
- All unused annual leave
- Proportional 13th cheque (if applicable)
- No payout for unused sick leave

### Step 2: Generate Final Settlement

**Navigate to:** South Africa > Payroll > Employee Final Settlement > New

#### Fields Auto-Populated
1. **Link to Employee Separation**: Select separation record
2. **Employee Details**: Auto-loaded
3. **Final Working Date**: From separation
4. **Notice Period Pay**: Calculated if not worked
5. **Severance Pay**: If retrenchment (1 week × years)
6. **Leave Payout**: All unused annual leave days
7. **13th Cheque**: Pro-rata for year
8. **Deductions**: Outstanding loans, advances

#### Tax Treatment

**Notice Pay:**
- Taxed at normal PAYE rates
- Added to regular payslip

**Severance Pay:**
- Tax-free up to R500,000
- Above R500,000: Special tax table applies
- Separate IRP5 code (3704)

**Leave Payout:**
- Taxed at normal PAYE rates
- Averaged with previous 12 months

### Step 3: Process Final Payslip

Create final salary slip including:

```
EARNINGS:
- Regular salary (pro-rata)
- Notice pay (if applicable)
- Leave payout
- Pro-rata bonus

DEDUCTIONS:
- PAYE (on taxable portions)
- UIF (on normal earnings only)
- Outstanding loans

COMPANY CONTRIBUTIONS:
- UIF Employer (on normal earnings)
- No SDL on severance
```

### Step 4: Create UIF U19 Declaration

**Navigate to:** SA Tax > UIF U19 Declaration > New

#### Required Fields
- **Employee**: Terminated employee
- **Employment Start Date**: From employee record
- **Employment End Date**: Last working day
- **Reason for Leaving**: 
  - Resignation
  - Dismissal
  - Retrenchment
  - End of Contract
- **Total UIF Contributions**: Auto-calculated from payslips
- **Last Remuneration**: Final month's salary

#### Submission to DOL

1. **Save** and **Submit** U19 declaration
2. **Print** form (DOL-U19)
3. **Employee** takes form to Department of Labour
4. **Keep copy** for company records (audit trail)

### Step 5: Exit Interview & Documentation

**Checklist:**
- ✅ Exit interview completed
- ✅ Company assets returned (laptop, access card, etc.)
- ✅ Final settlement agreement signed
- ✅ UIF U19 provided to employee
- ✅ Reference letter (if requested)
- ✅ Certificate of Service
- ✅ Copy of IRP5 (if mid-year termination)

### Compliance Notes

**⚠️ BCEA Requirements:**
- Notice period cannot be waived without compensation
- Severance pay mandatory for operational dismissals
- Leave payout mandatory for all unused annual leave
- Medical certificate rules still apply during notice

**⚠️ UIF Requirements:**
- Employer must provide U19 declaration
- Employee must claim within 6 months
- Total contributions must be accurate
- Reason for leaving affects claim eligibility

### Common Scenarios

**Scenario 1: Resignation (3 years service)**
```
Notice Period: 4 weeks
Severance Pay: R0 (not applicable)
Leave Payout: 10 days × daily rate
Pro-rata 13th: 8/12 × annual 13th
Tax: Normal PAYE + averaged leave
```

**Scenario 2: Retrenchment (5 years service)**
```
Notice Period: 4 weeks (or pay in lieu)
Severance Pay: 5 weeks gross salary (tax-free)
Leave Payout: 15 days × daily rate
Pro-rata 13th: Current YTD
Tax: Severance tax-free, rest at normal PAYE
```

**Scenario 3: Dismissal - Misconduct (2 years service)**
```
Notice Period: 4 weeks (can be waived by employer)
Severance Pay: R0 (not applicable)
Leave Payout: 8 days × daily rate
Pro-rata 13th: None (discretionary)
Tax: Normal PAYE
```

### Success Indicators

- ✅ Employee Separation record created and submitted
- ✅ BCEA notice periods correctly calculated
- ✅ Severance pay accurate (if applicable)
- ✅ Final Settlement generated and approved
- ✅ Final payslip processed with all components
- ✅ UIF U19 provided to employee
- ✅ All company assets returned
- ✅ Employee record status set to "Left"

---

## 16. COIDA Management

### Overview

COIDA (Compensation for Occupational Injuries and Diseases Act) provides no-fault insurance for work-related injuries and diseases. All employers must register and pay annual assessments.

### Step 1: Initial COIDA Setup

**Navigate to:** COIDA > COIDA Settings > New (Single)

#### Required Configuration
- **Company**: Select company
- **COIDA Registration Number**: From Compensation Fund (format: CF123456)
- **Industry Classification**: Select from list (determines assessment rate)
- **Risk Class**: 1 (low risk) to 4 (high risk)
- **Assessment Rate**: % of annual payroll (e.g., 1.25%)
- **Annual Payroll**: Estimated for assessment calculation

#### Industry Classifications & Rates

| Industry | Risk Class | Typical Rate |
|----------|------------|--------------|
| Office/Administration | 1 | 0.27% - 0.35% |
| Retail/Services | 1-2 | 0.43% - 0.58% |
| Manufacturing | 2-3 | 0.81% - 1.45% |
| Construction | 3-4 | 2.16% - 4.31% |
| Mining | 4 | 4.31% - 8.87% |

### Step 2: Record Workplace Injuries

**Navigate to:** COIDA > Workplace Injury > New

#### When to Record
- Any injury requiring medical attention
- Any incident causing 3+ days absence
- Any fatality or serious injury
- Any occupational disease diagnosis

#### Required Information
- **Employee**: Injured employee
- **Injury Date**: When incident occurred
- **Injury Time**: Approximate time
- **Location**: Where injury occurred
- **Injury Type**: 
  - Minor (first aid only)
  - Moderate (medical treatment)
  - Serious (hospitalization)
  - Permanent disablement
  - Fatality
- **Body Part Affected**: Select from list
- **Injury Description**: Detailed description
- **Witnesses**: Names of witnesses
- **Immediate Action Taken**: First aid, hospital, etc.

#### Automatic Actions

On save, za_local:
1. Creates incident report
2. Notifies HR Manager
3. Checks if reportable to Compensation Fund
4. Creates timeline for follow-up

### Step 3: Submit OID Claim

**Navigate to:** COIDA > OID Claim > New

**OID = Occupational Injuries and Diseases**

#### When to Submit
- Employee unable to work for 3+ days
- Permanent disablement resulted
- Employee requires ongoing medical care
- Employee claims compensation

#### Required Documents
1. **W.Cl.2** - Employer's Report of Accident
2. **W.Cl.3** - Employee's Notice of Accident
3. **W.Cl.4** - Doctor's First Report
4. **W.Cl.22** - Medical Report (if hospitalized)
5. **Wage details** - Last 12 months payslips

#### Claim Information
- **Link to Workplace Injury**: Select injury record
- **Claim Type**:
  - Temporary Total Disablement (TTD)
  - Temporary Partial Disablement (TPD)
  - Permanent Disablement
  - Medical Expenses
  - Death Benefits
- **Claim Amount**: If known
- **Expected Return to Work Date**: Estimate
- **Status**: Draft/Submitted/Approved/Paid/Rejected

#### Submission Process

1. **Complete all forms** (W.Cl.2, W.Cl.3, W.Cl.4)
2. **Attach medical reports**
3. **Submit to Compensation Fund**:
   - Online: https://secure.cfonline.org.za
   - Email: claims@compensation.gov.za
   - Post: Compensation Fund regional office
4. **Update claim status** in za_local
5. **Track progress** via Compensation Fund portal

### Step 4: Annual COIDA Return

**Navigate to:** COIDA > COIDA Annual Return > New

**Due Date:** March 31 annually (for previous tax year)

#### Information Required
- **Assessment Year**: Previous tax year (e.g., 2024/2025)
- **Total Annual Payroll**: Sum of all gross salaries
- **Number of Employees**: Average for year
- **Assessment Rate**: Current rate from settings
- **Assessment Due**: Payroll × Rate
- **Provisional Payments Made**: Quarterly payments
- **Balance Due/Refund**: Calculation

#### Calculation Example

```
Annual Payroll: R12,500,000
Assessment Rate: 1.25%
Assessment Due: R12,500,000 × 1.25% = R156,250
Provisional Paid: R150,000
Balance Due: R6,250
```

#### Submission

1. **Complete ROE (Return of Earnings)** form
2. **Submit to Compensation Fund**:
   - Online: https://secure.cfonline.org.za
   - By March 31
3. **Pay balance** (if due)
4. **Claim refund** (if overpaid)
5. **Keep proof of submission** (audit requirement)

### Compliance Requirements

**⚠️ Mandatory:**
- Register within 7 days of starting business
- Submit ROE annually by March 31
- Report all injuries within 7 days
- Keep injury register for 4 years
- Display COIDA certificate in workplace
- Notify fund of payroll increases

**⚠️ Penalties:**
- Late ROE submission: 10% penalty
- Non-registration: Criminal offense
- False information: R4,000 fine or 12 months imprisonment
- Late injury reporting: Claim may be rejected

### Success Indicators

- ✅ COIDA Settings configured with correct rate
- ✅ All workplace injuries recorded within 24 hours
- ✅ OID claims submitted within 7 days
- ✅ Annual return submitted by March 31
- ✅ Assessment paid in full
- ✅ COIDA certificate displayed
- ✅ Injury register maintained

---

## 17. VAT Management

### Overview

For VAT-registered companies, za_local provides VAT201 return preparation, vendor classification, and VAT analysis tools.

### Step 1: VAT Settings

**Navigate to:** SA VAT > South Africa VAT Settings > New (Single)

#### Configuration
- **Company**: Select company
- **VAT Number**: 10-digit VAT number (e.g., 4123456789)
- **VAT Registration Date**: Date registered for VAT
- **Standard VAT Rate**: 15% (current SA rate)
- **VAT Filing Frequency**: Monthly or Bi-monthly
- **Filing Category**:
  - Category A: Monthly (turnover > R30m)
  - Category B: Bi-monthly (turnover R1.5m - R30m)
  - Category C: Bi-monthly (turnover < R1.5m)

### Step 2: Configure VAT Rates

**Navigate to:** SA VAT > South Africa VAT Rate > New

Create rates for different scenarios:

**Standard Rate (15%)**
```
Rate Name: Standard VAT
Rate: 15%
Account: VAT Collected - Sales
Valid From: Current date
```

**Zero-Rated (0%)**
```
Rate Name: Zero-Rated Supplies
Rate: 0%
Account: VAT on Zero-Rated Sales
Examples: Exports, basic foodstuffs, petrol
```

**Exempt (N/A)**
```
Rate Name: Exempt Supplies
Rate: 0% (no VAT charged or claimed)
Examples: Financial services, residential rent
```

### Step 3: Classify VAT Vendors

**Navigate to:** SA VAT > VAT Vendor Type > New

Create vendor classifications:

1. **Registered VAT Vendor** - Can claim input VAT
2. **Non-VAT Vendor** - Cannot claim VAT
3. **Foreign Supplier** - Import VAT applicable
4. **Government Entity** - Special VAT rules

**Assign to Suppliers:**
- Open each Supplier record
- Set "VAT Vendor Type" field
- Save

### Step 4: Process VAT201 Return

**Navigate to:** SA VAT > VAT201 Return > New

#### Information Required
- **Period**: Month or bi-month (e.g., "January 2025")
- **From Date**: Start of period
- **To Date**: End of period

#### Click "Fetch Data"

System automatically populates:

**OUTPUT VAT (Box 1-7):**
- Box 1: Standard-rated supplies (15%)
- Box 2: Zero-rated supplies (0%)
- Box 3: Exempt supplies
- Box 4: Total supplies
- Box 5: Input tax claimed
- Box 6: Net VAT payable/(refundable)

**INPUT VAT (Box 14-19):**
- Box 14: Capital goods acquired
- Box 15: Other goods/services
- Box 16: Total input tax
- Box 17: Adjustments
- Box 18: Net VAT refundable

#### Reconciliation

**Common Issues:**
- Missing invoices (scan purchase invoices)
- Incorrect VAT rates (check supplier setup)
- Non-deductible VAT (entertainment, private use)
- Import VAT (customs declarations)

### Step 5: Submit VAT Return

#### Filing Options

**Option A: eFiling (Recommended)**
1. **Export VAT201** from za_local (CSV format)
2. **Login** to SARS eFiling: www.sarsefiling.co.za
3. **Navigate** to Returns > VAT201
4. **Upload** CSV file
5. **Review** and **Submit**
6. **Pay** via EFT (if VAT payable)

**Option B: Manual Filing**
1. **Print** VAT201 form from za_local
2. **Complete** manually
3. **Submit** to SARS branch
4. **Pay** at bank (if VAT payable)

#### Payment Details

**If VAT Payable:**
```
Beneficiary: SARS VAT
Bank: ABSA
Branch Code: 632005
Account: 4072 173 468
Reference: VAT NUMBER + PERIOD (e.g., 4123456789012025)
```

**Payment Deadline:**
- **Monthly**: 25th of following month
- **Bi-monthly**: 25th of month after period end

### VAT Analysis Report

**Navigate to:** SA VAT > Reports > VAT Analysis

**Filters:**
- Period (monthly/quarterly)
- Company
- VAT category (Standard/Zero/Exempt)

**Output:**
- Total sales by VAT category
- Total purchases by VAT category
- Net VAT position
- Reconciliation to GL

### Common VAT Scenarios

**Scenario 1: Standard Business**
```
Sales (incl VAT): R115,000
VAT Output (15%): R15,000

Purchases (incl VAT): R57,500
VAT Input (15%): R7,500

Net VAT Payable: R15,000 - R7,500 = R7,500
```

**Scenario 2: Mixed Supplies**
```
Standard-rated sales: R100,000 (VAT: R15,000)
Zero-rated exports: R50,000 (VAT: R0)
Total sales: R150,000
VAT output: R15,000

Apportionment: 100,000/150,000 = 66.67% of input VAT claimable
```

**Scenario 3: Import VAT**
```
Import value: $10,000
Exchange rate: R18/$
Rand value: R180,000
Customs duty (10%): R18,000
VAT (15% on R198,000): R29,700
Total payable to SARS: R47,700
VAT claimable on next return: R29,700
```

### Success Indicators

- ✅ VAT Settings configured correctly
- ✅ All suppliers classified (VAT vendor status)
- ✅ VAT rates set up (15%, 0%, exempt)
- ✅ VAT201 generated monthly/bi-monthly
- ✅ Reconciliation to GL complete
- ✅ Returns submitted by 25th
- ✅ VAT payments made on time
- ✅ Proof of submission retained

---

## 18. Business Trip Management (New in v3.1)

### Overview

za_local v3.1 introduces comprehensive Business Trip management with SARS-compliant travel allowances, mileage claims, and automatic expense claim generation.

### Features

✅ **SARS-Compliant Rates**
- Mileage allowance: R4.25/km (2024 rate)
- Regional per diem rates (16 SA cities + international)
- Incidental expense allowances

✅ **Complete Workflow**
- Trip planning and approval
- Allowance tracking by region/day
- Journey tracking (mileage/flights/trains)
- Accommodation expense tracking
- Auto-generate Expense Claims

✅ **Integration**
- Links to Expense Claims
- Connects to Payroll (taxable portions)
- Audit trail for SARS

### Step 1: Configure Business Trip Settings

**Navigate to:** South Africa > Payroll > Business Trip Settings

**Mileage Allowance:**
- **Mileage Allowance Rate**: R4.25 per km (SARS 2024 rate)
- **Mileage Expense Claim Type**: "Travel" or create new

**Daily Allowances:**
- **Meal Expense Claim Type**: "Travel"
- **Incidental Expense Claim Type**: "Others"

**Workflow Settings:**
- **Require Manager Approval**: ✅ Checked (recommended)
- **Auto Create Expense Claim on Submit**: ✅ Checked (saves time)

**Save** settings.

### Step 2: Set Up Business Trip Regions

**Navigate to:** South Africa > Payroll > Business Trip Region

**Pre-loaded Regions (16):**

| Region | Daily Allowance | Incidental | Location |
|--------|----------------|------------|----------|
| Johannesburg | R1,500 | R100 | Gauteng |
| Cape Town | R1,400 | R100 | Western Cape |
| Durban | R1,300 | R100 | KZN |
| Pretoria | R1,200 | R100 | Gauteng |
| Port Elizabeth | R1,100 | R100 | Eastern Cape |
| Bloemfontein | R1,000 | R100 | Free State |
| International - Africa | R2,200 | R200 | Africa |
| International - Europe | R3,300 | R300 | Europe |
| ... | ... | ... | ... |

**Add Custom Region:**
1. Click **New**
2. **Region Name**: e.g., "Rustenburg"
3. **Country**: "South Africa"
4. **Daily Allowance Rate**: R1,000
5. **Incidental Allowance Rate**: R100
6. **Is Active**: ✅
7. **Save**

### Step 3: Create a Business Trip

**Navigate to:** South Africa > Payroll > Business Trip > New

#### Basic Details
- **Employee**: Select traveling employee
- **Company**: Auto-filled
- **Trip Purpose**: e.g., "Client Meeting - Cape Town"
- **From Date**: 2025-02-10
- **To Date**: 2025-02-12
- **Status**: Draft (auto-set)

#### Click "Generate Allowances" Button

System creates one row per day:

| Date | Region | Daily Rate | Incidental | Total |
|------|--------|-----------|------------|-------|
| 2025-02-10 | (select) | R0 | R0 | R0 |
| 2025-02-11 | (select) | R0 | R0 | R0 |
| 2025-02-12 | (select) | R0 | R0 | R0 |

**Select Region for each day:**
1. Click **Region** dropdown for Day 1
2. Select "Cape Town"
3. **Daily Rate** auto-fills: R1,400
4. **Incidental Rate** auto-fills: R100
5. **Total** calculates: R1,500
6. Repeat for remaining days

**Allowances Table (completed):**

| Date | Region | Daily Rate | Incidental | Total |
|------|--------|-----------|------------|-------|
| 2025-02-10 | Cape Town | R1,400 | R100 | R1,500 |
| 2025-02-11 | Cape Town | R1,400 | R100 | R1,500 |
| 2025-02-12 | Cape Town | R1,400 | R100 | R1,500 |

**Total Allowances:** R4,500

### Step 4: Add Journey Details

**Journeys & Transport Section:**

**Day 1: Flight to Cape Town**
- **Date**: 2025-02-10
- **From Location**: Johannesburg
- **To Location**: Cape Town
- **Transport Mode**: Flight
- **Receipt Amount**: R2,800
- **Receipt Attached**: ✅

**Day 3: Flight back**
- **Date**: 2025-02-12
- **From Location**: Cape Town
- **To Location**: Johannesburg
- **Transport Mode**: Flight
- **Receipt Amount**: R2,600
- **Receipt Attached**: ✅

**Local Travel (Uber)**
- **Date**: 2025-02-11
- **From Location**: Hotel
- **To Location**: Client Office
- **Transport Mode**: Uber/Bolt
- **Receipt Amount**: R250
- **Receipt Attached**: ✅

**Total Transport:** R5,650

**Mileage Example (Private Car):**
```
Date: 2025-02-11
From Location: Hotel
To Location: Client Office (Return)
Transport Mode: Car (Private)
Distance (km): 45
Mileage Rate: R4.25 (auto-filled from settings)
Mileage Claim: R191.25 (auto-calculated)
```

### Step 5: Add Accommodation

**Accommodation Section:**

**Night 1:**
- **Date**: 2025-02-10
- **Hotel Name**: Protea Hotel V&A Waterfront
- **City**: Cape Town
- **Amount**: R1,800
- **Receipt Attached**: ✅

**Night 2:**
- **Date**: 2025-02-11
- **Hotel Name**: Protea Hotel V&A Waterfront
- **City**: Cape Town
- **Amount**: R1,800
- **Receipt Attached**: ✅

**Total Accommodation:** R3,600

### Step 6: Add Other Expenses

**Other Expenses Section:**

**Parking:**
- **Date**: 2025-02-11
- **Description**: Airport Parking
- **Amount**: R180
- **Receipt Required**: ✅

**Wi-Fi:**
- **Date**: 2025-02-10
- **Description**: Hotel Wi-Fi
- **Amount**: R150
- **Receipt Required**: ✅

**Total Other:** R330

### Step 7: Review & Submit

**Summary Totals:**

| Category | Amount |
|----------|--------|
| Daily Allowances | R4,200 |
| Incidental Allowances | R300 |
| Transport (Flights/Uber) | R5,650 |
| Accommodation | R3,600 |
| Other Expenses | R330 |
| **GRAND TOTAL** | **R14,080** |

**Actions:**
1. **Save** business trip
2. **Submit** for approval (if required)
3. **Manager approves** via workflow
4. System **Auto-Creates Expense Claim**

### Step 8: Expense Claim Auto-Generation

**Navigate to:** HR > Expense Claim > [Auto-generated]

System creates Expense Claim with:

**Expenses Table:**

| Date | Description | Type | Amount |
|------|-------------|------|--------|
| 2025-02-12 | Business Trip Allowances: Client Meeting | Travel | R4,500 |
| 2025-02-12 | Transport (Flights/Trains/Rental) | Travel | R5,650 |
| 2025-02-12 | Accommodation | Travel | R3,600 |
| 2025-02-12 | Other Expenses | Others | R330 |

**Total Claim:** R14,080

**Status:** Draft (ready for manager approval)

**Link:** Business Trip field populated with trip reference

### Tax Treatment of Travel Allowances

**SARS Rules:**

**Reimbursive Allowances (Actual):**
- Employee keeps receipts
- Company reimburses exact amounts
- **Not taxable** to employee
- **za_local default method**

**Fixed Travel Allowance (80/20):**
- Monthly fixed amount (e.g., R5,000/month)
- 80% taxable, 20% non-taxable
- Employee must keep logbook
- Different SARS rules apply

**Mileage Allowance:**
- Up to R4.25/km is **tax-free**
- Above R4.25/km is **taxable**
- Must be for business purposes only

### Reports

**Business Trip Summary Report:**
```
Navigate to: South Africa > Payroll > Reports > Business Trip Summary

Filters:
- Date Range: 2025-01-01 to 2025-12-31
- Employee: All or specific
- Company: Select company

Output:
- Number of trips
- Total allowances paid
- Total mileage claims
- Total accommodation
- Average trip cost
- Export to Excel
```

### Common Scenarios

**Scenario 1: Day Trip (No Accommodation)**
```
From: Johannesburg
To: Pretoria (120km round trip)
Transport: Private Car

Mileage: 120km × R4.25 = R510
Lunch: R200 (incidental)
Total: R710 (tax-free)
```

**Scenario 2: International Trip**
```
Destination: London (5 days)
Flights: R18,000
Accommodation: £120/night × 5 = R12,000
Daily allowance: R3,300 × 5 = R16,500
Total: R46,500

Tax treatment:
- Flights: Reimbursive (not taxable)
- Accommodation: Reimbursive (not taxable)
- Allowances: May be taxable if exceeds SARS rates
```

**Scenario 3: Conference + Leisure**
```
Business days: 3 days (claimable)
Leisure days: 2 days (not claimable)

Claim:
- 3 days allowances ✅
- Flights: Apportion 60% ✅
- Accommodation: 3 nights only ✅
```

### Best Practices

**Before the Trip:**
- ✅ Create Business Trip record in advance
- ✅ Get manager approval if required
- ✅ Set daily budget expectations
- ✅ Book flights/accommodation in advance

**During the Trip:**
- ✅ Keep ALL receipts (photo backup)
- ✅ Note mileage if using private car
- ✅ Document business purpose
- ✅ Keep receipts separate from personal

**After the Trip:**
- ✅ Complete Business Trip within 5 days
- ✅ Attach all receipts
- ✅ Submit for approval
- ✅ Process expense claim promptly

### Success Indicators

- ✅ Business Trip Settings configured (R4.25/km)
- ✅ 16 regions loaded with current rates
- ✅ Business Trip created and submitted
- ✅ All receipts attached
- ✅ Expense Claim auto-generated
- ✅ Manager approved claim
- ✅ Employee reimbursed
- ✅ Audit trail maintained for SARS

---

## 19. Sectoral Compliance

### Overview

Certain industries in South Africa have additional compliance requirements through Bargaining Councils or Sectoral Determinations that set minimum wages and working conditions.

### Step 1: Configure Bargaining Council

**Navigate to:** South Africa > Payroll > Bargaining Council

**Pre-loaded Councils (11):**
- MEIBC (Metal and Engineering)
- NBCRFLI (Road Freight and Logistics)
- CCMA
- National Bargaining Council for the Textile Industry
- And 7 more...

**Add Custom Council:**
1. Click **New**
2. **Council Name**: e.g., "Western Cape Clothing BC"
3. **Full Name**: Western Cape Clothing Industry Bargaining Council
4. **Registration Date**: When registered
5. **Contribution Rate**: e.g., 2% of payroll
6. **Payment Frequency**: Monthly
7. **Save**

### Step 2: Assign Company to Bargaining Council

**Navigate to:** Setup > Company > [Your Company]

**SA Registration Details Section:**
- **Bargaining Council**: Select council (e.g., "MEIBC")
- **Sectoral Determination**: If applicable (e.g., "Domestic Workers")

**Save** company record.

### Step 3: Configure Sectoral Minimum Wages

**Navigate to:** South Africa > Payroll > Sectoral Minimum Wage > New

**Example: Domestic Workers (2024)**
```
Sector: Domestic Workers
Job Category: Domestic Worker
Area: Urban
Minimum Hourly Rate: R25.42
Minimum Monthly (full-time): R4,651.67
Effective From: 2024-03-01
Valid Until: 2025-02-28
```

**Example: Farm Workers (2024)**
```
Sector: Agriculture
Job Category: Farm Worker
Area: All areas
Minimum Hourly Rate: R27.58
Minimum Monthly (full-time): R5,049.27
Effective From: 2024-03-01
Valid Until: 2025-02-28
```

### Step 4: Configure Industry-Specific Contributions

**Navigate to:** South Africa > Payroll > Industry Specific Contribution > New

**Example: MEIBC Contributions**
```
Bargaining Council: MEIBC
Contribution Type: Sick Pay Fund
Employee Contribution: 1%
Employer Contribution: 1%
Maximum Monthly: R500
Effective From: 2024-01-01
```

**Add to Salary Structure:**
1. Open **Salary Structure**
2. Add row in **Deductions**:
   - Component: "MEIBC Sick Pay - Employee"
   - Formula: `base * 0.01` (1%)
   - Condition: Bargaining Council = "MEIBC"
3. Add row in **Company Contributions**:
   - Component: "MEIBC Sick Pay - Employer"
   - Formula: `base * 0.01` (1%)

### Step 5: Monthly Compliance Submissions

**MEIBC Example:**

**Submit by 7th of month:**
1. **Payroll Report** - All employee wages
2. **Sick Pay Fund Contributions**
3. **Skills Development Contributions**
4. **Bargaining Council Levies**

**Online Submission:**
- Portal: https://meibc.co.za
- Upload CSV from za_local
- Payment via EFT

### NAEDO Debit Orders

**NAEDO = National Authenticated Early Debit Order**

Used for:
- Garnishee orders (court-ordered deductions)
- Child maintenance
- Debt repayments
- Loan repayments

**Navigate to:** South Africa > Payroll > NAEDO Deduction > New

#### Required Information
- **Employee**: Select employee
- **Order Type**: Garnishee/Maintenance/Debt
- **Order Number**: Court order number
- **Beneficiary Name**: Recipient
- **Bank Details**: Beneficiary account
- **Deduction Amount**: Monthly amount
- **Start Date**: When deductions begin
- **End Date**: When deductions end (if known)
- **Priority**: 1 (highest) to 10 (lowest)

#### Deduction Priority (BCEA)

**Legal order of deductions:**
1. Tax (PAYE)
2. Maintenance orders
3. Garnishee orders
4. Other debts
5. Voluntary deductions (loans, etc.)

**Maximum total deductions:**
- PAYE: No limit
- Other deductions: Maximum 25% of net pay
- Exception: Maintenance can exceed 25%

#### Process in Payroll

On payroll processing:
1. System fetches active NAEDO deductions
2. Applies deductions in priority order
3. Respects 25% limit (except maintenance)
4. Creates EFT payment entries
5. Generates NAEDO file for bank

### Success Indicators

- ✅ Bargaining Council configured (if applicable)
- ✅ Sectoral minimum wages set
- ✅ Industry-specific contributions in salary structure
- ✅ Monthly returns submitted by deadline
- ✅ NAEDO deductions correctly prioritized
- ✅ Maximum deduction limits respected
- ✅ All statutory payments made on time

---

## 20. Reports & Analytics

### Overview

za_local provides comprehensive reports for payroll analysis, compliance monitoring, and decision-making.

> 💡 **Quick Access**: All reports are accessible via the **South Africa > Payroll** workspace in the sidebar. Navigate to **South Africa > Payroll > Reports** to see all available reports organized by category.

### Payroll Register

**Navigate to:** South Africa > Payroll > Reports > Payroll Register

**Purpose:** Complete payroll breakdown for period

**Filters:**
- **Period**: Select month/payroll period
- **Company**: Select company
- **Department**: All or specific
- **Employee**: All or specific

**Output Columns:**
- Employee ID, Name, Department
- Basic Salary, Allowances, Gross Pay
- PAYE, UIF, SDL, Other Deductions
- Net Pay, Bank Details
- Company Contributions (UIF, SDL)
- Total Cost to Company

**Export:** Excel, PDF, CSV

**Use Cases:**
- Monthly payroll review
- Budget vs actual analysis
- Departmental cost allocation
- Audit trail

### Department Cost Analysis

**Navigate to:** South Africa > Payroll > Reports > Department Cost Analysis

**Purpose:** Analyze payroll costs by department

**Filters:**
- **From Date**: 2025-01-01
- **To Date**: 2025-12-31
- **Company**: Select
- **Cost Center**: Optional

**Output:**

| Department | Employees | Gross Salary | Company Contrib | Total Cost | Avg per Employee |
|------------|-----------|--------------|----------------|------------|------------------|
| Engineering | 25 | R1,250,000 | R125,000 | R1,375,000 | R55,000 |
| Sales | 15 | R900,000 | R90,000 | R990,000 | R66,000 |
| Operations | 30 | R1,500,000 | R150,000 | R1,650,000 | R55,000 |
| HR | 8 | R400,000 | R40,000 | R440,000 | R55,000 |
| **Total** | **78** | **R4,050,000** | **R405,000** | **R4,455,000** | **R57,115** |

**Chart:** Pie chart of cost distribution

### Statutory Submissions Summary

**Navigate to:** South Africa > Payroll > Reports > Statutory Submissions Summary

**Purpose:** Track all statutory submissions and payments

**Filters:**
- **Tax Year**: 2024-2025
- **Company**: Select

**Output:**

| Month | EMP201 Status | PAYE Amount | UIF Amount | SDL Amount | Payment Status | Submission Date |
|-------|---------------|-------------|------------|-----------|----------------|-----------------|
| Mar 2024 | Submitted | R125,000 | R25,000 | R12,500 | Paid | 2024-04-05 |
| Apr 2024 | Submitted | R128,000 | R26,000 | R13,000 | Paid | 2024-05-06 |
| May 2024 | Submitted | R130,000 | R26,500 | R13,250 | Paid | 2024-06-04 |
| ... | ... | ... | ... | ... | ... | ... |
| **Total** | **12/12** | **R1,545,000** | **R309,000** | **R154,500** | **All Paid** | - |

**Alerts:**
- 🔴 Outstanding submissions
- 🟡 Late submissions
- 🟢 All compliant

### EEA2 Income Differentials

**Navigate to:** SA EE > Reports > EEA2 Income Differentials

**Purpose:** Analyze pay equity for EE reporting

**Filters:**
- **Company**: Select
- **As at Date**: 2025-02-28

**Output Matrix:**

| Occupational Level | African Male | African Female | Coloured Male | ... | White Female | Pay Gap |
|--------------------|--------------|----------------|---------------|-----|--------------|---------|
| Top Management | R95,000 | R92,000 | - | ... | R98,000 | 6.5% |
| Senior Management | R75,000 | R72,000 | R76,000 | ... | R78,000 | 8.3% |
| Professionally Qualified | R45,000 | R43,000 | R46,000 | ... | R47,000 | 9.3% |
| **Average** | **R55,000** | **R52,000** | **R57,000** | ... | **R58,000** | **10.9%** |

**Analysis:**
- Identifies pay gaps by race and gender
- Flags areas for attention
- Export for EEA2 submission
- Supports equity planning

### EEA4 Employment Equity Plan

**Navigate to:** SA EE > Reports > EEA4 Employment Equity Plan

**Purpose:** Workforce demographics for EE Act compliance

**Output:**

| Occupational Level | Total | Male | Female | African | Coloured | Indian | White | Disabled |
|--------------------|-------|------|--------|---------|----------|--------|-------|----------|
| Top Management | 8 | 6 (75%) | 2 (25%) | 2 (25%) | 0 | 1 (13%) | 5 (63%) | 0 |
| Senior Management | 15 | 10 (67%) | 5 (33%) | 6 (40%) | 2 (13%) | 2 (13%) | 5 (33%) | 1 (7%) |
| Professionally Qualified | 45 | 28 (62%) | 17 (38%) | 20 (44%) | 8 (18%) | 5 (11%) | 12 (27%) | 3 (7%) |
| **Total** | **150** | **95 (63%)** | **55 (37%)** | **68 (45%)** | **22 (15%)** | **15 (10%)** | **45 (30%)** | **12 (8%)** |

**Targets vs Achieved:**
- Track progress against EE plan targets
- Identify under-represented groups
- Set future hiring targets

### EE Workforce Profile

**Navigate to:** SA EE > Reports > EE Workforce Profile

**Purpose:** Visual workforce demographics

**Charts:**
1. **Pie Chart:** Race distribution
2. **Bar Chart:** Gender per level
3. **Line Chart:** Representation trends over time
4. **Heat Map:** Under-representation areas

### Custom Reports

**Create Custom Report:**
1. Navigate to: Setup > Report Builder
2. Select DocType: "Salary Slip"
3. Add fields: employee, gross_pay, net_pay, paye
4. Add filters: posting_date, company
5. Save report
6. Run and export

### Success Indicators

- ✅ Payroll Register generated monthly
- ✅ Department costs tracked and analyzed
- ✅ Statutory submissions tracked
- ✅ All EMP201s submitted on time
- ✅ EEA2 report prepared (if required)
- ✅ EEA4 report prepared (if required)
- ✅ Pay equity gaps identified and addressed
- ✅ Reports exported for audit

---

## 21. Advanced Features

### EFT File Generation

**Navigate to:** South Africa > Payroll > Payroll Payment Batch > New

**Purpose:** Generate bank file for salary payments

**Supported Banks:**
- Standard Bank (CSV format)
- ABSA (CSV format)
- FNB (TXT format)
- Nedbank (CSV format)

**Process:**
1. **Select Payroll Entry**: Choose submitted payroll
2. **Payment Date**: Date for bank processing
3. **Bank**: Select bank
4. **Click "Generate EFT File"**
5. **Download** file
6. **Upload** to bank's online banking portal

**File Contents:**
```
Employee Name, Bank, Branch, Account, Amount, Reference
John Doe, FNB, 250655, 62123456789, 25000.00, Salary Feb 2025
Jane Smith, Standard, 051001, 123456789, 30000.00, Salary Feb 2025
...
```

### SARS XML Export

**EMP501 XML Export:**
```python
Navigate to: SA Tax > EMP501 Reconciliation > [Select record]
Click: "Export XML for SARS eFiling"
Download: EMP501_2024_2025.xml
Upload to SARS eFiling portal
```

**IRP5 Bulk XML Export:**
```python
Navigate to: SA Tax > IRP5 Certificate > List View
Select: All employee certificates
Actions > "Export Bulk XML"
Download: IRP5_Bulk_2024_2025.xml
Upload to SARS eFiling portal
```

### Data Import Templates

**Import Employees (CSV):**
```csv
employee_id,first_name,last_name,za_id_number,date_of_joining,department
EMP001,John,Doe,9001015009087,2024-01-15,Engineering
EMP002,Jane,Smith,8508225009081,2024-02-01,Sales
```

**Import Salary Structures (CSV):**
```csv
employee,base,housing_allowance,travel_allowance,from_date
EMP001,25000,5000,3000,2024-03-01
EMP002,30000,6000,0,2024-03-01
```

### API Integration

**Payroll API Endpoints:**
```python
# Get employee payroll data
GET /api/resource/Salary Slip?employee=EMP001&filters=[["posting_date",">=","2024-01-01"]]

# Create additional salary
POST /api/resource/Additional Salary
{
    "employee": "EMP001",
    "salary_component": "Bonus",
    "amount": 5000,
    "payroll_date": "2024-03-31"
}

# Get EMP201 data
GET /api/resource/EMP201 Submission/EMP201-00001
```

### Scheduled Compliance Checks

**Automated Daily Tasks:**
- Tax directive expiry warnings (30 days)
- ETI eligibility changes (age/tenure)

**Automated Weekly Tasks:**
- ID number validation (checksum + duplicates)

**Automated Monthly Tasks:**
- SARS rate update reminders
- COIDA rate review alerts

**Automated Quarterly Tasks:**
- EEA reporting deadline reminders

**Check Status:**
```bash
bench execute za_local.tasks.daily
bench execute za_local.tasks.weekly
bench execute za_local.tasks.monthly
```

---

## 22. Common Workflows Quick Reference

### Monthly Payroll (5-Step Process)

```
1. PREPARE (Week 1)
   └─ Update employee changes (joins/leaves/promotions)
   └─ Process additional salaries (bonuses/deductions)
   └─ Apply tax directives
   └─ Review leave applications

2. PROCESS (Week 3)
   └─ Create Payroll Entry
   └─ Get Employees
   └─ Create Salary Slips
   └─ Review for accuracy

3. APPROVE (Week 3)
   └─ Manager reviews salary slips
   └─ HR confirms totals
   └─ Submit Payroll Entry

4. PAY (Week 4)
   └─ Generate EFT file
   └─ Upload to bank
   └─ Confirm payments processed

5. REPORT (Week 4)
   └─ Create EMP201
   └─ Submit to SARS by 7th
   └─ Pay SARS by 7th
   └─ Archive payslips
```

### Annual Tax Cycle

```
MARCH (Tax Year Start)
└─ Update tax rebates for new year
└─ Update ETI slabs
└─ Update UIF threshold

MAY (IRP5 & EMP501 Final Season)
└─ Generate IRP5 certificates (all employees)
└─ Review and correct errors
└─ IRP5 Deadline: May 31 (internal), June 15 (SARS submission)
└─ EMP501 Final reconciliation (full tax year March-February)
└─ EMP501 Final Deadline: May 31
└─ Reconcile provisional tax

JUNE-JULY
└─ Submit IRP5 bulk file to SARS
└─ Distribute IRP5s to employees
└─ Handle SARS queries

OCTOBER
└─ EMP501 Interim reconciliation (March-August period)
└─ Submit to SARS by October 31
```

### Employee Lifecycle

```
HIRE
└─ Create Employee record
└─ Employment Equity classification
└─ Assign to Bargaining Council (if applicable)
└─ Create Salary Structure Assignment
└─ Allocate leave
└─ Generate employment contract

MANAGE
└─ Process monthly payroll
└─ Track leave applications
└─ Record training (Skills Development)
└─ Annual performance reviews
└─ Salary increases

TERMINATE
└─ Employee Separation record
└─ Calculate notice period (BCEA)
└─ Final Settlement (severance/leave)
└─ Final payslip
└─ UIF U19 declaration
└─ IRP5 certificate
```

---

## 23. Troubleshooting & FAQs

### Common Issues

**Q: ETI not calculating on salary slip**

A: Check:
1. Employee age < 30 (ETI eligibility)
2. Employment tenure < 24 months
3. ETI slabs exist for tax year
4. Salary within ETI bands (R2,000-R6,500)
5. Payroll Settings > "Disable ETI" = unchecked

**Q: PAYE amount seems incorrect**

A: Verify:
1. Employee tax rebates configured
2. Medical tax credits applied (if dependants)
3. Tax directive active (overrides standard PAYE)
4. Annual taxable income calculation method
5. Previous months YTD figures correct

**Q: UIF deduction exceeds R177.12**

A: Check:
1. Salary component formula: `min(gross_pay * 0.01, 177.12)`
2. UIF threshold updated (R17,712 monthly cap)
3. Additional salaries not double-counting

**Q: IRP5 totals don't match EMP201**

A: Reconcile:
1. IRP5 = per employee for tax year
2. EMP201 = monthly submissions total
3. Check for missed months
4. Verify employee count
5. Review mid-year joins/leaves

**Q: Business Trip not generating Expense Claim**

A: Check:
1. Business Trip Settings > "Auto Create Expense Claim" = ✅
2. Business Trip status = "Submitted"
3. Expense Claim Type configured
4. Employee has manager assigned (if approval required)

**Q: CSV import failing for Business Trip Regions**

A: Verify:
1. CSV file encoding (UTF-8)
2. Numeric values in correct format (1500 not "1,500")
3. Required fields: region_name, daily_allowance_rate
4. File path: `za_local/data/business_trip_region.csv`

### Error Messages

**Error:** "Document Links Row #1: Invalid doctype or fieldname"

**Solution:** This error during installation means a DocType Link references a non-existent field. Check `hooks.py` for invalid link configurations. All DocType Links have been validated in v3.1.

**Error:** "Custom field already exists"

**Solution:** During reinstall, custom fields may already exist. The system skips duplicates automatically. If persistent, manually delete custom fields via Customize Form before reinstall.

**Error:** "'<' not supported between instances of 'str' and 'int'"

**Solution:** CSV import type conversion issue (fixed in v3.1). Ensure `csv_importer.py` includes `convert_csv_types()` function.

**Error:** "Please set account in Salary Component ... All components must have associated accounts for SA payroll compliance."

**What it means:** One or more Salary Components on the Salary Slip/Structure do not have a `Salary Component Account` configured for the company.

**Solution:** Add accounts on each component. The error lists all missing components with clickable links (e.g. `Basic Salary`, `PAYE`, `UIF Employer Contribution`). Open each component and add rows in the "Salary Component Account" child table for your company.

### Performance Optimization

**Large Payroll (500+ employees):**
1. Process payroll in batches (by department)
2. Increase timeout settings
3. Schedule during off-peak hours
4. Use background jobs

**Slow Reports:**
1. Add database indexes on frequently queried fields
2. Limit date ranges
3. Filter by company/department
4. Export to Excel for complex analysis

---

## 24. Compliance Calendar

### Monthly Deadlines

| Date | Task | Authority | Penalty for Late |
|------|------|-----------|------------------|
| 7th | EMP201 Submission | SARS | Administrative penalty + interest |
| 7th | PAYE Payment | SARS | 10% penalty + interest |
| 7th | UIF/SDL Payment | SARS | Interest + penalty |
| 15th | COIDA Payment (if monthly) | Compensation Fund | 10% penalty |
| 25th | VAT201 Return (monthly) | SARS | Administrative penalty |
| 25th | VAT Payment | SARS | 10% penalty + interest |
| Last day | Payroll Processing | Internal | Employee dissatisfaction |

### Quarterly Deadlines

| Month | Task | Authority |
|-------|------|-----------|
| Jan/Apr/Jul/Oct | COIDA Payment (quarterly) | Compensation Fund |
| End of Quarter | Provisional Tax (if applicable) | SARS |

### Annual Deadlines

| Date | Task | Authority | Penalty |
|------|------|-----------|---------|
| **March 31** | COIDA Annual Return (ROE) | Compensation Fund | 10% + interest |
| **April 30** | WSP Submission | SETA | Loss of Mandatory Grant |
| **April 30** | ATR Submission | SETA | Loss of Discretionary Grant |
| **May 31** | IRP5 Generation | Internal (SARS by June 15) | Employee complaints |
| **October 31** | EMP501 Reconciliation (Interim: March-August) | SARS | 1% of annual PAYE per month (max 10%) |
| **May 31** | EMP501 Reconciliation (Final: March-February full tax year) | SARS | 1% of annual PAYE per month (max 10%) |
| **January 15** | EEA Report Submission (if designated) | DOL | Up to R2.7M fine |

### Tax Year Dates

**South African Tax Year:**
- **Starts:** March 1
- **Ends:** February 28/29

**Important Tax Year Tasks:**
- **March:** Update tax tables, rebates, thresholds
- **February:** Year-end preparations, provisional reconciliations

### Reminder: Enable Scheduled Tasks

Ensure scheduled tasks are running:
```bash
bench --site your-site enable-scheduler
bench doctor  # Verify scheduler is active
```

---

## 25. Best Practices

### Data Backup

**Daily Backups:**
```bash
bench --site your-site backup
# Stores in: sites/your-site/private/backups/
```

**Off-site Storage:**
- Copy backups to cloud storage (Dropbox/Google Drive)
- Retain for minimum 5 years (SARS requirement)

**Test Restores:**
- Quarterly restore test on staging environment
- Document restore procedure

### Security

**User Access Control:**
- HR Manager: Full access
- Payroll Officer: Payroll + Tax only
- Employee: View own payslips only
- Manager: Approve team leave/expense claims

**Sensitive Data:**
- ID numbers encrypted at rest
- Salary information role-restricted
- Audit log for all payroll changes

**Password Policy:**
- Minimum 10 characters
- 2FA for admin users
- Password rotation every 90 days

### Audit Trail

**Maintain:**
- All payroll reports (5 years)
- All EMP201 submissions (5 years)
- All IRP5 certificates (5 years)
- Employee records (3 years after termination)
- COIDA injury reports (4 years)

### Month-End Checklist

**Before Processing:**
- [ ] All leave applications approved/rejected
- [ ] All additional salaries created
- [ ] All employee changes processed (joins/leaves)
- [ ] Tax directives updated
- [ ] Bank account changes verified

**During Processing:**
- [ ] Payroll Entry created
- [ ] All employees included
- [ ] Salary slips reviewed (spot-check 10%)
- [ ] Totals reconciled to budget
- [ ] Manager approval obtained

**After Processing:**
- [ ] Payroll submitted
- [ ] EFT file generated and sent to bank
- [ ] Employee payslips distributed (email)
- [ ] EMP201 created and submitted
- [ ] SARS payment made
- [ ] Reports archived

**Reconciliation:**
- [ ] Payroll to GL reconciliation
- [ ] Bank statement reconciliation
- [ ] SARS payment confirmation
- [ ] Outstanding variances resolved

### Year-End Checklist

**February (Year-End):**
- [ ] Review all employee records for accuracy
- [ ] Confirm all payrolls processed (12 months)
- [ ] Verify YTD totals on salary slips
- [ ] Generate preliminary IRP5s for review

**March (New Tax Year):**
- [ ] Update tax tables/rebates/thresholds
- [ ] Update ETI slabs for new year
- [ ] Review salary structures
- [ ] Annual leave reset (if applicable)

**May (IRP5 Season):**
- [ ] Generate final IRP5s
- [ ] Employee review and corrections
- [ ] EMP501 reconciliation
- [ ] Submit to SARS by May 31
- [ ] Distribute IRP5s to employees

### Performance Tips

**Optimize Payroll Processing:**
1. Process in batches (max 100 employees)
2. Use filters (department/branch)
3. Clear browser cache regularly
4. Schedule large processes during off-peak

**Database Maintenance:**
```bash
bench --site your-site mariadb
ANALYZE TABLE `tabSalary Slip`;
ANALYZE TABLE `tabEmployee`;
```

**Regular Cleanup:**
- Archive old payroll data (> 5 years)
- Delete draft salary slips after submit
- Clear system logs (> 90 days)

---

## 26. Support & Resources

### Documentation

- **README.md**: Quick overview and features
- **QUICK_SETUP_CHECKLIST.md**: 2-hour setup guide
- **FEATURE_COMPARISON.md**: vs erpnext_germany
- **VALIDATION_REPORT_v3.1.md**: System validation
- **TUTORIAL_OUTLINE.md**: Video tutorial scripts
- **FINAL_SUMMARY.md**: Implementation summary

### Official Resources

**SARS (Tax):**
- Website: www.sars.gov.za
- eFiling: www.sarsefiling.co.za
- Contact: 0800 00 SARS (7277)

**Department of Labour:**
- Website: www.labour.gov.za
- CCMA: www.ccma.org.za
- Contact: 0860 105 090

**Department of Employment & Labour:**
- UIF: www.ufiling.co.za
- Contact: 0800 030 007

**Compensation Fund (COIDA):**
- Website: www.labour.gov.za/compensation-fund
- Online: secure.cfonline.org.za
- Contact: 012 319 5000

**National Minimum Wage Commission:**
- Website: www.thepresidency.gov.za

### za_local Support

**Community Support:**
- **GitHub Issues**: Report bugs, request features
- **Frappe Forum**: Community discussions
- **Stack Overflow**: Tag `frappe` + `za-local`

**Professional Support:**
- **Email**: info@cohenix.com
- **Website**: www.cohenix.com
- **Implementation Services**: Custom setup, training, migration
- **Support Plans**: Hourly/monthly retainer options

### Training Resources

**Video Tutorials** (See TUTORIAL_OUTLINE.md):
1. Quick Start (5 min)
2. Complete Setup (15 min)
3. Monthly Payroll (10 min)
4. Annual Tax Reconciliation (10 min)
5. Employee Termination (5 min)
6. Business Trips (8 min)
7. Employment Equity (12 min)

**Webinars:**
- Monthly compliance updates
- Feature deep-dives
- Q&A sessions

### Legal Disclaimer

This software is provided "as is" without warranty. While za_local aims for full compliance with South African labour and tax laws, users are responsible for:

1. Verifying calculations against current legislation
2. Consulting with tax professionals for complex scenarios
3. Maintaining proper records for audits
4. Submitting all returns to authorities
5. Making all statutory payments on time

Cohenix and the za_local contributors are not liable for penalties, interest, or losses resulting from misconfiguration or misuse of the software.

**Always consult qualified professionals** (accountants, tax attorneys, labour consultants) for complex compliance matters.

### Updates & Changelog

**Current Version:** 3.1.0 (January 2025)

**Recent Updates:**
- ✅ Business Trip Management (8 DocTypes)
- ✅ Document deletion protection (SARS audit)
- ✅ Property setters (40+ DocTypes)
- ✅ Enhanced employee fields (7 fields)
- ✅ Automated compliance tasks (5 scheduled)
- ✅ CSV master data import (51 records)
- ✅ Bidirectional DocType links (21 links)

**Coming Soon (Roadmap):**
- 🔄 SARS API integration (direct eFiling)
- 🔄 Advanced BEE scorecard calculator
- 🔄 Pension fund integrations
- 🔄 Mobile app (employee self-service)
- 🔄 Advanced analytics dashboard

### Contributing

za_local is open-source (MIT License). Contributions welcome:

1. **Fork** repository
2. **Create** feature branch
3. **Test** thoroughly
4. **Submit** pull request
5. **Document** changes

**Code Standards:**
- PEP 8 for Python
- ESLint for JavaScript
- Frappe coding guidelines
- Comprehensive docstrings

### Acknowledgments

- **Frappe Community**: Excellent framework
- **erpnext_germany**: Inspiration and benchmarking
- **SA Business Community**: Compliance requirements and feedback
- **Contributors**: All developers and testers

---

## 🎉 Congratulations!

You've completed the za_local Implementation Guide. You now have the knowledge to:

✅ Install and configure za_local  
✅ Process monthly payroll with full SARS compliance  
✅ Manage employee lifecycle (hire to termination)  
✅ Handle tax submissions (EMP201, EMP501, IRP5)  
✅ Track fringe benefits and travel  
✅ Generate Employment Equity reports  
✅ Manage COIDA and VAT compliance  
✅ Process employee terminations (BCEA-compliant)  
✅ Create business trips with expense claims  
✅ Generate comprehensive reports  

**Your Next Steps:**
1. Complete Quick Setup Checklist (2 hours)
2. Create test data and practice
3. Process first production payroll
4. Schedule monthly compliance tasks
5. Train your team

**Support:** If you need help, refer to Section 26 for resources.

---

**Built with ❤️ by Cohenix for the South African ERPNext community** 🇿🇦

**za_local v3.1.0** - World-Class South African Localization

---

*End of Implementation Guide*

