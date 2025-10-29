# Quick Setup Checklist - za_local

Fast-track setup guide for South African Localization. Follow this checklist for a complete installation in 2-4 hours.

## 📋 Pre-Installation

- [ ] ERPNext v14/15 installed
- [ ] HRMS app installed
- [ ] Python 3.10+ confirmed
- [ ] Database backup taken
- [ ] Admin access confirmed

## 🔧 Installation (30 minutes)

### Step 1: Install App
```bash
# Get the app
cd /path/to/frappe-bench
bench get-app za_local

# Install on site
bench --site your-site.local install-app za_local

# Run migrations
bench --site your-site.local migrate

# Clear cache
bench --site your-site.local clear-cache
bench restart
```

- [ ] App installed successfully
- [ ] No errors in console
- [ ] Modules visible in sidebar

### Step 2: Verify Installation
- [ ] SA Payroll module visible
- [ ] SA Tax module visible
- [ ] SA VAT module visible
- [ ] COIDA module visible
- [ ] SA EE module visible
- [ ] Custom fields on Employee visible
- [ ] Custom fields on Company visible

## 🏢 Company Configuration (15 minutes)

Navigate to: **Setup > Company > [Your Company]**

### SA Registration Details Section
- [ ] PAYE Registration Number (10 digits)
- [ ] UIF Reference Number (8-9 digits)
- [ ] SDL Reference Number
- [ ] COIDA Registration Number (if applicable)
- [ ] VAT Number (10 digits, if registered)
- [ ] SETA selected
- [ ] Bargaining Council (if applicable)

**Save** the company record.

## 💰 Tax Configuration (45 minutes)

### Step 1: Tax Rebates
Navigate to: **SA Payroll > Tax Rebates and Medical Tax Credit**

- [ ] Primary Rebate: R17,235 (2024-2025)
- [ ] Secondary Rebate: R9,444 (65+)
- [ ] Tertiary Rebate: R3,145 (75+)
- [ ] Medical Tax Credit Rates table populated
  - [ ] Main Member: R364/month
  - [ ] First Dependant: R364/month
  - [ ] Additional: R246/month each
- [ ] **Save**

### Step 2: ETI Slabs
Navigate to: **SA Tax > ETI Slab > New**

**First 12 Months:**
- [ ] Slab Name: "ETI First 12 Months"
- [ ] Period: First 12 Months
- [ ] Effective From: 2024-03-01
- [ ] Slab details table:
  - [ ] R0-R2,000: 50%
  - [ ] R2,001-R4,500: R1,000
  - [ ] R4,501-R6,500: Declining
  - [ ] R6,501+: R0
- [ ] **Submit**

**Second 12 Months:**
- [ ] Slab Name: "ETI Second 12 Months"
- [ ] Period: Second 12 Months
- [ ] Same date range
- [ ] Slab details: 25% rates (half of first 12)
- [ ] **Submit**

## 👥 Payroll Configuration (30 minutes)

### Step 1: Payroll Settings
Navigate to: **HRMS Settings > Payroll Settings**

**SA Settings Section:**
- [ ] Calculate Annual Taxable Amount: "Payroll Period"
- [ ] Disable ETI Calculation: Unchecked

**Statutory Components:**
- [ ] PAYE Salary Component: "PAYE"
- [ ] UIF Employee Component: "UIF Employee"
- [ ] UIF Employer Component: "UIF Employer"
- [ ] SDL Component: "SDL"
- [ ] COIDA Component: "COIDA" (if applicable)
- [ ] **Save**

### Step 2: Create Salary Components
If not auto-created, manually create:
- [ ] PAYE (Deduction, Tax Component)
- [ ] UIF Employee (Deduction, 1%, max R177.12)
- [ ] UIF Employer (Company Contribution, 1%, max R177.12)
- [ ] SDL (Deduction, 1%)

### Step 3: Create Salary Structure
Navigate to: **Payroll > Salary Structure > New**

- [ ] Name: "SA Standard Monthly Salary"
- [ ] Company: Your company
- [ ] Is Active: Yes
- [ ] Earnings: Basic, Housing, Travel (as needed)
- [ ] Deductions: PAYE, UIF, SDL, Retirement Fund
- [ ] Company Contributions: UIF Employer, SDL Employer
- [ ] **Save**

## 🏖️ Leave Management (20 minutes)

### Verify Leave Types
Navigate to: **HR > Leave Type**

Confirm these 6 BCEA leave types exist:
- [ ] Annual Leave (SA) - 21 days
- [ ] Sick Leave (SA) - 36 days per 3 years
- [ ] Family Responsibility Leave (SA) - 3 days
- [ ] Maternity Leave (SA) - 4 months
- [ ] Study Leave (SA)
- [ ] Unpaid Leave (SA)

### Create Holiday List
Navigate to: **HR > Holiday List > New**

