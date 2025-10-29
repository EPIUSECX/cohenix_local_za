# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Purchase Document Deletion Protection

Implements SARS audit trail requirements by preventing deletion of
non-consecutive purchase documents (Purchase Order, Purchase Receipt, Purchase Invoice).

Per SARS regulations, businesses must maintain consecutive numbering of
purchase documents for tax audit purposes. This module only allows deletion
of the most recent document in a naming series to preserve the audit trail.
"""

import frappe
from frappe import _


def on_trash(doc, method=None):
	"""
	Validate that only the most recent purchase document can be deleted.
	
	This ensures consecutive numbering is maintained for SARS audit compliance.
	Only the latest document (by naming series) can be deleted.
	
	Args:
		doc: The document being deleted
		method: Event method (not used)
	
	Raises:
		frappe.ValidationError: If document is not the most recent in series
	"""
	if not is_latest_in_series(doc):
		frappe.throw(
			_(
				"For SARS audit trail compliance, only the most recent {0} can be deleted. "
				"<br><br>"
				"This document <b>{1}</b> is not the latest in its naming series. "
				"<br>"
				"Latest document: <b>{2}</b>"
				"<br><br>"
				"To maintain consecutive numbering required by SARS, please delete documents "
				"in reverse chronological order (newest first)."
			).format(
				doc.doctype,
				doc.name,
				get_latest_document_name(doc.doctype, doc.naming_series)
			),
			title=_("Cannot Delete Document - SARS Compliance"),
		)


def is_latest_in_series(doc):
	"""
	Check if this document is the latest in its naming series.
	
	Args:
		doc: Document to check
	
	Returns:
		bool: True if this is the latest document, False otherwise
	"""
	# Get naming series field based on doctype
	naming_series_field = get_naming_series_field(doc.doctype)
	if not naming_series_field:
		# No naming series, allow deletion
		return True
	
	naming_series = doc.get(naming_series_field)
	if not naming_series:
		# No naming series set, allow deletion
		return True
	
	# Get the latest document name in this series
	latest_name = get_latest_document_name(doc.doctype, naming_series)
	
	# Allow deletion if this is the latest document
	return doc.name == latest_name


def get_naming_series_field(doctype):
	"""
	Get the naming series field name for a doctype.
	
	Args:
		doctype: DocType name
	
	Returns:
		str: Field name for naming series, or None if not found
	"""
	naming_series_fields = {
		"Request for Quotation": "naming_series",
		"Supplier Quotation": "naming_series",
		"Purchase Order": "naming_series",
		"Purchase Receipt": "naming_series",
		"Purchase Invoice": "naming_series",
	}
	return naming_series_fields.get(doctype)


def get_latest_document_name(doctype, naming_series):
	"""
	Get the name of the latest document in a naming series.
	
	Args:
		doctype: DocType name
		naming_series: Naming series prefix
	
	Returns:
		str: Name of latest document, or None if not found
	"""
	naming_series_field = get_naming_series_field(doctype)
	
	if not naming_series_field:
		return None
	
	# Query for latest document in this series
	latest = frappe.get_all(
		doctype,
		filters={naming_series_field: naming_series},
		fields=["name"],
		order_by="creation desc",
		limit=1
	)
	
	return latest[0].name if latest else None

