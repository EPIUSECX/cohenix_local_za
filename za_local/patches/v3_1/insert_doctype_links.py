# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patch: Insert DocType Links for bidirectional navigation

Creates 22 DocType Link records to enable bidirectional navigation
via the Connections tab in standard ERPNext DocTypes.
"""

import frappe


def execute():
	"""Insert DocType Links for bidirectional connections"""
	
	print("Inserting DocType Links...")
	
	# Get links from hooks
	links = frappe.get_hooks("za_local_custom_records")
	
	if not links:
		print("! No custom records found in hooks")
		return
	
	count = 0
	for custom_record in links:
		# Create filter dict for existence check
		filters = {
			"parent": custom_record.get("parent"),
			"link_doctype": custom_record.get("link_doctype"),
			"link_fieldname": custom_record.get("link_fieldname"),
		}
		
		if not frappe.db.exists("DocType Link", filters):
			try:
				doc = frappe.get_doc(custom_record)
				doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
				count += 1
			except Exception as e:
				print(f"! Warning: Could not create link for {custom_record.get('parent')}: {e}")
	
	frappe.db.commit()
	print(f"✓ Inserted {count} DocType Links for bidirectional navigation")

