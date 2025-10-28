# ZA Local - South African Localization for ERPNext

## Overview

**ZA Local** is a comprehensive South African localization module for ERPNext and HRMS that provides essential features for businesses operating in South Africa. It covers statutory compliance requirements, tax regulations, payroll localization, and financial reporting specific to the South African context.

This module is a modernized refactoring of the kartoza app, built with clean architecture, modular design, and following modern Frappe best practices.

### Key Features

- **SARS Tax Compliance**: PAYE calculations, EMP201 monthly submissions, EMP501 bi-annual reconciliations, IRP5 tax certificates
- **Employment Tax Incentive (ETI)**: Automated ETI eligibility checking and calculations
- **Payroll Management**: UIF, SDL, and frequency-based payroll processing
- **COIDA Management**: Workplace injury tracking, OID claims, annual returns
- **VAT Management**: VAT201 returns, VAT analysis, vendor classification
- **Modern Architecture**: Modular structure with 4 focused modules (SA Payroll, SA Tax, SA VAT, COIDA)

---

## Table of Contents

1. [Installation](#installation)
2. [Module Structure](#module-structure)
3. [Features](#features)
4. [Configuration](#configuration)
5. [Custom Fields](#custom-fields)
6. [Migration from Kartoza](#migration-from-kartoza)
7. [Development](#development)
8. [Troubleshooting](#troubleshooting)
9. [License](#license)
10. [Support](#support)

---

## Installation

### Prerequisites

- ERPNext v14 or v15
- HRMS app installed
- Python 3.10+
- Frappe Framework v14 or v15

### Installation Steps

```bash
# 1. Navigate to your bench directory
cd /path/to/your/bench

# 2. Get the app
bench get-app https://github.com/your-org/za_local.git

# 3. Install on your site
bench --site your-site.local install-app za_local

# 4. Run migrations
bench --site your-site.local migrate

# 5. Clear cache
bench --site your-site.local clear-cache

# 6. Restart bench
bench restart
```

### Post-Installation

After installation, you'll see a success message with next steps. Configure the following:

1. **Company Registration Details**: Add VAT number, COIDA registration, SDL/UIF reference numbers
2. **Payroll Settings**: Configure PAYE, UIF, SDL, and COIDA salary components
3. **Tax Configuration**: Set up ETI Slabs and Tax Rebates
4. **Employee Data**: Populate SA ID numbers and employee types

---

## Module Structure

ZA Local is organized into 4 focused modules:

### 1. SA Payroll Module

Handles payroll processing frequencies and employee classifications.

**DocTypes:**
- Employee Payroll Frequency
- Employee Frequency Detail
- Employee Type
- Employee Private Benefit
- Retirement Annuity Slab
- Medical Tax Credit Rate
- Tax Rebates and Medical Tax Credit

### 2. SA Tax Module

Manages SARS submissions, PAYE, and ETI calculations.

**DocTypes:**
- EMP201 Submission (Monthly SARS return)
- EMP501 Reconciliation (Bi-annual reconciliation)
- IRP5 Certificate (Employee tax certificates)
- Employee ETI Log
- ETI Slab
- And related child tables

**Reports:**
- EMP201 Report

### 3. SA VAT Module

Handles VAT compliance and returns.

**DocTypes:**
- SA VAT Settings
- VAT201 Return
- VAT Vendor Type
- SA VAT Rate (child table)

**Reports:**
- VAT Analysis

### 4. COIDA Module

Manages workplace injuries and compensation claims.

**DocTypes:**
- COIDA Settings
- COIDA Annual Return
- Workplace Injury
- OID Claim
- OID Medical Report

---

## Features

### SARS Tax Compliance

#### PAYE (Pay As You Earn)
- Automatic PAYE calculation based on annual taxable income
- Age-based tax rebates (Primary, Secondary, Tertiary)
- Medical aid tax credits
- Retirement annuity deductions

#### Employment Tax Incentive (ETI)
- Automated eligibility checking (age 18-29)
- ETI amount calculation based on remuneration brackets
- First 12 months and second 12 months differentiation
- Pro-rating based on hours worked
- Comprehensive ETI logging for audit trails

#### EMP201 Monthly Submissions
- Automatic data collection from salary slips
- PAYE, UIF, SDL, and ETI totals
- Export functionality for SARS e-Filing
- Period-based filtering

#### EMP501 Bi-Annual Reconciliations
- Consolidation of EMP201 submissions
- IRP5 certificate reconciliation
- CSV export for SARS e-Filing
- Validation and discrepancy detection

#### IRP5 Tax Certificates
- Individual and bulk generation
- Income and deduction categorization
- SARS code mapping
- Print format included

### Payroll Management

#### Frequency-Based Processing
- Support for Monthly, Quarterly, Half-Yearly, and Yearly frequencies
- Pay at beginning or end of period
- Automatic salary slip filtering by frequency

#### Statutory Contributions
- **UIF**: 1% employee + 1% employer (capped at R17,712)
- **SDL**: 1% of gross pay (employer)
- **COIDA**: Industry-specific rates

#### Company Contributions
- Separate tracking of employer contributions
- Journal entry integration
- Bank account management per employee

### COIDA Management

- Workplace injury recording
- OID claim processing
- Medical report attachments
- Annual return generation
- Industry rate configuration

### VAT Management

- VAT201 return preparation
- Input and output VAT tracking
- Standard, zero-rated, and exempt classification
- VAT analysis reporting

---

## Configuration

### 1. Company Setup

Navigate to **Company** and configure:

```
South African Registration Details:
- VAT Number (10 digits)
- COIDA Registration Number
- SDL Reference Number
- UIF Reference Number
```

### 2. Payroll Settings

Navigate to **Payroll Settings** → **South African Settings**:

```
Configure:
- Calculate Annual Taxable Amount Based On: Payroll Period
- PAYE Salary Component
- UIF Employee Salary Component
- UIF Employer Salary Component
- SDL Salary Component
- COIDA Salary Component
```

### 3. Tax Rebates and Medical Tax Credit

Navigate to **Tax Rebates and Medical Tax Credit** (Single DocType):

```
Configure Rebate Rates:
- Primary Rebate: R17,235
- Secondary Rebate: R9,444 (age 65+)
- Tertiary Rebate: R3,145 (age 75+)

Configure Medical Tax Credit Rates:
- Main Member: R364/month
- First Dependant: R364/month
- Additional Dependants: R246/month each
```

### 4. ETI Slab

Navigate to **ETI Slab**:

```
Configure ETI Calculation Brackets:

First 12 Months:
- R0 - R2,000: 50% of remuneration
- R2,001 - R4,500: R1,000
- R4,501 - R6,500: R1,000 - (0.5 × (R - R4,500))
- Above R6,500: R0

Second 12 Months:
- R0 - R2,000: 25% of remuneration
- R2,001 - R4,500: R500
- R4,501 - R6,500: R500 - (0.25 × (R - R4,500))
- Above R6,500: R0
```

### 5. Employee Setup

For each employee, configure:

```
South African Details:
- SA ID Number (13 digits)
- Employee Type (required)
- Hours Per Month (for ETI pro-rating)
- Payroll Payable Bank Account
```

---

## Custom Fields

All custom fields use the `za_` prefix for consistency:

### Employee
- `za_id_number`: SA ID Number
- `za_employee_type`: Employee classification
- `za_hours_per_month`: Hours for ETI calculations
- `za_payroll_payable_bank_account`: Payment account

### Company
- `za_vat_number`: VAT registration number
- `za_coida_registration_number`: COIDA registration
- `za_sdl_reference_number`: SDL reference
- `za_uif_reference_number`: UIF reference

### Payroll Settings
- `za_paye_salary_component`: PAYE component
- `za_uif_employee_salary_component`: UIF employee component
- `za_uif_employer_salary_component`: UIF employer component
- `za_sdl_salary_component`: SDL component
- `za_coida_salary_component`: COIDA component
- `za_disable_eti_calculation`: Disable ETI flag

### Additional Salary
- `za_is_company_contribution`: Company contribution flag

### Salary Structure Assignment
- `za_annual_bonus`: Annual bonus amount

---

## Migration from Kartoza

### Automated Migration

If you're migrating from the kartoza app:

1. **Backup Your Site**:
   ```bash
   bench --site your-site.local backup --with-files
   ```

2. **Install za_local**:
   ```bash
   bench --site your-site.local install-app za_local
   ```

3. **Data Migration**:
   - All DocTypes are compatible (same names)
   - Custom field names changed from `custom_` to `za_` prefix
   - Data migration script will handle field renaming

4. **Uninstall kartoza** (optional):
   ```bash
   bench --site your-site.local uninstall-app kartoza
   ```

### Key Changes

1. **Field Naming**: `custom_id_number` → `za_id_number`
2. **Module Structure**: Single module → 4 focused modules
3. **Code Organization**: Monolithic files → Clean utilities
4. **Hooks**: Updated to use modern Frappe patterns

---

## Development

### Adding New Features

1. **Create DocType**:
   ```bash
   bench --site your-site.local make-doctype "New Feature" za_local
   ```

2. **Choose appropriate module**: SA Payroll, SA Tax, SA VAT, or COIDA

3. **Update workspace** in `za_local/config/[module].py`

### Running Tests

```bash
bench --site your-site.local run-tests --app za_local
```

### Code Quality

- Follow PEP 8 for Python code
- Use ESLint for JavaScript
- Document all functions with docstrings
- Write unit tests for critical functions

---

## Troubleshooting

### Common Issues

#### Issue: Custom fields not showing

**Solution**:
```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

#### Issue: ETI not calculating

**Check**:
1. ETI not disabled in Payroll Settings
2. Employee age between 18-29
3. Employee has SA ID number
4. ETI Slab is configured
5. Employee employed ≤ 24 months

#### Issue: PAYE calculation incorrect

**Check**:
1. Tax rebates configured correctly
2. Medical aid dependants set
3. Income Tax Slab active
4. Payroll period configured

#### Issue: Salary slip validation errors

**Check**:
1. All salary components have accounts
2. Employee has bank account set
3. Employee type is set
4. Payroll frequency configured

---

## License

MIT License

Copyright (c) 2025 Cohenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Support

### Documentation
- [Comprehensive Guide](docs/comprehensive_guide.md)
- [API Reference](docs/api_reference.md)
- [Tax Guide](docs/tax_guide.md)

### Community
- GitHub Issues: [Report bugs or request features](https://github.com/your-org/za_local/issues)
- Discussions: [Ask questions and share knowledge](https://github.com/your-org/za_local/discussions)

### Professional Support
For professional support, customization, or implementation services:
- Email: info@cohenix.com
- Website: https://cohenix.com

---

## Contributors

This app is a modernized refactoring of the original kartoza South African localization app, rebuilt with clean architecture and modern Frappe practices.

### Maintainers
- Cohenix Team

### Credits
- Original kartoza app by Aerele
- ERPNext and Frappe communities

---

## Changelog

### Version 1.0.0 (2025)
- Initial release as modern refactoring of kartoza
- 4 focused modules (SA Payroll, SA Tax, SA VAT, COIDA)
- 30+ DocTypes migrated and modernized
- Clean utility functions for tax, ETI, COIDA, VAT
- Comprehensive custom fields with za_ prefix
- Modern controller overrides
- Complete documentation

---

**Built with ❤️ by Cohenix for the South African ERPNext community**
