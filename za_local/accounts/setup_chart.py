"""
Chart of Accounts Setup for South Africa

This module handles loading the South African Chart of Accounts
for companies during setup.
"""

import frappe
from frappe import _
from pathlib import Path
import json


def load_sa_chart_of_accounts(company):
	"""
	Load South African Chart of Accounts for a company.
	
	If company has no accounts, loads the full SA chart.
	If company already has accounts, adds only the SA-specific tax accounts.
	
	Args:
		company: Company name for which to load the chart
	"""
	if not company:
		frappe.throw(_("Company is required to load Chart of Accounts"))
	
	# Check if company exists
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company '{0}' does not exist").format(company))
	
	# Check if company already has accounts
	existing_accounts = frappe.db.count("Account", {"company": company})
	
	# Get chart file path
	chart_path = Path(frappe.get_app_path("za_local", "accounts", "chart_of_accounts",
										  "za_south_africa_chart_template.json"))
	
	if not chart_path.exists():
		frappe.throw(_("Chart of Accounts file not found: {0}").format(chart_path))
	
	# Load chart data
	with open(chart_path, "r") as f:
		chart_data = json.load(f)
	
	try:
		if existing_accounts == 0:
			# No accounts exist - load full SA chart
			from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
			
			create_charts(company, chart_template=chart_data["name"], custom_chart=chart_data.get("tree"))
			
			frappe.msgprint(
				_("South African Chart of Accounts loaded successfully for {0}").format(company),
				title=_("Chart of Accounts Loaded"),
				indicator="green"
			)
			return True
		else:
			# Accounts exist - add only SA-specific tax accounts
			_add_sa_tax_accounts(company, chart_data.get("tree"))
			
			frappe.msgprint(
				_("South African tax accounts added to existing Chart of Accounts for {0}").format(company),
				title=_("Tax Accounts Added"),
				indicator="green"
			)
			return True
		
	except Exception as e:
		frappe.log_error(
			f"Error loading Chart of Accounts for {company}: {str(e)}",
			"ZA Local Chart of Accounts"
		)
		frappe.throw(
			_("Failed to load Chart of Accounts: {0}").format(str(e)),
			title=_("Chart Loading Failed")
		)


def _add_sa_tax_accounts(company, chart_tree):
	"""
	Add only SA-specific tax accounts to an existing chart.
	
	Args:
		company: Company name
		chart_tree: Chart of Accounts tree structure from JSON
	"""
	# Extract tax accounts from the chart tree
	tax_accounts = _extract_tax_accounts(chart_tree)
	
	# Get or create parent accounts
	liabilities_root = _get_or_create_account(
		company, "Liabilities", "Liability", is_group=1, root_type="Liability"
	)
	current_liabilities = _get_or_create_account(
		company, "Current Liabilities", "Liability", 
		parent=liabilities_root.name, is_group=1
	)
	
	assets_root = _get_or_create_account(
		company, "Assets", "Asset", is_group=1, root_type="Asset"
	)
	current_assets = _get_or_create_account(
		company, "Current Assets", "Asset",
		parent=assets_root.name, is_group=1
	)
	
	# Create Tax Liabilities group if it doesn't exist (SA-specific naming)
	# Check if it exists with either name (for compatibility with standard charts)
	tax_liabilities_name = "Tax Liabilities"  # Use SA-specific naming per SA laws/legislation
	existing_tax_group = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": ["in", ["Tax Liabilities", "Duties and Taxes"]], "is_group": 1},
		"name"
	)
	if existing_tax_group:
		tax_liabilities = frappe.get_doc("Account", existing_tax_group)
		# If it's named "Duties and Taxes", we'll use it but prefer "Tax Liabilities" for new companies
	else:
		tax_liabilities = _get_or_create_account(
			company, tax_liabilities_name, "Tax",
			parent=current_liabilities.name, is_group=1
		)
	
	# Create Tax Assets group if it doesn't exist
	tax_assets = _get_or_create_account(
		company, "Tax Assets", "Tax",
		parent=current_assets.name, is_group=1
	)
	
	# Add tax accounts from liabilities
	liability_tax_accounts = tax_accounts.get("liabilities", {})
	for account_name, account_info in liability_tax_accounts.items():
		_get_or_create_account(
			company, account_name, "Tax",
			parent=tax_liabilities.name, is_group=0
		)
	
	# Add tax accounts from assets
	asset_tax_accounts = tax_accounts.get("assets", {})
	for account_name, account_info in asset_tax_accounts.items():
		_get_or_create_account(
			company, account_name, "Tax",
			parent=tax_assets.name, is_group=0
		)


