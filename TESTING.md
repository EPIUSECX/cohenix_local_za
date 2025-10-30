# Testing Guide for ZA Local

## Quick Test

To validate all data files load correctly:

```bash
bench --site your-site.local execute za_local.test_data_loading.run_all_tests
```

## What Gets Tested

The test script validates:

1. **JSON File Syntax** - All JSON files are valid
2. **Payroll Period Structure** - Correct fields and values
3. **Tax Rebates Structure** - Single DocType with child tables
4. **Income Tax Slab Structure** - Parent with 7 child slabs
5. **Salary Components Structure** - All 11 components
6. **CSV Files** - All CSV files exist with headers
7. **Actual Data Loading** - Real database insert test (rolled back)

## Expected Output

```
======================================================================
  ZA LOCAL DATA LOADING VALIDATION TEST
======================================================================

TEST 1: Validating JSON file syntax...
✓ PASSED

TEST 2: Validating Payroll Period structure...
✓ PASSED

TEST 3: Validating Tax Rebates structure...
✓ PASSED

TEST 4: Validating Income Tax Slab structure...
✓ PASSED

TEST 5: Validating Salary Components structure...
✓ PASSED

TEST 6: Validating CSV files...
✓ PASSED

TEST 7: Testing actual data loading...
✓ PASSED

======================================================================
  RESULTS: 7 passed, 0 failed
======================================================================
```

## Before Deploying to Production

Always run the test script after:
- Modifying any JSON data files
- Changing `install.py` or `setup_wizard.py`
- Updating SARS rates or rebates
- Adding new data files

## Test Data Files

The following files are validated:

**JSON Files:**
- `setup/data/payroll_period_2024.json` - Payroll Period (2024-2025)
- `setup/data/salary_components.json` - 4 statutory components
- `setup/data/earnings_components.json` - 7 earnings components
- `setup/data/tax_slabs_2024.json` - Income Tax Slab with 7 brackets
- `setup/data/tax_rebates_2024.json` - Tax Rebates & Medical Credits

**CSV Files:**
- `data/business_trip_region.csv` - 16 regions
- `data/bargaining_council_list.csv` - Bargaining councils
- `data/seta_list.csv` - SETA list

## Troubleshooting

### Test Fails on JSON Syntax
- Check JSON file for syntax errors (missing commas, brackets)
- Use a JSON validator: https://jsonlint.com/

### Test Fails on Structure
- Compare your JSON structure to HRMS DocType definitions
- Check field names match exactly (case-sensitive)
- Verify child table structures

### Test Fails on Data Loading
- Check if required dependencies exist (e.g., Payroll Period before Tax Rebates)
- Review error messages for missing fields
- Check database logs: `bench --site your-site.local console`

## Manual Testing in UI

After automated tests pass, manually verify in the UI:

1. **Payroll Period**
   - Navigate to: Payroll > Payroll Period
   - Should see: "2024-2025" (March 1, 2024 - Feb 28, 2025)

2. **Tax Rebates**
   - Navigate to: SA Payroll > Tax Rebates and Medical Tax Credit
   - Should see rebates and medical credits populated

3. **Income Tax Slab**
   - Navigate to: Payroll > Income Tax Slab
   - Open: "South Africa 2024-2025"
   - Should see: 7 tax brackets from 18% to 45%

4. **Salary Components**
   - Navigate to: Payroll > Salary Component
   - Should see: 11 components (PAYE, UIF, SDL, Basic, etc.)

5. **Business Trip Regions**
   - Navigate to: SA Payroll > Business Trip Region
   - Should see: 16 regions with rates

## Version History

- **v3.2.0** - Fixed all data loading issues, added comprehensive test suite
- **v3.1.0** - Initial data files (had structure issues)

## Support

For issues with testing or data loading:
- Check GitHub Issues: https://github.com/your-org/za_local/issues
- Email: info@cohenix.com


