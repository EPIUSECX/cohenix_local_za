# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SouthAfricaVATSettings(Document):
    def validate(self):
        self.ensure_company_default()
        self.validate_vat_rates()
        self.validate_vat_accounts()
        self.validate_company_vat_number()

    def ensure_company_default(self):
        """Ensure company is set, and propagate to default_vat_report_company when appropriate."""
        if not self.company:
            # Default to the first company (alphabetical order) if none selected
            companies = frappe.get_all("Company", pluck="name", order_by="name asc", limit=1)
            if companies:
                self.company = companies[0]

        # If no explicit default_vat_report_company, fall back to selected company
        if self.company and not self.default_vat_report_company:
            self.default_vat_report_company = self.company
        
    def validate_vat_rates(self):
        """Validate VAT rates"""
        # If no rates captured yet, pre-populate sensible defaults so the user
        # sees a ready-to-use configuration on first save.
        if not self.vat_rates:
            # Standard rate from the main field
            self.append("vat_rates", {
                "rate_name": "Standard Rate",
                "rate": self.standard_vat_rate,
                "is_standard_rate": 1,
                "description": "Standard VAT rate for South Africa"
            })

            # Optional zero-rated row
            if self.enable_zero_rated_items:
                self.append("vat_rates", {
                    "rate_name": "Zero Rate",
                    "rate": 0,
                    "is_zero_rated": 1,
                    "is_exempt": 0,
                    "description": "Zero-rated items (0% VAT)"
                })

            # Optional exempt row
            if self.enable_exempt_items:
                self.append("vat_rates", {
                    "rate_name": "Exempt",
                    "rate": 0,
                    "is_zero_rated": 0,
                    "is_exempt": 1,
                    "description": "VAT exempt items"
                })

        # Check if standard rate is present
        standard_rate_exists = False
        for rate in self.vat_rates:
            if rate.is_standard_rate:
                standard_rate_exists = True
                # Ensure standard rate matches the main setting
                if rate.rate != self.standard_vat_rate:
                    rate.rate = self.standard_vat_rate
                    
        if not standard_rate_exists and self.vat_rates:
            # Add standard rate if not present
            self.append("vat_rates", {
                "rate_name": "Standard Rate",
                "rate": self.standard_vat_rate,
                "is_standard_rate": 1,
                "description": "Standard VAT rate for South Africa"
            })
            
        # Check for zero rate if enabled
        if self.enable_zero_rated_items:
            zero_rate_exists = False
            for rate in self.vat_rates:
                if rate.rate == 0 and rate.is_zero_rated:
                    zero_rate_exists = True
                    
            if not zero_rate_exists:
                # Add zero rate if not present
                self.append("vat_rates", {
                    "rate_name": "Zero Rate",
                    "rate": 0,
                    "is_zero_rated": 1,
                    "is_exempt": 0,
                    "description": "Zero-rated items (0% VAT)"
                })
                
        # Check for exempt rate if enabled
        if self.enable_exempt_items:
            exempt_rate_exists = False
            for rate in self.vat_rates:
                if rate.is_exempt:
                    exempt_rate_exists = True
                    
            if not exempt_rate_exists:
                # Add exempt rate if not present
                self.append("vat_rates", {
                    "rate_name": "Exempt",
                    "rate": 0,
                    "is_zero_rated": 0,
                    "is_exempt": 1,
                    "description": "VAT exempt items"
                })
                
    def validate_vat_accounts(self):
        """Validate VAT accounts"""
        if self.input_vat_account == self.output_vat_account:
            frappe.throw("Input VAT Account and Output VAT Account cannot be the same")
            
        # Check if accounts exist
        for account_field in ["input_vat_account", "output_vat_account"]:
            account = getattr(self, account_field)
            if account and not frappe.db.exists("Account", account):
                frappe.throw(f"Account {account} does not exist")

    def validate_company_vat_number(self):
        """Validate VAT number on the default company (display-only here)."""
        # Prefer the explicitly selected company for validation; fall back to default_vat_report_company
        company = self.company or self.default_vat_report_company
        if not company:
            return

        vat_number = frappe.db.get_value("Company", company, "za_vat_number")
        if not vat_number:
            frappe.msgprint(
                "VAT Registration Number is not set on the selected Default VAT Report Company. "
                "Set it on the Company record to ensure VAT201 returns are correct.",
                indicator="yellow",
            )
            return

        # South African VAT numbers are 10 digits, usually starting with 4
        import re
        if not re.match(r"^[0-9]{10}$", vat_number):
            frappe.throw("Company VAT Registration Number must be 10 digits")

        if not vat_number.startswith("4"):
            frappe.msgprint(
                "South African VAT Registration Numbers typically start with '4'",
                indicator="yellow",
            )
                
    def on_update(self):
        """Update VAT settings in Accounts Settings"""
        # Update standard VAT rate in Accounts Settings
        accounts_settings = frappe.get_doc("Accounts Settings")
        if hasattr(accounts_settings, "standard_tax_rate") and accounts_settings.standard_tax_rate != self.standard_vat_rate:
            accounts_settings.standard_tax_rate = self.standard_vat_rate
            accounts_settings.save()
            
        # Create or update tax templates based on VAT rates
        self.update_tax_templates()
        
    def update_tax_templates(self):
        """Create or update tax templates based on VAT rates"""
        # Only proceed if default_vat_report_company is set
        if not self.default_vat_report_company:
            frappe.msgprint(
                "Default VAT Report Company is not set. Skipping tax template creation. "
                "Please set this value in South African VAT Settings after company setup.",
                indicator='yellow'
            )
            return

        # Create sales tax template
        self.create_or_update_tax_template("Sales", self.output_vat_account)

        # Create purchase tax template
        self.create_or_update_tax_template("Purchase", self.input_vat_account)
        
        # Create/update item tax templates for each VAT rate
        self.update_item_tax_templates()
        
    def create_or_update_tax_template(self, template_type, account):
        """Create or update tax template for sales or purchase"""
        template_name = f"South Africa VAT {self.standard_vat_rate}% - {template_type}"
        doctype_name = f"{template_type} Taxes and Charges Template"

        # No need to check for default_vat_report_company here; handled in update_tax_templates

        if frappe.db.exists(doctype_name, template_name):
            tax_template = frappe.get_doc(doctype_name, template_name)
            # If existing template is missing a company, set it
            if not tax_template.company:
                tax_template.company = self.default_vat_report_company
        else:
            tax_template = frappe.new_doc(doctype_name)
            tax_template.title = template_name
            tax_template.name = template_name # Kartoza sets name explicitly
            tax_template.company = self.default_vat_report_company
            tax_template.is_default = 1
            
        # Clear existing taxes
        tax_template.taxes = []
        
        # Add taxes based on VAT rates
        for rate in self.vat_rates:
            if not rate.is_exempt:  # Skip exempt rates
                tax_template.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": account,
                    "description": rate.rate_name,
                    "rate": rate.rate
                })
                
        tax_template.save()
        
        return tax_template.name

    def update_item_tax_templates(self):
        """Create or update Item Tax Templates for each VAT rate.

        This ensures that users can set VAT at item level (standard, zero-rated, exempt)
        in line with Frappe localisation guidelines.
        """
        if not self.default_vat_report_company:
            # Company check is already enforced in update_tax_templates, but keep
            # this guard for defensive programming in case this method is reused.
            return

        for rate in self.vat_rates:
            # Build a stable, descriptive title per rate
            # Example: "South Africa VAT Standard Rate (15%)" or "South Africa VAT Zero Rate (0%)"
            label_parts = ["South Africa VAT", rate.rate_name]
            if rate.rate is not None:
                label_parts.append(f"({frappe.utils.fmt_float(rate.rate, 2)}%)")
            template_title = " ".join(label_parts)

            # Fetch or create the Item Tax Template for this rate/company
            existing_name = frappe.db.get_value(
                "Item Tax Template",
                {"title": template_title, "company": self.default_vat_report_company},
                "name",
            )

            if existing_name:
                item_tax_template = frappe.get_doc("Item Tax Template", existing_name)
            else:
                item_tax_template = frappe.new_doc("Item Tax Template")
                item_tax_template.title = template_title
                item_tax_template.company = self.default_vat_report_company

            # Reset taxes to keep the configuration in sync with VAT Settings
            item_tax_template.taxes = []

            if rate.is_exempt:
                # Exempt items: keep template with no tax rows so they remain untaxed
                pass
            else:
                # Standard and zero-rated items: one row pointing to the output VAT account
                if not self.output_vat_account:
                    frappe.msgprint(
                        "Output VAT Account is not set in South Africa VAT Settings. "
                        f"Skipping Item Tax Template configuration for {template_title}.",
                        indicator="yellow",
                    )
                    continue

                item_tax_template.append(
                    "taxes",
                    {
                        "tax_type": self.output_vat_account,
                        "tax_rate": rate.rate,
                    },
                )

            item_tax_template.save()
