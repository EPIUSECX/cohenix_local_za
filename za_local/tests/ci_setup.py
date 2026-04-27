import frappe


def prepare_site_for_tests():
	"""Seed ERPNext masters that older test runners expect on fresh CI sites."""
	ensure_transit_warehouse_type()


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
	frappe.db.commit()
