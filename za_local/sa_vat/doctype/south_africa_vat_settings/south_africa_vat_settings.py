# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SouthAfricaVATSettings(Document):
    def validate(self):
        self.validate_vat_rates()
        self.validate_vat_accounts()
        self.validate_vat_registration_number()
        
    def validate_vat_rates(self):
        """Validate VAT rates"""
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
                
    def validate_vat_registration_number(self):
        """Validate VAT registration number format"""
        if self.vat_registration_number:
            # South African VAT numbers are 10 digits, usually starting with 4
            import re
            if not re.match(r'^[0-9]{10}$', self.vat_registration_number):
                frappe.throw("VAT Registration Number must be 10 digits")
                
            if not self.vat_registration_number.startswith('4'):
                frappe.msgprint("South African VAT Registration Numbers typically start with '4'", indicator='yellow')
                
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
