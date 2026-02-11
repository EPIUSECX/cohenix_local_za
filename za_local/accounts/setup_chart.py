"""
Chart of Accounts Setup for South Africa

This module handles loading the South African Chart of Accounts
for companies during setup and provides integration helpers
for the ERPNext setup wizard.
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
		frappe.log_error(
			"Company is required to load Chart of Accounts",
			"ZA Local Chart of Accounts",
		)
		return False
	if not frappe.db.exists("Company", company):
		frappe.log_error(
			f"Company '{company}' does not exist",
			"ZA Local Chart of Accounts",
		)
		return False
	
	# Get chart file path
	chart_path = Path(frappe.get_app_path("za_local", "accounts", "chart_of_accounts",
										  "za_south_africa_chart_template.json"))
	
	if not chart_path.exists():
		frappe.log_error(
			f"Chart of Accounts file not found: {chart_path}",
			"ZA Local Chart of Accounts",
		)
		return False
	
	try:
		# Company should already have a base chart created by ERPNext's setup wizard.
		# We only *augment* that chart with SA-specific tax accounts.
		existing_accounts = frappe.db.count("Account", {"company": company})
		if existing_accounts == 0:
			# If no accounts exist yet, don't try to build an entire chart here.
			# Let ERPNext's own setup logic handle the base chart, then ZA can be
			# applied later via a separate action.
			frappe.log_error(
				f"No accounts found for company {company} when attempting to load ZA Chart of Accounts. "
				"Skipping ZA chart augmentation.",
				"ZA Local Chart of Accounts",
			)
			return False
		
		# Load chart data from ZA template and add SA-specific tax accounts
		with open(chart_path, "r") as f:
			chart_data = json.load(f)
		
		_add_sa_tax_accounts(company, chart_data.get("tree"))
		return True
		
	except Exception as e:
		frappe.log_error(
			f"Error loading Chart of Accounts for {company}: {str(e)}\n{frappe.get_traceback()}",
			"ZA Local Chart of Accounts",
		)
		# Do not re-raise: allow setup wizard to complete; user can add SA accounts later if needed
		return False


def _get_root_account(company, root_type):
	"""Find the existing root account by root_type (works with any chart naming)."""
	name = frappe.db.get_value(
		"Account",
		{"company": company, "root_type": root_type, "parent_account": ("in", ("", None))},
		"name",
	)
	return frappe.get_doc("Account", name) if name else None


def _get_account_by_name_and_parent(company, account_name, parent_account_name):
	"""Find an account by company, account_name, and parent (by name)."""
	parent = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": parent_account_name},
		"name",
	)
	if not parent:
		return None
	name = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": account_name, "parent_account": parent},
		"name",
	)
	return frappe.get_doc("Account", name) if name else None


def _get_child_account_under(company, parent_doc, preferred_names):
	"""
	Find a direct child account of parent_doc whose account_name is in preferred_names
	or starts with the first preferred name (handles translated/suffixed names).
	"""
	children = frappe.get_all(
		"Account",
		filters={"company": company, "parent_account": parent_doc.name},
		fields=["name", "account_name"],
	)
	if not children:
		return None
	preferred = list(preferred_names)
	for c in children:
		if c.account_name in preferred:
			return frappe.get_doc("Account", c.name)
		if preferred and c.account_name and c.account_name.startswith(preferred[0]):
			return frappe.get_doc("Account", c.name)
	return None


def _get_or_create_tax_group_under(company, parent_account_doc, preferred_names, account_type="Tax"):
	"""Find existing tax group under parent (e.g. Duties and Taxes / Tax Liabilities) or create one."""
	for preferred_name in preferred_names:
		existing = frappe.db.get_value(
			"Account",
			{
				"company": company,
				"account_name": preferred_name,
				"parent_account": parent_account_doc.name,
				"is_group": 1,
			},
			"name",
		)
		if existing:
			return frappe.get_doc("Account", existing)
	# Create first preferred name
	return _get_or_create_account(
		company, preferred_names[0], account_type,
		parent=parent_account_doc.name, is_group=1
	)


def _add_sa_tax_accounts(company, chart_tree):
	"""
	Add only SA-specific tax accounts to an existing chart.
	Works with any standard chart (e.g. Source of Funds (Liabilities) / Application of Funds (Assets)).
	"""
	# Extract tax accounts from our ZA template tree
	tax_accounts = _extract_tax_accounts(chart_tree)

	# Find existing roots by root_type (don't assume "Liabilities" / "Assets" names)
	liabilities_root = _get_root_account(company, "Liability")
	assets_root = _get_root_account(company, "Asset")
	if not liabilities_root or not assets_root:
		raise ValueError(
			f"Could not find Chart of Accounts roots for company {company} "
			f"(Liability root={bool(liabilities_root)}, Asset root={bool(assets_root)})"
		)

	# Find Current Liabilities / Current Assets: try by parent doc first (resilient to naming), then by name+parent
	current_liabilities = _get_child_account_under(
		company, liabilities_root, ["Current Liabilities"]
	)
	if not current_liabilities:
		current_liabilities = _get_account_by_name_and_parent(
			company, "Current Liabilities", liabilities_root.account_name
		)
	current_assets = _get_child_account_under(
		company, assets_root, ["Current Assets"]
	)
	if not current_assets:
		current_assets = _get_account_by_name_and_parent(
			company, "Current Assets", assets_root.account_name
		)
	if not current_liabilities or not current_assets:
		raise ValueError(
			f"Could not find Current Liabilities or Current Assets for company {company}"
		)

	# Use existing Tax Liabilities / Duties and Taxes group or create Tax Liabilities
	tax_liabilities = _get_or_create_tax_group_under(
		company, current_liabilities, ["Tax Liabilities", "Duties and Taxes"]
	)
	tax_assets = _get_or_create_tax_group_under(
		company, current_assets, ["Tax Assets"]
	)

	# Add SA tax ledgers under the groups
	liability_tax_accounts = tax_accounts.get("liabilities", {})
	for account_name, account_info in liability_tax_accounts.items():
		_get_or_create_account(
			company, account_name, "Tax",
			parent=tax_liabilities.name, is_group=0
		)
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
	try:
		chart_path = Path(frappe.get_app_path("za_local", "accounts", "chart_of_accounts",
											  "za_south_africa_chart_template.json"))
		
		if chart_path.exists():
			with open(chart_path, "r") as f:
				chart_data = json.load(f)
				return chart_data.get("name")
	except Exception as e:
		# Log error but don't fail - chart template loading is optional
		frappe.log_error(f"Error getting chart template name: {str(e)}", "ZA Chart Template")
	
	return None


def get_za_chart_tree():
	"""
	Return the full ZA Chart of Accounts tree from the JSON template.

	This is used by the hooks-level monkey patch of ERPNext's
	`get_chart` so that when the ZA template is selected in the
	Company / Setup Wizard flows, ERPNext can create the complete
	South African chart using its standard `create_charts` logic.
	"""
	try:
		chart_path = Path(
			frappe.get_app_path(
				"za_local", "accounts", "chart_of_accounts", "za_south_africa_chart_template.json"
			)
		)

		if not chart_path.exists():
			return None

		with open(chart_path, "r") as f:
			chart_data = json.load(f)

		return chart_data.get("tree")
	except Exception as e:
		# Log error but don't fail - this is a best-effort helper
		frappe.log_error(f"Error getting ZA chart tree: {str(e)}", "ZA Chart Template")
		return None


@frappe.whitelist()
def get_charts_for_country_with_za(country, with_standard: bool = False):
	"""
	Whitelisted wrapper used by ERPNext setup wizard to fetch charts.

	This function is registered via `override_whitelisted_methods` in hooks.py
	as an override for get_charts_for_country. It calls ERPNext's implementation
	then injects the South Africa chart option when country is South Africa.

	Injection is done here (not in the monkey patch) so it works on every
	request; the monkey patch only runs at install/migrate and is not active
	when the setup wizard runs in a fresh process.
	"""
	from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore

	charts = coa_module.get_charts_for_country(country, with_standard)
	if country == "South Africa" and isinstance(charts, list):
		try:
			chart_name = get_chart_template_name()
			if chart_name and chart_name not in charts:
				charts.insert(0, chart_name)
		except Exception:
			pass
	return charts


def extend_charts_for_country():
	"""
	Extend ERPNext's chart discovery to include za_local charts.
	
	This monkey patches ERPNext's get_charts_for_country function to include
	the South African chart template when South Africa is selected as the country.
	"""
	try:
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore
		from functools import wraps

		# Check if function exists and hasn't been wrapped already
		if not hasattr(coa_module, "get_charts_for_country"):
			return

		# Avoid double wrapping
		if getattr(coa_module.get_charts_for_country, "_za_wrapped", False):
			return

		original_get_charts = coa_module.get_charts_for_country

		@wraps(original_get_charts)
		def get_charts_for_country_with_za(country, with_standard: bool = False):
			"""Return core charts plus ZA template for South Africa."""
			try:
				charts = original_get_charts(country, with_standard)
			except Exception:
				# Hard fallback to original behaviour if wrapper misbehaves
				try:
					return original_get_charts(country, with_standard)
				except Exception:
					return []

			# Inject ZA chart name only for South Africa
			if country == "South Africa" and isinstance(charts, list):
				try:
					chart_name = get_chart_template_name()
					if chart_name and chart_name not in charts:
						# Add at the beginning so it's the default suggestion
						charts.insert(0, chart_name)
				except Exception as e:
					try:
						frappe.log_error(f"Could not load ZA chart template name: {e}", "ZA Chart Extension")
					except Exception:
						# Logging failure should not break chart discovery
						pass

			return charts

		# Mark as wrapped to avoid double wrapping
		get_charts_for_country_with_za._za_wrapped = True
		coa_module.get_charts_for_country = get_charts_for_country_with_za
	except Exception:
		# Chart discovery extension is optional, never break hooks loading
		pass


def extend_chart_loader():
	"""
	Extend ERPNext's get_chart so ZA template JSON can be used as a full chart.

	When the selected chart template name matches the ZA chart template, we
	load the JSON from za_local and return its `tree` so that
	`create_charts` imports the entire South African chart as the company's
	Chart of Accounts (full replacement pattern).
	"""
	try:
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore
		from functools import wraps

		if not hasattr(coa_module, "get_chart"):
			return

		# Avoid double wrapping
		if getattr(coa_module.get_chart, "_za_wrapped", False):
			return

		original_get_chart = coa_module.get_chart
		za_template_name = get_chart_template_name()

		@wraps(original_get_chart)
		def get_chart_with_za(chart_template, existing_company=None):
			"""
			If chart_template is ZA template name, return ZA JSON tree;
			otherwise delegate to core get_chart.
			"""
			try:
				if za_template_name and chart_template == za_template_name:
					tree = get_za_chart_tree()
					if tree:
						return tree
			except Exception:
				# Silently ignore and fall through to original_get_chart
				pass

			return original_get_chart(chart_template, existing_company)

		get_chart_with_za._za_wrapped = True
		coa_module.get_chart = get_chart_with_za
	except Exception:
		# Loader extension is optional, never break hooks loading
		pass


def patch_financial_report_templates_sync():
	"""
	Monkey patch sync_financial_report_templates to tolerate unknown COA names.

	When a custom ZA chart template is selected, ERPNext's default implementation
	calls get_chart(chart_of_accounts) and assumes it returns a dict. For
	non-ERPNext charts (e.g. from za_local), this returns None which causes:

	    AttributeError: 'NoneType' object has no attribute 'get'

	This crashes Company creation during setup, so no Company is saved.

	This patch safely handles the "chart not found" case by:
	- Treating it as if disable_default_financial_report_template == False
	- Still syncing default templates for all installed apps
	"""
	try:
		from erpnext.accounts.doctype.financial_report_template import financial_report_template as frt_module  # type: ignore
		from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_module  # type: ignore

		if not hasattr(frt_module, "sync_financial_report_templates"):
			return

		# Avoid double patching
		if getattr(frt_module.sync_financial_report_templates, "_za_patched", False):
			return

		original_sync = frt_module.sync_financial_report_templates

		def safe_sync_financial_report_templates(chart_of_accounts, existing_company=None):
			# For existing companies, keep behaviour unchanged
			if existing_company:
				return original_sync(chart_of_accounts, existing_company)

			disable_default_financial_report_template = False

			if chart_of_accounts:
				try:
					coa = coa_module.get_chart(chart_of_accounts)
				except Exception:
					coa = None

				# Only look for override flag when we have a valid chart dict
				if isinstance(coa, dict):
					disable_default_financial_report_template = coa.get(
						"disable_default_financial_report_template", False
					)

			installed_apps = frappe.get_installed_apps()

			for app in installed_apps:
				# If a regional chart disables ERPNext defaults, honour that
				if disable_default_financial_report_template and app == "erpnext":
					continue

				frt_module._sync_templates_for(app)

		safe_sync_financial_report_templates._za_patched = True
		frt_module.sync_financial_report_templates = safe_sync_financial_report_templates
	except Exception:
		# Never break setup due to patching issues
		try:
			frappe.log_error("Failed to patch sync_financial_report_templates", "ZA Local Setup")
		except Exception:
			pass

