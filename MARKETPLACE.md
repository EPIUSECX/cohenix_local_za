# ZA Local - South African Localization for ERPNext

**Complete compliance solution for South African businesses**

## What is ZA Local?

ZA Local is a comprehensive South African localization module for ERPNext that handles all statutory compliance requirements, tax regulations, payroll management, and SARS-compliant document generation. Built following modern Frappe best practices, it integrates seamlessly into ERPNext's setup wizard for instant deployment.

## Why Choose ZA Local?

### 🚀 **Instant Setup**
- Integrated into ERPNext setup wizard
- Automatic activation when "South Africa" is selected
- Pre-configured defaults loaded in 15 minutes
- No command-line knowledge required

### 🖨️ **Professional, SARS-Compliant Documents**
- **Tax Invoices** with automatic Full/Abridged detection (R5,000 threshold)
- **Quotations, Sales Orders, Delivery Notes**
- **Purchase Documents** (Invoices, Orders)
- **Payment Receipts, Credit/Debit Notes**
- All include VAT breakdown, company branding, sequential numbering
- Automatically set as default print formats

### 💰 **Complete Tax Compliance**
- **PAYE** calculations with 2024-2025 tax tables
- **EMP201** monthly PAYE/UIF/SDL submissions
- **EMP501** bi-annual reconciliations
- **IRP5** employee tax certificates
- **IT3(b)** employer reconciliation declarations with PDF generation
- **Bulk IT3(b) Generation** tool with progress tracking
- **Employment Tax Incentive (ETI)** calculations

### 💼 **Payroll Management**
- **UIF** (Unemployment Insurance Fund) calculations
- **SDL** (Skills Development Levy) at 1%
- **Frequency-based payroll** (Weekly, Bi-weekly, Monthly)
- **Fringe benefits** management
- **Leave encashment** with tax calculations
- **Final settlements** automation

### 📊 **VAT Management**
- **VAT201** returns generation
- **VAT analysis** reports
- VAT vendor classification
- Input/Output VAT tracking
- SARS-compliant VAT invoicing

### 🏥 **COIDA Compliance**
- Workplace injury tracking
- OID (Occupational Injuries Database) claims
- Annual COIDA returns
- Industry-specific rates

### 🏛️ **Employment Equity & BEE**
- EE workforce demographics
- EE reports (EEA2, EEA4)
- Skills development tracking
- Workplace Skills Plan (WSP)
- BEE scorecard integration

### ✈️ **Business Trip Management**
- SARS-compliant mileage tracking
- Travel allowance calculations
- Accommodation and expense management
- Regional rates (SA business trip regions)

## What Gets Loaded During Setup?

When you complete the ERPNext setup wizard with "South Africa" selected:

✅ **Salary Components**
- PAYE (Pay As You Earn)
- UIF Employee & Employer Contributions
- Skills Development Levy (SDL)

✅ **Earnings Components**
- Basic Salary, Housing Allowance
- Travel Allowance, Medical Aid
- Commission, Overtime, Bonus

✅ **Tax Tables (2024-2025)**
- 7-bracket income tax slabs
- Primary, secondary, tertiary rebates
- Medical tax credits

✅ **Print Formats**
- 9 SARS-compliant document templates
- Automatic Full/Abridged invoice detection
- Professional, branded layouts

✅ **Payroll Period**
- SA tax year (March to February)
- 2024-2025 period pre-configured

✅ **Master Data**
- SA business trip regions
- Public holidays
- SETA classifications

## Who Is This For?

- **South African businesses** using ERPNext
- **Accounting firms** managing multiple SA clients
- **HR departments** handling SA payroll
- **Companies** needing SARS compliance
- **Organizations** requiring professional invoicing

## Technical Specifications

- **Compatibility**: ERPNext v15.x+, Frappe v15.x+, HRMS v15.x+
- **Python**: 3.10+
- **License**: MIT
- **Architecture**: Modular design with 5 focused modules
- **Dependencies**: PyPDF2, reportlab for PDF generation

## Module Structure

```
za_local/
├── sa_payroll/     # Payroll, UIF, SDL, fringe benefits
├── sa_tax/         # PAYE, EMP201, EMP501, IRP5, IT3(b)
├── sa_vat/         # VAT201, VAT analysis
├── coida/          # Workplace injuries, OID claims
├── sa_ee/          # Employment Equity, Skills Development
├── print_format/   # SARS-compliant document templates
└── setup/          # Setup wizard integration
```

## Support & Documentation

- **Implementation Guide**: Comprehensive step-by-step setup
- **Quick Setup Checklist**: 30-minute configuration guide
- **Testing Guide**: Data validation scripts
- **Issue Tracking**: GitHub issues
- **Community**: Frappe Forum

## Version History

### Version 3.3.0 (Latest)
- **NEW**: 9 SA-compliant print formats with auto-detection
- **NEW**: IT3(b) Certificate PDF generation
- **NEW**: Bulk IT3(b) generation tool
- **ENHANCED**: Automatic print format setup during installation
- **TECHNICAL**: Added PyPDF2 and reportlab dependencies

### Version 3.2.0
- Integrated setup wizard
- Automatic data loading
- PyPDF2 dependency fix

### Version 3.1.0
- COIDA integration
- ETI automation
- Enhanced VAT features

## Get Started Today

1. Install ERPNext and za_local apps
2. Run ERPNext setup wizard
3. Select "South Africa" as your country
4. Complete the za_local setup page
5. Start invoicing and processing payroll! ✅

## License

MIT License - Free for commercial and personal use

## Author

**Cohenix**  
Email: info@cohenix.com  
Specialized in ERPNext implementations for South African businesses