- [ ] Name: "SA Public Holidays 2024"
- [ ] From Date: 2024-01-01
- [ ] To Date: 2024-12-31
- [ ] Add 12 SA public holidays
- [ ] **Save**
- [ ] Set as Default Holiday List in Company

## ✈️ Business Trip Setup (15 minutes)

### Step 1: Business Trip Settings
Navigate to: **SA Payroll > Business Trip Settings**

- [ ] Mileage Allowance Rate: R4.25/km
- [ ] Meal Expense Claim Type: "Travel"
- [ ] Mileage Expense Claim Type: "Travel"
- [ ] Require Manager Approval: Checked
- [ ] Auto Create Expense Claim: Checked
- [ ] **Save**

### Step 2: Verify Business Trip Regions
Navigate to: **SA Payroll > Business Trip Region**

- [ ] Confirm 16 regions loaded (Johannesburg, Cape Town, etc.)
- [ ] Add custom regions if needed

## 👤 Create First Employee (15 minutes)

Navigate to: **HR > Employee > New**

### Basic Details
- [ ] First Name, Last Name
- [ ] Gender, Date of Birth
- [ ] Date of Joining
- [ ] Company
- [ ] Department, Designation

### SA Registration Details
- [ ] SA ID Number (13 digits)
- [ ] Employee Type
- [ ] Hours Per Month: 160 (for monthly employees)
- [ ] Bank Account linked

### Employment Equity
- [ ] Race classification
- [ ] Occupational Level
- [ ] Disability status (if applicable)

### Leave Allocation
- [ ] Annual Leave: 21 days
- [ ] Sick Leave: 12 days
- [ ] Family Responsibility: 3 days

### Salary Structure Assignment
- [ ] Assign "SA Standard Monthly Salary"
- [ ] Set Base salary amount
- [ ] **Submit**

## 💵 Process Test Payroll (30 minutes)

### Create Payroll Entry
Navigate to: **Payroll > Payroll Entry > New**

- [ ] Company: Your company
- [ ] Payroll Frequency: Monthly
- [ ] Start Date: First of month
- [ ] End Date: Last of month
- [ ] Get Employees
- [ ] Create Salary Slips
- [ ] Review salary slips
  - [ ] PAYE calculated
  - [ ] UIF calculated (1%, max R177.12)
  - [ ] SDL calculated (1%)
  - [ ] Net Pay reasonable
- [ ] **Submit** Payroll Entry

### Generate EMP201
Navigate to: **SA Tax > EMP201 Submission > New**

- [ ] Select current month
- [ ] Fetch from Salary Slips
- [ ] Verify totals:
  - [ ] PAYE amount
  - [ ] UIF amount (employee + employer)
  - [ ] SDL amount
  - [ ] ETI amount (if applicable)
- [ ] **Submit**

## ✈️ Test Business Trip (Optional, 20 minutes)

Navigate to: **SA Payroll > Business Trip > New**

- [ ] Select Employee
- [ ] Trip Purpose: "Test Trip"
- [ ] From/To Dates
- [ ] Click "Generate Allowances"
- [ ] Select regions for each day
- [ ] Add journey (private car with distance)
- [ ] **Submit**
- [ ] Click "Create Expense Claim"
- [ ] Verify Expense Claim created

## ✅ Final Verification

### System Check
- [ ] All modules accessible
- [ ] No console errors
- [ ] Custom fields visible
- [ ] DocType links working (Connections tab)

### Compliance Check
- [ ] Statutory components configured
- [ ] Tax calculations correct
- [ ] Leave types compliant with BCEA
- [ ] Public holidays loaded
- [ ] ETI eligibility checking

### Documentation
- [ ] README.md reviewed
- [ ] IMPLEMENTATION_GUIDE.md bookmarked
- [ ] Support contacts noted

## 🎉 Setup Complete!

**Total Time**: ~2.5 hours (first time), ~1 hour (subsequent)

### What's Next?

1. **Configure remaining employees**
2. **Setup COIDA rates** (if applicable)
3. **Configure VAT settings** (if VAT registered)
4. **Setup Employment Equity** classifications
5. **Configure SETA and Skills Development**
6. **Review Business Trip workflow**
7. **Setup approval workflows**
8. **Train HR staff**

### Monthly Operations

- **By 7th**: Submit EMP201 to SARS
- **Monthly**: Process payroll
- **Quarterly**: EEA reporting (if required)
- **Annually**: IRP5/EMP501 reconciliation (May 31)

### Need Help?

- 📖 **Full Guide**: See `IMPLEMENTATION_GUIDE.md`
- 🔧 **Validation**: See `CODE_VALIDATION_REPORT.md`
- 📝 **README**: See `README.md`
- 💬 **Support**: Contact Cohenix or raise GitHub issue

---

**Congratulations!** 🎊 Your SA localization is configured and ready for production use.

