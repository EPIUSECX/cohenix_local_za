# 🚀 za_local - Quick Start Guide

## Installation

```bash
# Install the app
cd /workspace/development-bench
bench --site YOUR_SITE install-app za_local

# Run setup wizard
bench --site YOUR_SITE console
>>> from za_local.setup.setup_wizard import run_sa_compliance_wizard
>>> run_sa_compliance_wizard(company="Your Company")
```

## Essential Features

### 1. Monthly Payroll
```
HR > Payroll Entry > Create
→ Generate Salary Slips
→ Submit
→ SA Payroll > Payroll Payment Batch > Generate EFT File
→ SA Payroll > Reports > Statutory Submissions Summary
```

### 2. Tax Submissions
```
Monthly (EMP201):
→ SA Tax > EMP201 Submission > Create from Payslips

Annual (EMP501):
→ SA Tax > EMP501 Reconciliation > Create
→ Generate XML > Upload to SARS eFiling

Annual (IRP5):
→ SA Tax > IRP5 Certificate > Bulk Generate
→ Generate XML > Upload to SARS eFiling
```

### 3. Leave Management
```
→ HR > Leave Application (auto-validates BCEA rules)
→ Leave Allocation (BCEA-compliant types)
→ Public Holidays (12 SA holidays auto-generated)
```

### 4. Fringe Benefits
```
→ SA Payroll > Company Car Benefit (CO2-based taxation)
→ SA Payroll > Housing Benefit (rental value taxation)
→ SA Payroll > Cellphone/Fuel/Bursary Benefits
→ Auto-adds to monthly taxable income
```

### 5. Employment Equity
```
→ Employee > Employment Equity Tab (classify all employees)
→ SA EE > Reports > EEA2 Income Differentials
→ SA EE > Reports > EEA4 Employment Equity Plan
→ SA EE > Workplace Skills Plan (annual submission)
```

### 6. Employee Termination
```
→ HR > Employee Separation
→ System calculates: Notice period, Severance, Leave payout
→ Create Final Settlement
→ Generate UIF U19 Declaration
```

## Key DocTypes by Module

### SA Payroll
- Fringe Benefit
- Company Car Benefit
- Housing Benefit
- Retirement Fund
- Employee Final Settlement
- Payroll Payment Batch

### SA Tax
- IT3b Certificate
- Tax Directive
- IRP5 Certificate
- EMP201 Submission
- EMP501 Reconciliation
- UIF U19 Declaration

### SA EE
- Skills Development Record
- Workplace Skills Plan
- Annual Training Report

### SA VAT
- VAT201 Return
- VAT Reconciliation

### COIDA
- COIDA Submission
- COIDA Rate

## Quick Tips

1. **Setup First**: Run the setup wizard before processing payroll
2. **Tax Directives**: Add tax directives BEFORE payroll to reduce PAYE
3. **Fringe Benefits**: Setup early in the month for timely taxation
4. **EFT Files**: Generate after payroll submission
5. **Reports**: Run monthly for reconciliation

## Support

📖 Full Documentation: See README.md
🔧 Code Validation: See CODE_VALIDATION_REPORT.md
✅ App Information: See README.md

## Version
v3.0.0 - All 9 Phases Complete

🎉 **Ready for Production!** 🎉
