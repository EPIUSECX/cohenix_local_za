# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patch: Import CSV master data

Imports predefined master data:
- Business Trip Regions (16 SA cities + international)
- SETA list (24 sectors)
- Bargaining Councils (11 councils)
"""

import frappe


def execute():
	"""Import master data from CSV files"""
	
	print("Importing master data...")
	
	try:
		from za_local.utils.csv_importer import import_all_master_data
		import_all_master_data()
		frappe.db.commit()
		print("✓ Master data imported successfully")
	except Exception as e:
		print(f"! Warning: Could not import master data: {e}")
		print("  Master data can be imported manually later.")