def _extract_tax_accounts(chart_tree):
	"""
	Extract SA-specific tax accounts from chart tree.
	
	Returns:
		dict: {"liabilities": {...}, "assets": {...}}
	"""
	tax_accounts = {"liabilities": {}, "assets": {}}
	
	# Extract from Liabilities > Current Liabilities > Tax Liabilities
	if "Liabilities" in chart_tree:
		liabilities = chart_tree["Liabilities"]
		if "Current Liabilities" in liabilities:
			current_liabilities = liabilities["Current Liabilities"]
			# Check for "Tax Liabilities" (SA-specific naming) or "Duties and Taxes" (standard naming)
			# We prefer SA-specific "Tax Liabilities" but support both for compatibility
			tax_liabilities_group = current_liabilities.get("Tax Liabilities") or current_liabilities.get("Duties and Taxes")
			if tax_liabilities_group:
				tax_liabilities = tax_liabilities_group
				for account_name, account_info in tax_liabilities.items():
					# Skip metadata fields
					if account_name not in ["account_type", "is_group", "root_type"]:
						# Empty dict {} means it's a ledger account (not a group)
						# Dict with only metadata means it's a group
						if isinstance(account_info, dict):
							if not account_info or (account_info.get("account_type") == "Tax" and not account_info.get("is_group")):
								tax_accounts["liabilities"][account_name] = account_info or {}
	
	# Extract from Assets > Current Assets > Tax Assets
	if "Assets" in chart_tree:
		assets = chart_tree["Assets"]
		if "Current Assets" in assets:
			current_assets = assets["Current Assets"]
			if "Tax Assets" in current_assets:
				tax_assets = current_assets["Tax Assets"]
				for account_name, account_info in tax_assets.items():
					# Skip metadata fields
					if account_name not in ["account_type", "is_group", "root_type"]:
						# Empty dict {} means it's a ledger account (not a group)
						if isinstance(account_info, dict):
							if not account_info or (account_info.get("account_type") == "Tax" and not account_info.get("is_group")):
								tax_accounts["assets"][account_name] = account_info or {}
	
	return tax_accounts


def _get_or_create_account(company, account_name, account_type, parent=None, is_group=0, root_type=None):
	"""
	Get existing account or create it if it doesn't exist.
	
	Args:
		company: Company name
		account_name: Account name
		account_type: Account type
		parent: Parent account name
		is_group: Whether account is a group
		root_type: Root type (for root accounts only)
	
	Returns:
		Account document
	"""
	# Try to find existing account
	existing = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": account_name},
		"name"
	)
	
	if existing:
		return frappe.get_doc("Account", existing)
	
	# Create new account
	account_doc = frappe.get_doc({
		"doctype": "Account",
		"company": company,
		"account_name": account_name,
		"account_type": account_type,
		"parent_account": parent or "",
		"is_group": is_group,
		"root_type": root_type,
	})
	
	if root_type:
		account_doc.flags.ignore_mandatory = True
	
	account_doc.flags.ignore_permissions = True
	account_doc.insert()
	
	return account_doc


def get_chart_template_name():
	"""Get the name of the South African Chart of Accounts template"""
	chart_path = Path(frappe.get_app_path("za_local", "accounts", "chart_of_accounts",
										  "za_south_africa_chart_template.json"))
	
	if chart_path.exists():
		with open(chart_path, "r") as f:
			chart_data = json.load(f)
			return chart_data.get("name")
	
	return None

