#!/usr/bin/env python3
"""
Test Script for ZA Local Data Loading

This script validates that all JSON and CSV data files are correctly
structured and can be loaded into the database without errors.

Run with:
    bench --site your-site.local execute za_local.test_data_loading.run_all_tests
"""

import frappe
from frappe import _
from pathlib import Path
import json


def run_all_tests():
	"""Run all data loading tests"""
	print("\n" + "="*70)
	print("  ZA LOCAL DATA LOADING VALIDATION TEST")
	print("="*70 + "\n")
	
	tests = [
		test_json_files_syntax,
		test_payroll_period_structure,
		test_tax_rebates_structure,
		test_income_tax_slab_structure,
		test_salary_components_structure,
		test_csv_files_exist,
		test_actual_data_loading,
	]
	
	passed = 0
	failed = 0
	
	for test in tests:
		try:
			test()
			passed += 1
			print(f"✓ PASSED\n")
		except AssertionError as e:
			failed += 1
			print(f"✗ FAILED: {e}\n")
		except Exception as e:
			failed += 1
			print(f"✗ ERROR: {e}\n")
			import traceback
			traceback.print_exc()
	
	print("\n" + "="*70)
	print(f"  RESULTS: {passed} passed, {failed} failed")
	print("="*70 + "\n")
	
	return passed, failed


def test_json_files_syntax():
	"""Test 1: Validate JSON syntax of all data files"""
	print("TEST 1: Validating JSON file syntax...")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	json_files = [
		"payroll_period_2024.json",
		"salary_components.json",
		"earnings_components.json",
		"tax_slabs_2024.json",
		"tax_rebates_2024.json",
	]
	
	for filename in json_files:
		filepath = data_dir / filename
		assert filepath.exists(), f"File not found: {filename}"
		
		with open(filepath, "r") as f:
			data = json.load(f)  # Will raise JSONDecodeError if invalid
		
		print(f"  ✓ {filename}: Valid JSON")
	
	print(f"  All {len(json_files)} JSON files have valid syntax")


def test_payroll_period_structure():
	"""Test 2: Validate Payroll Period JSON structure"""
	print("\nTEST 2: Validating Payroll Period structure...")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	filepath = data_dir / "payroll_period_2024.json"
	
	with open(filepath, "r") as f:
		data = json.load(f)
	
	assert isinstance(data, list), "Should be a list"
	assert len(data) == 1, "Should contain 1 record"
	
	record = data[0]
	assert record.get("doctype") == "Payroll Period", "Wrong doctype"
	assert record.get("name") == "2024-2025", "Wrong name"
	assert record.get("start_date") == "2024-03-01", "Wrong start date"
	assert record.get("end_date") == "2025-02-28", "Wrong end date"
	
	print("  ✓ Payroll Period structure is correct")
	print(f"    - Name: {record['name']}")
	print(f"    - Period: {record['start_date']} to {record['end_date']}")


def test_tax_rebates_structure():
	"""Test 3: Validate Tax Rebates JSON structure"""
	print("\nTEST 3: Validating Tax Rebates structure...")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	filepath = data_dir / "tax_rebates_2024.json"
	
	with open(filepath, "r") as f:
		data = json.load(f)
	
	assert isinstance(data, dict), "Should be a dict (Single DocType)"
	assert data.get("doctype") == "Tax Rebates and Medical Tax Credit", "Wrong doctype"
	assert data.get("name") == "Tax Rebates and Medical Tax Credit", "Wrong name for Single"
	
	# Check Tax Rebates Rate child table
	rebates = data.get("tax_rebates_rate", [])
	assert len(rebates) == 1, "Should have 1 tax rebate row"
	rebate = rebates[0]
	assert rebate.get("payroll_period") == "2024-2025", "Wrong payroll period"
	assert rebate.get("primary") == 17235, "Wrong primary rebate"
	assert rebate.get("secondary") == 9444, "Wrong secondary rebate"
	assert rebate.get("tertiary") == 3145, "Wrong tertiary rebate"
	
	# Check Medical Tax Credit child table
	medical = data.get("medical_tax_credit", [])
	assert len(medical) == 1, "Should have 1 medical tax credit row"
	med = medical[0]
	assert med.get("payroll_period") == "2024-2025", "Wrong payroll period"
	assert med.get("one_dependant") == 364, "Wrong one dependant credit"
	assert med.get("two_dependant") == 610, "Wrong two dependant credit"
	assert med.get("additional_dependant") == 410, "Wrong additional dependant credit"
	
	print("  ✓ Tax Rebates structure is correct")
	print(f"    - Primary Rebate: R{rebate['primary']:,}")
	print(f"    - Medical (1 dep): R{med['one_dependant']}")
	print(f"    - Medical (2 dep): R{med['two_dependant']}")


