# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patch: Create property setters for SA defaults

Sets default values and customizations:
- ZAR currency defaults for Employee and Company
- Protected file attachments for 40+ DocTypes
- Hide irrelevant fields
"""

import frappe
from frappe.custom.doctype.customize_form.customize_form import (
	docfield_properties,
	doctype_properties,
)
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	"""Create property setters for SA localization"""
	
	from za_local.setup.property_setters import get_property_setters
	
	print("Creating property setters...")
	
	for doctypes, property_setters in get_property_setters().items():
		if isinstance(doctypes, str):
			doctypes = (doctypes,)

		for doctype in doctypes:
			for property_setter in property_setters:
				# Skip if already exists
				existing = frappe.db.exists(
					"Property Setter",
					{
						"doc_type": doctype,
						"field_name": property_setter[0],
						"property": property_setter[1],
					}
				)
				
				if existing:
					continue
				
				if property_setter[0]:
					for_doctype = False
					property_type = docfield_properties[property_setter[1]]
				else:
					for_doctype = True
					property_type = doctype_properties[property_setter[1]]

				make_property_setter(
					doctype=doctype,
					fieldname=property_setter[0],
					property=property_setter[1],
					value=property_setter[2],
					property_type=property_type,
					for_doctype=for_doctype,
				)
	
	frappe.db.commit()
	print("✓ Property setters created successfully")

