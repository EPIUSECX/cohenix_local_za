# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt

class COIDAAnnualReturn(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_assessment_fee()
        
    def validate_dates(self):
        """Validate that the dates match the fiscal year"""
        if self.fiscal_year:
            fiscal_year = frappe.get_doc("Fiscal Year", self.fiscal_year)
            if getdate(self.from_date) != getdate(fiscal_year.year_start_date):
                self.from_date = fiscal_year.year_start_date
            
            if getdate(self.to_date) != getdate(fiscal_year.year_end_date):
                self.to_date = fiscal_year.year_end_date
    
    def calculate_assessment_fee(self):
        """Calculate the assessment fee based on earnings and rate"""
        if not self.assessment_rate:
            # Try to get the rate from COIDA Settings
            if self.industry_class:
                coida_settings = frappe.get_single("COIDA Settings")
                for rate in coida_settings.industry_rates:
                    if rate.industry_class == self.industry_class:
                        self.assessment_rate = rate.assessment_rate
                        break
        
        if self.total_annual_earnings and self.assessment_rate:
            self.assessment_fee = flt(self.total_annual_earnings) * flt(self.assessment_rate) / 100
    
    def on_submit(self):
        self.status = "Submitted"
        self.submission_date = frappe.utils.today()
    
    def on_cancel(self):
        self.status = "Draft"
        self.submission_date = None
    
    @frappe.whitelist()
    def fetch_employee_data(self):
        """Fetch employee count and earnings data from salary slips"""
        if not self.company or not self.from_date or not self.to_date:
            frappe.throw(_("Company and date range are required to fetch data"))
        
        # Get total employees
        employees = frappe.db.sql("""
            SELECT COUNT(DISTINCT employee) as count
            FROM `tabSalary Slip`
            WHERE company = %s 
            AND start_date >= %s 
            AND end_date <= %s
            AND docstatus = 1
        """, (self.company, self.from_date, self.to_date), as_dict=True)
        
        if employees and employees[0].count:
            self.total_employees = employees[0].count
        
        # Get total earnings
        earnings = frappe.db.sql("""
            SELECT SUM(gross_pay) as total
            FROM `tabSalary Slip`
            WHERE company = %s 
            AND start_date >= %s 
            AND end_date <= %s
            AND docstatus = 1
        """, (self.company, self.from_date, self.to_date), as_dict=True)
        
        if earnings and earnings[0].total:
            self.total_annual_earnings = earnings[0].total
        
        # Get director earnings if applicable
        director_earnings = frappe.db.sql("""
            SELECT SUM(ss.gross_pay) as total
            FROM `tabSalary Slip` ss
            JOIN `tabEmployee` e ON ss.employee = e.name
            WHERE ss.company = %s 
            AND ss.start_date >= %s 
            AND ss.end_date <= %s
            AND ss.docstatus = 1
            AND e.designation IN ('Director', 'Managing Director', 'Executive Director')
        """, (self.company, self.from_date, self.to_date), as_dict=True)
        
        if director_earnings and director_earnings[0].total:
            self.director_earnings = director_earnings[0].total
        
        # Calculate assessment fee
        self.calculate_assessment_fee()
        
        return self
