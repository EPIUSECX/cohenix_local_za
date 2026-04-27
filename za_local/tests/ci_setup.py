import frappe


def prepare_site_for_tests():
	"""Seed ERPNext masters that older test runners expect on fresh CI sites."""
	ensure_genders()
	ensure_transit_warehouse_type()
	frappe.db.commit()


def ensure_genders():
	if not frappe.db.table_exists("Gender"):
		return

	for gender in ("Male", "Female", "Other"):
		if frappe.db.exists("Gender", gender):
			continue

		doc = frappe.new_doc("Gender")
		doc.gender = gender
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)


def ensure_transit_warehouse_type():
	if not frappe.db.table_exists("Warehouse Type"):
		return
	if frappe.db.exists("Warehouse Type", "Transit"):
		return

	doc = frappe.new_doc("Warehouse Type")
	doc.name = "Transit"
	doc.description = "Goods in transit"
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