def test_income_tax_slab_structure():
	"""Test 4: Validate Income Tax Slab JSON structure"""
	print("\nTEST 4: Validating Income Tax Slab structure...")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	filepath = data_dir / "tax_slabs_2024.json"
	
	with open(filepath, "r") as f:
		data = json.load(f)
	
	assert isinstance(data, list), "Should be a list"
	assert len(data) == 1, "Should contain 1 record"
	
	record = data[0]
	assert record.get("doctype") == "Income Tax Slab", "Wrong doctype"
	assert record.get("name") == "South Africa 2024-2025", "Wrong name"
	assert record.get("effective_from") == "2024-03-01", "Wrong effective date"
	assert record.get("currency") == "ZAR", "Wrong currency"
	
	# Check child table
	slabs = record.get("slabs", [])
	assert len(slabs) == 8, f"Should have 8 slabs, found {len(slabs)}"
	
	# Validate slab structure
	for i, slab in enumerate(slabs, 1):
		assert "from_amount" in slab, f"Slab {i} missing from_amount"
		assert "to_amount" in slab, f"Slab {i} missing to_amount"
		assert "percent_deduction" in slab, f"Slab {i} missing percent_deduction"
	
	print("  ✓ Income Tax Slab structure is correct")
	print(f"    - Name: {record['name']}")
	print(f"    - Currency: {record['currency']}")
	print(f"    - Slabs: {len(slabs)} brackets (18% to 45%)")


def test_salary_components_structure():
	"""Test 5: Validate Salary Components JSON structure"""
	print("\nTEST 5: Validating Salary Components structure...")
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	
	# Test statutory components
	filepath = data_dir / "salary_components.json"
	with open(filepath, "r") as f:
		data = json.load(f)
	
	assert isinstance(data, list), "Should be a list"
	assert len(data) == 4, f"Should have 4 components, found {len(data)}"
	
	expected_names = {
		"PAYE",
		"UIF Employee Contribution",
		"UIF Employer Contribution",
		"SDL Contribution",
	}
	assert {comp["salary_component"] for comp in data} == expected_names, (
		"Statutory salary components must match the expected ZA Local set without SARS code prefixes"
	)
	
	type_map = {comp["salary_component"]: comp.get("type") for comp in data}
	assert type_map.get("UIF Employer Contribution") == "Company Contribution", (
		"UIF Employer Contribution must load as Company Contribution"
	)
	assert type_map.get("SDL Contribution") == "Company Contribution", (
		"SDL Contribution must load as Company Contribution"
	)
	assert type_map.get("UIF Employee Contribution") == "Deduction", (
		"UIF Employee Contribution must remain a Deduction"
	)

	formula_map = {comp["salary_component"]: comp.get("formula") for comp in data}
	expected_uif_formula = "(gross_pay * 0.01) if (gross_pay * 0.01) <= 177.12 else 177.12"
	expected_sdl_formula = "gross_pay * 0.01"
	assert formula_map.get("UIF Employee Contribution") == expected_uif_formula, (
		"UIF Employee Contribution must cap at 177.12 using gross pay"
	)
	assert formula_map.get("UIF Employer Contribution") == expected_uif_formula, (
		"UIF Employer Contribution must cap at 177.12 using gross pay"
	)
	assert formula_map.get("SDL Contribution") == expected_sdl_formula, (
		"SDL Contribution must calculate at 1% of gross pay"
	)
	
	for comp in data:
		assert comp.get("doctype") == "Salary Component", "Wrong doctype"
		assert "salary_component" in comp, "Missing salary_component"
		assert "salary_component_abbr" in comp, "Missing abbr"
		assert "type" in comp, "Missing type"
	
	print(f"  ✓ Statutory Salary Components: {len(data)} components")
	
	# Test earnings components
	filepath = data_dir / "earnings_components.json"
	with open(filepath, "r") as f:
		data = json.load(f)
	
	assert isinstance(data, list), "Should be a list"
	assert len(data) == 7, f"Should have 7 components, found {len(data)}"
	
	print(f"  ✓ Earnings Components: {len(data)} components")
	print(f"  Total: {4 + 7} = 11 Salary Components")


