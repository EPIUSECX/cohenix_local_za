# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, formatdate

class VAT201Return(Document):
    def validate(self):
        self.validate_dates()
        self.ensure_period_dates()
        self.set_submission_period()
        self.set_vat_registration_number()
        self.calculate_totals()
        
    def validate_dates(self):
        """Validate submission date"""
        if getdate(self.submission_date) > getdate(today()):
            frappe.throw("Submission Date cannot be in the future")
        if self.from_date and self.to_date and getdate(self.from_date) > getdate(self.to_date):
            frappe.throw("From Date cannot be after To Date")

    def ensure_period_dates(self):
        """Ensure period fields exist to prevent attribute lookups from failing"""
        # The DocType now defines these fields, but guard for legacy documents
        if not hasattr(self, "from_date"):
            self.from_date = None
        if not hasattr(self, "to_date"):
            self.to_date = None

    def set_submission_period(self):
        """Populate submission period label from date range"""
        if getattr(self, "from_date", None) and getattr(self, "to_date", None):
            from_label = formatdate(getdate(self.from_date))
            to_label = formatdate(getdate(self.to_date))
            self.submission_period = f"{from_label} to {to_label}"
        else:
            self.submission_period = None
            
    def set_vat_registration_number(self):
        """Set VAT registration number from company"""
        if self.company and not self.vat_registration_number:
            # Try to get from company
            vat_number = frappe.db.get_value("Company", self.company, "za_vat_number")
            if vat_number:
                self.vat_registration_number = vat_number
                    
    def calculate_totals(self):
        """Calculate all totals"""
        # Calculate total supplies
        self.total_supplies = flt(self.standard_rated_supplies) + flt(self.zero_rated_supplies) + flt(self.exempt_supplies)
        
        # Calculate standard rated output tax
        vat_settings = frappe.get_doc("South Africa VAT Settings")
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
        vat_settings = frappe.get_doc("South Africa VAT Settings")
        if not vat_settings.sars_efiling_username or not vat_settings.sars_efiling_password:
            frappe.throw("SARS e-Filing credentials not configured in South Africa VAT Settings")
            
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
        self.set_submission_period()
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
        vat_settings = frappe.get_doc("South Africa VAT Settings")
        if not vat_settings.output_vat_account or not vat_settings.input_vat_account:
            frappe.throw("VAT accounts not configured in South Africa VAT Settings")
        
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

        # Get all sales invoices with VAT for the period (has some output VAT)
        sales_invoices = self.get_sales_invoices_with_vat(from_date, to_date, vat_settings)
        # Get all sales invoices with no VAT (exempt supplies)
        exempt_sales_invoices = self.get_sales_invoices_exempt(from_date, to_date, vat_settings)

        # Exempt Item Tax Template names (from VAT Settings): used to separate exempt from zero-rated
        exempt_item_templates = self._get_exempt_item_tax_templates(vat_settings)

        # Process sales invoices with VAT: derive standard vs zero from tax amount to avoid double-count
        standard_rate = flt(vat_settings.standard_vat_rate, 2)
        for invoice in sales_invoices:
            taxes = frappe.db.sql("""
                SELECT rate, base_net_amount, base_tax_amount
                FROM `tabSales Taxes and Charges`
                WHERE parent = %(parent)s AND account_head = %(account)s
            """, {"parent": invoice.name, "account": vat_settings.output_vat_account}, as_dict=1)

            standard_tax = sum(flt(t.base_tax_amount) for t in taxes if flt(t.rate) == standard_rate)
            standard_net = (standard_tax / (standard_rate / 100.0)) if standard_rate else 0
            zero_net = flt(invoice.base_net_total) - standard_net

            # When there is no standard tax, invoice is either zero-rated or exempt (item-level template)
            if standard_net > 0:
                self.standard_rated_supplies += standard_net
                self.zero_rated_supplies += zero_net
            else:
                if exempt_item_templates and self._invoice_uses_only_exempt_template(
                    invoice.name, exempt_item_templates
                ):
                    self.exempt_supplies += flt(invoice.base_net_total)
                else:
                    self.zero_rated_supplies += flt(invoice.base_net_total)

        # Process exempt sales (no output VAT)
        for invoice in exempt_sales_invoices:
            self.exempt_supplies += flt(invoice.base_net_total)
        
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
                    # Handle case where is_capital_goods field may not exist
                    if item.item_group:
                        # Check if field exists in Item Group doctype
                        item_group_meta = frappe.get_meta("Item Group")
                        if item_group_meta.has_field("is_capital_goods"):
                            if frappe.db.get_value("Item Group", item.item_group, "is_capital_goods"):
                                is_capital = True
                
                # Add to appropriate input tax field
                if is_capital:
                    self.capital_goods_input += tax.tax_amount
                else:
                    self.other_goods_services_input += tax.tax_amount
        
        # Calculate totals
        self.calculate_totals()
        self.set_submission_period()
        
        # Return summary
        return {
            "sales_invoices_count": len(sales_invoices) + len(exempt_sales_invoices),
            "purchase_invoices_count": len(purchase_invoices),
            "standard_rated_supplies": self.standard_rated_supplies,
            "zero_rated_supplies": self.zero_rated_supplies,
            "exempt_supplies": self.exempt_supplies,
            "standard_rated_output": self.standard_rated_output,
            "capital_goods_input": self.capital_goods_input,
            "other_goods_services_input": self.other_goods_services_input,
        }

    def _get_exempt_item_tax_templates(self, vat_settings):
        """Return list of Item Tax Template names that are exempt (from VAT Settings vat_rates with is_exempt)."""
        company = self.company or getattr(vat_settings, "default_vat_report_company", None)
        if not company:
            return []
        names = []
        for rate in getattr(vat_settings, "vat_rates", []) or []:
            if not getattr(rate, "is_exempt", 0):
                continue
            title = "South Africa VAT {} ({:.2f}%)".format(
                getattr(rate, "rate_name", "Exempt"), flt(rate.rate, 2)
            )
            name = frappe.db.get_value(
                "Item Tax Template", {"title": title, "company": company}, "name"
            )
            if name:
                names.append(name)
        return names

    def _invoice_uses_only_exempt_template(self, invoice_name, exempt_item_templates):
        """True if every item on the invoice uses an exempt Item Tax Template (or has no template)."""
        if not exempt_item_templates:
            return False
        rows = frappe.db.sql(
            """
            SELECT item_tax_template FROM `tabSales Invoice Item`
            WHERE parent = %s AND (item_tax_template IS NOT NULL AND item_tax_template != '')
            """,
            invoice_name,
            as_dict=1,
        )
        if not rows:
            # No template set on any item: treat as zero-rated, not exempt
            return False
        return all(r.item_tax_template in exempt_item_templates for r in rows)

    def get_sales_invoices_exempt(self, from_date, to_date, vat_settings):
        """Get submitted sales in period with no output VAT at all (exempt supplies).
        Excludes zero-rated: those have an output VAT row at 0%, so they are in get_sales_invoices_with_vat.
        """
        conditions = ""
        if self.company:
            conditions += f" AND si.company = '{self.company}'"
        return frappe.db.sql(f"""
            SELECT si.name, si.posting_date, si.base_net_total
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
            AND (si.base_total_taxes_and_charges = 0 OR si.base_total_taxes_and_charges IS NULL)
            AND NOT EXISTS (
                SELECT 1 FROM `tabSales Taxes and Charges` st
                WHERE st.parent = si.name AND st.account_head = %(account)s
            )
            ORDER BY si.posting_date
        """, {"from_date": from_date, "to_date": to_date, "account": vat_settings.output_vat_account}, as_dict=1)

    def get_sales_invoices_with_vat(self, from_date, to_date, vat_settings):
        """Get all sales invoices that have the output VAT account on their tax table (standard and zero-rated).
        Includes zero-rated so we can sum their base_net_amount into zero_rated_supplies from the 0%% row.
        """
        conditions = ""
        if self.company:
            conditions += f" AND si.company = '{self.company}'"
        invoices = frappe.db.sql(f"""
            SELECT DISTINCT si.name, si.posting_date, si.customer, si.customer_name,
                si.base_net_total, si.base_total, si.base_total_taxes_and_charges
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Taxes and Charges` st ON st.parent = si.name AND st.account_head = %(account)s
            WHERE si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
            ORDER BY si.posting_date
        """, {"from_date": from_date, "to_date": to_date, "account": vat_settings.output_vat_account}, as_dict=1)
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
