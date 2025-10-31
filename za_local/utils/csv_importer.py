# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
CSV Data Import Utility

Provides generic functions for importing master data from CSV files
into Frappe DocTypes. Used for loading predefined data like business
trip regions, SETAs, bargaining councils, etc.
"""

import contextlib
from csv import DictReader
from pathlib import Path

import frappe
from frappe.exceptions import DuplicateEntryError


def import_csv_data(doctype, csv_filename, update_existing=False):
	"""
	Import CSV data into a specified DocType.
	
	Args:
		doctype: Name of the DocType to import data into
		csv_filename: Name of the CSV file (in za_local/data/ directory)
		update_existing: If True, update existing records. If False, skip duplicates.
	
	Returns:
		dict: Statistics about the import (created, updated, skipped, errors)
	"""
	stats = {
		"created": 0,
		"updated": 0,
		"skipped": 0,
		"errors": 0
	}
	
	# Check if DocType exists
	if not frappe.db.exists("DocType", doctype):
		print(f"  Warning: DocType '{doctype}' does not exist. Skipping.")
		return stats
	
	# Build path to CSV file
	csv_path = Path(frappe.get_app_path("za_local", "data", csv_filename))
	
	if not csv_path.exists():
		print(f"  Warning: CSV file '{csv_filename}' not found at {csv_path}")
		return stats
	
	print(f"Importing {doctype} from {csv_filename}...")
	
	# Read and import CSV data
	with open(csv_path, "r", encoding="utf-8") as csvfile:
		reader = DictReader(csvfile)
		
		for row in reader:
			try:
				# Convert CSV string values to proper types
				converted_row = convert_csv_types(row)
				
				# Check if record already exists
				existing = check_existing_record(doctype, converted_row)
				
				if existing:
					if update_existing:
						# Update existing record
						doc = frappe.get_doc(doctype, existing)
						doc.update(converted_row)
						doc.save(ignore_permissions=True)
						stats["updated"] += 1
					else:
						# Skip duplicate
						stats["skipped"] += 1
						continue
				else:
					# Create new record
					doc = frappe.new_doc(doctype)
					doc.update(converted_row)
					
					with contextlib.suppress(DuplicateEntryError):
						doc.insert(ignore_permissions=True)
						stats["created"] += 1
			
			except Exception as e:
				print(f"  Error importing row {row}: {e}")
				stats["errors"] += 1
	
	# Commit changes
	frappe.db.commit()
	
	# Print summary
	print(f"  ✓ {doctype}: Created {stats['created']}, Updated {stats['updated']}, "
	      f"Skipped {stats['skipped']}, Errors {stats['errors']}")
	
	return stats


def convert_csv_types(row_data):
	"""
	Convert CSV string values to appropriate Python types.
	
	CSV files store everything as strings, but DocTypes need proper types
	(float for Currency, int for Int, etc.)
	
	Args:
		row_data: Dictionary of field values from CSV (all strings)
	
	Returns:
		dict: Converted values with proper types
	"""
	converted = {}
	
	# Fields that should be converted to float (currency fields)
	float_fields = [
		'daily_allowance_rate',
		'incidental_allowance_rate',
		'accommodation_limit',
		'mileage_rate',
		'rate',
		'amount',
		'cost'
	]
	
	# Fields that should be converted to int
	int_fields = [
		'duration_hours',
		'days',
		'months',
		'years'
	]
	
	for key, value in row_data.items():
		# Skip empty values
		if value == '' or value is None:
			converted[key] = None
			continue
		
		# Convert to float if it's a known currency/numeric field
		if key in float_fields:
			try:
				converted[key] = float(value)
			except (ValueError, TypeError):
				converted[key] = 0.0
		# Convert to int if it's a known integer field
		elif key in int_fields:
			try:
				converted[key] = int(value)
			except (ValueError, TypeError):
				converted[key] = 0
		# Keep as string
		else:
			converted[key] = value
	
	return converted


def check_existing_record(doctype, row_data):
	"""
	Check if a record already exists based on primary key or unique fields.
	
	Args:
		doctype: DocType name
		row_data: Dictionary of field values from CSV
	
	Returns:
		str: Name of existing record, or None if not found
	"""
	# Define primary key fields for each doctype
	primary_keys = {
		"Business Trip Region": ["region_name"],
		"Bargaining Council": ["council_name"],
		# Add more as needed
	}
	
	# Get primary key fields for this doctype
	key_fields = primary_keys.get(doctype)
	
	if not key_fields:
		# Default: check by 'name' field if it exists in row_data
		if "name" in row_data and row_data["name"]:
			return row_data["name"] if frappe.db.exists(doctype, row_data["name"]) else None
		return None
	
	# Build filter based on primary key fields
	filters = {}
	for field in key_fields:
		if field in row_data:
			filters[field] = row_data[field]
	
	if not filters:
		return None
	
	# Check if record exists
	existing = frappe.get_all(doctype, filters=filters, limit=1, pluck="name")
	return existing[0] if existing else None


def import_all_master_data():
	"""
	Import all master data CSV files.
	
	This function is called during installation to load predefined
	data for Business Trip Regions, SETAs, Bargaining Councils, etc.
	"""
print("\nImporting master data from CSV files...")

	data_files = [
		("Business Trip Region", "business_trip_region.csv"),
		("SETA", "seta_list.csv"),
		("Bargaining Council", "bargaining_council_list.csv"),
	]
	
	total_stats = {
		"created": 0,
		"updated": 0,
		"skipped": 0,
		"errors": 0
	}
	
	for doctype, filename in data_files:
		stats = import_csv_data(doctype, filename, update_existing=False)
		total_stats["created"] += stats["created"]
		total_stats["updated"] += stats["updated"]
		total_stats["skipped"] += stats["skipped"]
		total_stats["errors"] += stats["errors"]
	
	print(f"\n✓ Master data import complete: "
	      f"{total_stats['created']} created, {total_stats['updated']} updated, "
	      f"{total_stats['skipped']} skipped, {total_stats['errors']} errors\n")
	
	return total_stats

