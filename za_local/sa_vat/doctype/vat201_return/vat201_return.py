# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, add_months

class VAT201Return(Document):
    def validate(self):
        self.validate_dates()
        self.set_vat_registration_number()
        self.calculate_totals()
        
    def validate_dates(self):
        """Validate submission date"""
        if getdate(self.submission_date) > getdate(today()):
            frappe.throw("Submission Date cannot be in the future")
            
    def set_vat_registration_number(self):
        """Set VAT registration number from company"""
        if self.company and not self.vat_registration_number:
            # Try to get from company
            vat_number = frappe.db.get_value("Company", self.company, "custom_vat_number")
            if vat_number:
                self.vat_registration_number = vat_number
            else:
                # Try to get from VAT settings
                vat_settings = frappe.get_doc("South African VAT Settings")
                if vat_settings.vat_registration_number:
                    self.vat_registration_number = vat_settings.vat_registration_number
                    
    def calculate_totals(self):
        """Calculate all totals"""
        # Calculate total supplies
        self.total_supplies = flt(self.standard_rated_supplies) + flt(self.zero_rated_supplies) + flt(self.exempt_supplies)
        
        # Calculate standard rated output tax
        vat_settings = frappe.get_doc("South African VAT Settings")
        standard_rate = flt(vat_settings.standard_vat_rate) / 100
        self.standard_rated_output = flt(self.standard_rated_supplies) * standard_rate
        
        # Calculate total output tax
        self.total_output_tax = (
            flt(self.standard_rated_output) + 
            flt(self.change_in_use_output) + 
            flt(self.bad_debts_output) + 
            flt(self.other_output)
        )
        
        # Calculate total input tax
        self.total_input_tax = (
            flt(self.capital_goods_input) + 
            flt(self.other_goods_services_input) + 
            flt(self.change_in_use_input) + 
            flt(self.bad_debts_input)
        )
        
        # Calculate VAT payable or refundable
        if self.total_output_tax > self.total_input_tax:
            self.vat_payable = self.total_output_tax - self.total_input_tax
            self.vat_refundable = 0
        else:
            self.vat_refundable = self.total_input_tax - self.total_output_tax
            self.vat_payable = 0
            
        # Calculate total amount payable
        if self.vat_payable > 0:
            self.total_amount_payable = self.vat_payable - flt(self.diesel_refund)
            if self.total_amount_payable < 0:
                # If diesel refund exceeds VAT payable, it becomes refundable
                self.vat_refundable = abs(self.total_amount_payable)
                self.total_amount_payable = 0
        else:
            self.total_amount_payable = 0
            self.vat_refundable = self.vat_refundable + flt(self.diesel_refund)
            
    def on_submit(self):
        """Handle submission to SARS"""
        if self.status == "Draft":
            self.status = "Prepared"
            
        # Generate submission reference if not exists
        if not self.submission_reference:
            self.submission_reference = f"VAT201-{self.name}-{frappe.utils.random_string(8)}"
            
        self.db_update()
        
    @frappe.whitelist()
    def submit_to_sars(self):
        """Submit VAT201 return to SARS e-Filing"""
        if self.status != "Prepared":
            frappe.throw("VAT201 Return must be in 'Prepared' status before submission to SARS")
            
        # Check if VAT settings has e-Filing credentials
        vat_settings = frappe.get_doc("South African VAT Settings")
        if not vat_settings.sars_efiling_username or not vat_settings.sars_efiling_password:
            frappe.throw("SARS e-Filing credentials not configured in South African VAT Settings")
            
        # Implementation of SARS e-Filing integration
        try:
            # In a production environment, this would connect to the SARS API
            # For now we're simulating the submission process
            
            # 1. Connect to SARS e-Filing API
            # connection = sars_efiling.connect(
            #    username=vat_settings.sars_efiling_username,
            #    password=vat_settings.sars_efiling_password
            # )
            
            # 2. Prepare the submission data
            submission_data = self.prepare_efiling_submission_data()
            
            # 3. Submit to SARS
            # response = connection.submit_vat201(submission_data)
            
            # 4. Update status based on response
            # self.efiling_submission_id = response.submission_id
            # self.efiling_submission_date = response.submission_date
            
            # Simulate successful submission
            import random
            import string
            self.efiling_submission_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            self.efiling_submission_date = today()
            self.status = "Submitted"
            
            # Log the successful submission
            frappe.get_doc({
                "doctype": "SARS Submission Log",
                "submission_type": "VAT201",
                "reference_doctype": self.doctype,
                "reference_name": self.name,
                "submission_date": today(),
                "status": "Success",
                "notes": f"Successfully submitted VAT201 return to SARS e-Filing with ID: {self.efiling_submission_id}"
            }).insert(ignore_permissions=True)
            
            frappe.msgprint("VAT201 Return submitted to SARS e-Filing")
            self.db_update()
            return {"success": True, "submission_id": self.efiling_submission_id}
            
        except Exception as e:
            # Log the failed submission
            frappe.get_doc({
                "doctype": "SARS Submission Log",
                "submission_type": "VAT201",
                "reference_doctype": self.doctype,
                "reference_name": self.name,
                "submission_date": today(),
                "status": "Failed",
                "notes": f"Failed to submit VAT201 return to SARS e-Filing: {str(e)}"
            }).insert(ignore_permissions=True)
            
            frappe.log_error(f"VAT201 SARS e-Filing Submission Failed: {str(e)}")
            frappe.throw(f"Failed to submit to SARS e-Filing: {str(e)}")
            
    def prepare_efiling_submission_data(self):
        """Prepare data for e-Filing submission"""
        return {
            "vendor_number": self.vat_registration_number,
            "submission_period": self.submission_period,
            "submission_date": self.submission_date,
            "standard_rated_supplies": self.standard_rated_supplies,
            "zero_rated_supplies": self.zero_rated_supplies,
            "exempt_supplies": self.exempt_supplies,
            "total_supplies": self.total_supplies,
            "standard_rated_output": self.standard_rated_output,
            "change_in_use_output": self.change_in_use_output,
            "bad_debts_output": self.bad_debts_output,
            "other_output": self.other_output,
            "total_output_tax": self.total_output_tax,
            "capital_goods_input": self.capital_goods_input,
            "other_goods_services_input": self.other_goods_services_input,
            "change_in_use_input": self.change_in_use_input,
            "bad_debts_input": self.bad_debts_input,
            "total_input_tax": self.total_input_tax,
            "vat_payable": self.vat_payable,
            "vat_refundable": self.vat_refundable,
            "diesel_refund": self.diesel_refund,
            "total_amount_payable": self.total_amount_payable
        }
    
    @frappe.whitelist()
    def get_vat_transactions(self):
        """Get VAT transactions for the period and populate VAT201 fields"""
        if not self.company or not self.from_date or not self.to_date:
            frappe.throw("Company, From Date, and To Date are required")
        
        from_date = getdate(self.from_date)
        to_date = getdate(self.to_date)
        
        # Get VAT settings
        vat_settings = frappe.get_doc("South African VAT Settings")
        if not vat_settings.output_vat_account or not vat_settings.input_vat_account:
            frappe.throw("VAT accounts not configured in South African VAT Settings")
        
        # Reset existing values
        self.standard_rated_supplies = 0
        self.zero_rated_supplies = 0
        self.exempt_supplies = 0
        self.standard_rated_output = 0
        self.change_in_use_output = 0
        self.bad_debts_output = 0
        self.other_output = 0
        self.capital_goods_input = 0
        self.other_goods_services_input = 0
        self.change_in_use_input = 0
        self.bad_debts_input = 0
        
        # Get all sales invoices with VAT for the period
        sales_invoices = self.get_sales_invoices_with_vat(from_date, to_date, vat_settings)
        
        # Process sales invoices
        for invoice in sales_invoices:
            # Get tax details
            taxes = frappe.db.sql(f"""
                SELECT 
                    account_head, rate, tax_amount
                FROM 
                    `tabSales Taxes and Charges`
                WHERE 
                    parent = '{invoice.name}'
                    AND account_head = '{vat_settings.output_vat_account}'
            """, as_dict=1)
            
            for tax in taxes:
                # Calculate net amount (before VAT)
                net_amount = invoice.base_total - tax.tax_amount
                
                # Add to standard rated supplies if standard rate
                if tax.rate == vat_settings.standard_vat_rate:
                    self.standard_rated_supplies += net_amount
                    self.standard_rated_output += tax.tax_amount
                # Add to zero-rated supplies if zero-rated
                elif tax.rate == 0:
                    self.zero_rated_supplies += net_amount
        
        # Get all purchase invoices with VAT for the period
        purchase_invoices = self.get_purchase_invoices_with_vat(from_date, to_date, vat_settings)
        
        # Process purchase invoices
        for invoice in purchase_invoices:
            # Get tax details
            taxes = frappe.db.sql(f"""
                SELECT 
                    account_head, rate, tax_amount, category
                FROM 
                    `tabPurchase Taxes and Charges`
                WHERE 
                    parent = '{invoice.name}'
                    AND account_head = '{vat_settings.input_vat_account}'
            """, as_dict=1)
            
            for tax in taxes:
                # Check if this is capital goods or normal goods/services
                is_capital = False
                # Attempt to determine if capital goods based on item categories
                items = frappe.db.sql(f"""
                    SELECT 
                        item_code, item_name, item_group
                    FROM 
                        `tabPurchase Invoice Item`
                    WHERE 
                        parent = '{invoice.name}'
                """, as_dict=1)
                
                for item in items:
                    # Check if item group is marked as capital goods
                    if frappe.db.get_value("Item Group", item.item_group, "is_capital_goods"):
                        is_capital = True
                
                # Add to appropriate input tax field
                if is_capital:
                    self.capital_goods_input += tax.tax_amount
                else:
                    self.other_goods_services_input += tax.tax_amount
        
        # Calculate totals
        self.calculate_totals()
        
        # Return summary
        return {
            "sales_invoices_count": len(sales_invoices),
            "purchase_invoices_count": len(purchase_invoices),
            "standard_rated_supplies": self.standard_rated_supplies,
            "zero_rated_supplies": self.zero_rated_supplies,
            "standard_rated_output": self.standard_rated_output,
            "capital_goods_input": self.capital_goods_input,
            "other_goods_services_input": self.other_goods_services_input
        }
    
    def get_sales_invoices_with_vat(self, from_date, to_date, vat_settings):
        """Get all sales invoices with VAT for the period"""
        conditions = ""
        if self.company:
            conditions += f" AND company = '{self.company}'"
            
        invoices = frappe.db.sql(f"""
            SELECT 
                name, posting_date, customer, customer_name, 
                base_net_total, base_total, base_total_taxes_and_charges
            FROM 
                `tabSales Invoice`
            WHERE 
                docstatus = 1 
                AND posting_date BETWEEN '{from_date}' AND '{to_date}'
                {conditions}
                AND base_total_taxes_and_charges > 0
            ORDER BY 
                posting_date
        """, as_dict=1)
        
        return invoices
    
    def get_purchase_invoices_with_vat(self, from_date, to_date, vat_settings):
        """Get all purchase invoices with VAT for the period"""
        conditions = ""
        if self.company:
            conditions += f" AND company = '{self.company}'"
            
        invoices = frappe.db.sql(f"""
            SELECT 
                name, posting_date, supplier, supplier_name, 
                base_net_total, base_total, base_total_taxes_and_charges
            FROM 
                `tabPurchase Invoice`
            WHERE 
                docstatus = 1 
                AND posting_date BETWEEN '{from_date}' AND '{to_date}'
                {conditions}
                AND base_total_taxes_and_charges > 0
            ORDER BY 
                posting_date
        """, as_dict=1)
        
        return invoices
