# ZA Local v3.4.0 - Print Format & Customer VAT Enhancements

## Release Date
January 30, 2025

## 🎯 Overview
Major fixes and enhancements for SA-compliant print formats and customer VAT management.

## ✨ New Features

### Customer VAT Management
- **VAT Registration Field**: `tax_id` field on Customer DocType now labeled as "VAT Registration Number"
- **Company Registration**: New `za_company_registration` field for CIPC registration numbers
- **VAT Vendor Flag**: New `za_is_vat_vendor` checkbox to identify VAT-registered customers
- **Automatic Validation**: Real-time validation of SA VAT number format (10 digits, starts with 4)
- **Warning Messages**: User-friendly alerts for invalid VAT formats

### Print Format Improvements
- **Fixed HTML Rendering**: All print formats now correctly display in ERPNext
- **Dynamic Customer VAT**: Print templates now fetch customer VAT from Customer DocType
- **Embedded Templates**: HTML now embedded directly in JSON for reliable loading
- **Module Assignment**: All print formats correctly assigned to "SA Tax" module

## 🔧 Technical Changes

### Files Modified
1. **Custom Fields** (`za_local/setup/custom_fields.py`)
   - Added Customer custom fields (za_company_registration, za_is_vat_vendor)
   - Added property setter to relabel tax_id field
   
2. **Customer Validation** (`za_local/custom/customer.py`)
   - New validation hook for SA VAT number format
   - Automatic cleanup of VAT number (remove spaces/hyphens)
   - Warning messages for non-standard formats

3. **Hooks** (`za_local/hooks.py`)
   - Added Customer validation hook
   - Print format fixtures updated

4. **Print Formats** (all 9 formats)
   - HTML embedded in JSON files
   - Customer VAT lookup updated to use Customer.tax_id
   - Module changed from "ZA Local" to "SA Tax"

5. **Version** (`za_local/__init__.py`)
   - Bumped to 3.4.0

### Database Changes
- New custom fields on Customer DocType
- Property setter for tax_id label
- 9 print formats imported and registered

## 📋 Print Formats Included
1. SA Sales Invoice (Full/Abridged auto-detection)
2. SA Quotation
3. SA Sales Order
4. SA Delivery Note
5. SA Purchase Invoice
6. SA Purchase Order
7. SA Payment Entry
8. SA Credit Note
9. SA Debit Note
10. IT3b Certificate Print

## 🔍 Validation Rules

### SA VAT Number Format
- **Length**: Exactly 10 digits
- **Prefix**: Typically starts with 4 (warning if not)
- **Format**: Numbers only (spaces/hyphens automatically removed)
- **Example**: 4123456789

## 🚀 Installation/Upgrade

```bash
cd /path/to/bench
bench get-app --branch main https://github.com/your-repo/za_local
bench --site your-site migrate
bench --site your-site restart
```

## 📝 Breaking Changes
None - all changes are backward compatible.

## 🐛 Bug Fixes
- Fixed print formats not appearing in dropdown
- Fixed customer VAT not displaying on invoices
- Fixed module reference errors during import
- Fixed HTML template loading issues

## 💡 Usage

### Customer VAT Setup
1. Go to Customer list
2. Open any customer
3. Fill in "VAT Registration Number" field (10 digits)
4. Optionally fill "Company Registration Number"
5. Check "Is VAT Vendor" if applicable
6. Save - validation will run automatically

### Using Print Formats
1. Open any Sales Invoice, Quotation, etc.
2. Click "Print" button
3. Select from available SA print formats in dropdown
4. Formats are automatically set as default for SA companies

## 🔗 Dependencies
- ERPNext v15.x
- Frappe v15.x
- PyPDF2 >= 3.0.0
- reportlab >= 4.0.0

## 📞 Support
For issues or questions, please visit:
- GitHub: https://github.com/your-repo/za_local/issues
- Documentation: https://github.com/your-repo/za_local/wiki

---

**Full Changelog**: v3.3.0...v3.4.0
