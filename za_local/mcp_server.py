from typing import Any, Dict, List, Optional

import frappe
from frappe_mcp.server.server import MCP


# Expose an MCP server for development.
# Name it "frappe-workspace" so MCP clients can list it as installed.
mcp = MCP(name="frappe-workspace")


@mcp.register(allow_guest=False, xss_safe=True)
def mcp_endpoint():
	# Tools are defined in this module, so importing is not required.
	return


@mcp.tool(description="List DocType names in the system")
def list_doctypes() -> List[str]:
	"""Return all DocType names."""
	return frappe.get_all('DocType', pluck='name')


@mcp.tool(description="Get DocType metadata (fields, permissions, options)")
def get_doctype_schema(doctype: str) -> Dict[str, Any]:
	"""Return metadata for a DocType as a dictionary.

	- doctype: DocType name
	"""
	meta = frappe.get_meta(doctype)
	md = meta.as_dict()
	# Trim extremely large keys if present
	md.pop('fields', None)  # will add simplified fields below
	fields = []
	for f in meta.fields:
		fields.append({
			"fieldname": f.fieldname,
			"label": f.label,
			"fieldtype": f.fieldtype,
			"reqd": bool(getattr(f, 'reqd', 0)),
			"options": getattr(f, 'options', None),
			"in_list_view": bool(getattr(f, 'in_list_view', 0)),
		})
	md["fields"] = fields
	return md


@mcp.tool(description="Query documents with filters and fields")
def query_docs(
	doctype: str,
	filters: Optional[Dict[str, Any]] = None,
	fields: Optional[List[str]] = None,
	limit: int = 20,
	offset: int = 0,
	order_by: Optional[str] = None,
) -> List[Dict[str, Any]]:
	"""Return a list of documents.

	- doctype: DocType name
	- filters: key/value filters (e.g., {"status": "Open"})
	- fields: list of fields to fetch (defaults to name and modified)
	- limit: max rows
	- offset: starting offset
	- order_by: SQL order by clause (e.g., "modified desc")
	"""
	if not fields:
		fields = ["name", "modified"]
	kwargs: Dict[str, Any] = {
		"doctype": doctype,
		"filters": filters or {},
		"fields": fields,
		"limit_start": offset,
		"limit_page_length": limit,
	}
	if order_by:
		kwargs["order_by"] = order_by
	return frappe.get_all(**kwargs)


@mcp.tool(description="Fetch a single document by name")
def get_doc(doctype: str, name: str) -> Dict[str, Any]:
	"""Return a single document as a dictionary.

	- doctype: DocType name
	- name: document name (ID)
	"""
	doc = frappe.get_doc(doctype, name)
	return doc.as_dict()


@mcp.tool(description="Create a new document")
def create_doc(doctype: str, data: Dict[str, Any]) -> Dict[str, Any]:
	"""Create and insert a document.

	- doctype: DocType name
	- data: fields for the new document
	"""
	doc = frappe.get_doc({"doctype": doctype, **(data or {})})
	doc.insert()
	frappe.db.commit()
	return doc.as_dict()


@mcp.tool(description="Update an existing document by name")
def update_doc(doctype: str, name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
	"""Update fields of an existing document and save.

	- doctype: DocType name
	- name: document name (ID)
	- updates: fields to set
	"""
	doc = frappe.get_doc(doctype, name)
	for k, v in (updates or {}).items():
		setattr(doc, k, v)
	doc.save()
	frappe.db.commit()
	return doc.as_dict()