def test_csv_files_exist():
	"""Test 6: Validate CSV files exist and have headers"""
	print("\nTEST 6: Validating CSV files...")
	
	data_dir = Path(frappe.get_app_path("za_local", "data"))
	csv_files = [
		"business_trip_region.csv",
		"bargaining_council_list.csv",
		"seta_list.csv",
	]
	
	for filename in csv_files:
		filepath = data_dir / filename
		assert filepath.exists(), f"File not found: {filename}"
		
		# Read first line (header)
		with open(filepath, "r") as f:
			header = f.readline().strip()
		
		assert len(header) > 0, f"{filename} is empty"
		assert "," in header, f"{filename} doesn't appear to be CSV"
		
		print(f"  ✓ {filename}: Exists and has headers")


def test_actual_data_loading():
	"""Test 7: Actually load data and verify in database"""
	print("\nTEST 7: Testing actual data loading...")
	
	from za_local.setup.install import load_data_from_json
	from pathlib import Path
	
	data_dir = Path(frappe.get_app_path("za_local", "setup", "data"))
	
	# Start transaction (will rollback at end)
	frappe.db.begin()
	
	try:
		# 1. Load Payroll Period
		print("  Loading Payroll Period...")
		load_data_from_json(data_dir / "payroll_period_2024.json")
		
		# Verify it exists
		assert frappe.db.exists("Payroll Period", "2024-2025"), "Payroll Period not created"
		pp = frappe.get_doc("Payroll Period", "2024-2025")
		assert pp.start_date.isoformat() == "2024-03-01", "Wrong start date"
		print("    ✓ Payroll Period loaded")
		
		# 2. Load Tax Rebates
		print("  Loading Tax Rebates...")
		load_data_from_json(data_dir / "tax_rebates_2024.json")
		
		# Verify Single DocType was updated
		tax_doc = frappe.get_single("Tax Rebates and Medical Tax Credit")
		assert len(tax_doc.tax_rebates_rate) > 0, "No tax rebates loaded"
		assert len(tax_doc.medical_tax_credit) > 0, "No medical credits loaded"
		print("    ✓ Tax Rebates loaded")
		
		# 3. Load Income Tax Slab
		print("  Loading Income Tax Slab...")
		load_data_from_json(data_dir / "tax_slabs_2024.json")
		
		assert frappe.db.exists("Income Tax Slab", "South Africa 2024-2025"), "Tax Slab not created"
		slab = frappe.get_doc("Income Tax Slab", "South Africa 2024-2025")
		assert len(slab.slabs) == 8, f"Expected 8 slabs, found {len(slab.slabs)}"
		print("    ✓ Income Tax Slab loaded")
		
		# 4. Load Salary Components
		print("  Loading Salary Components...")
		load_data_from_json(data_dir / "salary_components.json")
		load_data_from_json(data_dir / "earnings_components.json")
		
		assert frappe.db.exists("Salary Component", "4102 PAYE"), "PAYE not created"
		assert frappe.db.exists("Salary Component", "Basic Salary"), "Basic Salary not created"
		print("    ✓ Salary Components loaded")
		
		# 5. Load Business Trip Regions
		print("  Loading Business Trip Regions...")
		from za_local.utils.csv_importer import import_csv_data
		stats = import_csv_data("Business Trip Region", "business_trip_region.csv")
		assert stats["created"] > 0 or stats["skipped"] > 0, "No regions loaded"
		print(f"    ✓ Business Trip Regions loaded ({stats['created']} created, {stats['skipped']} skipped)")
		
		print("\n  All data loaded successfully!")
		
	finally:
		# Rollback transaction (don't save test data)
		frappe.db.rollback()
		print("  (Changes rolled back - test only)")


if __name__ == "__main__":
	# For running outside Frappe context
	print("Please run with: bench --site your-site.local execute za_local.test_data_loading.run_all_tests")

