# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, today, add_months, get_first_day, get_last_day
import os
import json
import base64
from io import BytesIO

# Conditional imports for PDF generation
pdf_generation_available = False
try:
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import black
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdf_generation_available = True
except ImportError:
    frappe.log_error("PDF generation libraries not installed. Install PyPDF2 and reportlab for PDF functionality.")



class IRP5Certificate(Document):
    def autoname(self):
        """Set name based on generation mode"""
        if getattr(self, 'generation_mode', None) == 'Bulk':
            # For bulk generation, create a placeholder certificate number
            if not self.certificate_number:
                self.set_bulk_certificate_number()
        else:
            # For individual generation, create certificate number if we have required fields
            if self.employee and self.tax_year and not self.certificate_number:
                self.set_certificate_number()
        
        # The name will be set from the certificate_number field
        if self.certificate_number:
            self.name = self.certificate_number
    
    def validate(self):
        # Only require employee for Individual mode
        if getattr(self, 'generation_mode', None) == 'Bulk':
            # Bulk: require main fields, but not employee
            if not self.tax_year or not self.from_date or not self.to_date or not self.reconciliation_period:
                frappe.throw(_("Tax Year, From Date, To Date, and Reconciliation Period are required for Bulk generation."), title=_("Missing Required Fields"))
            # For bulk generation, set a placeholder certificate number if not set
            if not self.certificate_number:
                self.set_bulk_certificate_number()
            self.validate_dates()
        else:
            # Individual: require employee and main fields
            if not self.employee:
                frappe.throw(_("Employee is required"), title=_("Missing Employee"))
            if self.employee and self.tax_year and not self.certificate_number:
                self.set_certificate_number()
            self.validate_dates()
            self.validate_employee()
        if not self.status:
            self.status = "Draft"
    
    def validate_dates(self):
        if not self.from_date or not self.to_date:
            frappe.throw(_("Both From Date and To Date are required"), title=_("Missing Required Dates"))
        from_date, to_date = getdate(self.from_date), getdate(self.to_date)
        if from_date > to_date:
            frappe.throw(_("From Date cannot be after To Date"), title=_("Invalid Date Range"))

        if self.reconciliation_period == "Interim":
            if not (from_date.month == 3 and from_date.day == 1):
                frappe.throw(_("For Interim reconciliation, From Date must be March 1"), title=_("Invalid Interim Period Start Date"))
            if not (to_date.month == 8 and to_date.day == 31):
                frappe.throw(_("For Interim reconciliation, To Date must be August 31"), title=_("Invalid Interim Period End Date"))
        elif self.reconciliation_period == "Final":
            if not (from_date.month == 3 and from_date.day == 1):
                frappe.throw(_("For Final reconciliation, From Date must be March 1"), title=_("Invalid Final Period Start Date"))
            expected_end_month, expected_end_day = 2, 28
            if (from_date.year + 1) % 4 == 0 and ((from_date.year + 1) % 100 != 0 or (from_date.year + 1) % 400 == 0):
                expected_end_day = 29
            if not (to_date.month == expected_end_month and to_date.day == expected_end_day):
                frappe.throw(_("For Final reconciliation, To Date must be the last day of February"), title=_("Invalid Final Period End Date"))
            if to_date.year != from_date.year + 1:
                frappe.throw(_("Final period must span from March 1 to February of the next year"), title=_("Invalid Tax Year"))

    def validate_employee(self):
        # Only validate employee if present (for Individual mode)
        if not self.employee:
            return
        if not self.employee_name: self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
        if not self.company: self.company = frappe.db.get_value("Employee", self.employee, "company")
            
    def set_certificate_number(self):
        if not self.employee or not self.tax_year:
            frappe.log_error("Attempted to set certificate number without employee or tax year.", "IRP5 Certificate Numbering")
            return
        employee_id = frappe.db.get_value("Employee", self.employee, "name")
        tax_year_str = str(self.tax_year).replace("/", "-")
        unique_hash = frappe.generate_hash(length=8)
        self.certificate_number = f"IRP5-{tax_year_str}-{employee_id}-{unique_hash}"

    def set_bulk_certificate_number(self):
        """Set a placeholder certificate number for bulk generation"""
        if not self.tax_year:
            frappe.log_error("Attempted to set bulk certificate number without tax year.", "IRP5 Certificate Bulk Numbering")
            return
        tax_year_str = str(self.tax_year).replace("/", "-")
        unique_hash = frappe.generate_hash(length=8)
        self.certificate_number = f"IRP5-BULK-{tax_year_str}-{unique_hash}"

    def before_submit(self):
        self.status = "Prepared"
        self.calculate_totals()
        

    def calculate_totals(self):
        self.paye, self.uif, self.sdl = 0, 0, 0
        # Sum PAYE and UIF from deduction_details
        for deduction in self.deduction_details:
            if deduction.deduction_code == "4102":
                self.paye += flt(deduction.amount) # PAYE
            elif deduction.deduction_code == "4141":
                self.uif += flt(deduction.amount) # UIF Employee
            # If SDL is ever in deductions (rare), include it
            elif deduction.deduction_code == "4142":
                self.sdl += flt(deduction.amount)

        # SDL is typically a company contribution (code 4142)
        for contribution in getattr(self, 'company_contribution_details', []):
            if getattr(contribution, 'contribution_code', None) == "4142" or (getattr(contribution, 'description', "").strip().upper() == "SDL"):
                self.sdl += flt(contribution.amount)

        self.total_tax_payable = self.paye + self.uif + self.sdl - flt(self.eti)
        
    @frappe.whitelist()
    def generate_certificate_data(self):
        # For Bulk, employee may not be set on the main form
        if getattr(self, 'generation_mode', None) == 'Bulk':
            if not self.tax_year or not self.from_date or not self.to_date:
                frappe.throw(_("Tax Year, From Date, and To Date are required for Bulk generation."))
        else:
            if not self.employee or not self.tax_year:
                frappe.throw(_("Employee and Tax Year must be set to generate certificate data and number."))
            if not self.employee or not self.from_date or not self.to_date:
                frappe.throw(_("Employee, From Date, and To Date are required. Ensure Tax Year and Period are set."))
        if not self.certificate_number and getattr(self, 'generation_mode', None) != 'Bulk':
            self.set_certificate_number()

        from_date, to_date = getdate(self.from_date), getdate(self.to_date)
        self.income_details, self.deduction_details, self.company_contribution_details = [], [], []
        
        # For Bulk, this method is called per-employee, so self.employee will be set
        salary_slips = frappe.get_all("Salary Slip",
            filters={"employee": self.employee, "start_date": [">=", from_date], "end_date": ["<=", to_date], "docstatus": 1},
            fields=["name"], order_by="start_date"
        )
        
        if not salary_slips:
            frappe.msgprint(_("No salary slips found for this employee in the specified period"))
            self.calculate_eti()
            self.calculate_totals()
            return {"message": "No salary slips found, totals (including ETI) recalculated."}
            
        income_map, deduction_map, contribution_map = {}, {}, {}
        
        for slip_data in salary_slips:
            salary_slip_doc = frappe.get_doc("Salary Slip", slip_data.name)

            if not salary_slip_doc:
                frappe.log_error(f"Could not find Salary Slip {slip_data.name}", "IRP5 Certificate Generation")
                continue
            
            for earning in salary_slip_doc.earnings:
                is_contribution = frappe.db.get_value("Salary Component", earning.salary_component, "is_company_contribution")
                if is_contribution:
                    contribution_code = self.get_deduction_code(earning.salary_component, is_company_contribution=True)
                    if contribution_code:
                        contribution_map.setdefault(contribution_code, {"code": contribution_code, "description": self.get_deduction_description(contribution_code), "amount": 0})
                        contribution_map[contribution_code]["amount"] += flt(earning.amount)
                else:
                    income_code = self.get_income_code(earning.salary_component)
                    if not income_code: continue
                    income_map.setdefault(income_code, {"code": income_code, "description": self.get_income_description(income_code), "amount": 0})
                    income_map[income_code]["amount"] += flt(earning.amount)
            
            for deduction in salary_slip_doc.deductions:
                deduction_code = self.get_deduction_code(deduction.salary_component, is_company_contribution=False)
                if not deduction_code:
                    continue
                deduction_map.setdefault(deduction_code, {"code": deduction_code, "description": self.get_deduction_description(deduction_code), "amount": 0})
                deduction_map[deduction_code]["amount"] += flt(deduction.amount)

            for contribution in salary_slip_doc.get("company_contribution", []):
                contribution_code = self.get_deduction_code(contribution.salary_component, is_company_contribution=True)
                if contribution_code:
                    contribution_map.setdefault(contribution_code, {"code": contribution_code, "description": self.get_deduction_description(contribution_code), "amount": 0})
                    contribution_map[contribution_code]["amount"] += flt(contribution.amount)
        
        for code, details in income_map.items():
            self.append("income_details", {"income_code": code, "description": details["description"], "amount": details["amount"], "tax_year": self.tax_year, "period": self.reconciliation_period})
            
        for code, details in deduction_map.items():
            self.append("deduction_details", {"deduction_code": code, "description": details["description"], "amount": details["amount"], "tax_year": self.tax_year, "period": self.reconciliation_period})

        for code, details in contribution_map.items():
            self.append("company_contribution_details", {"contribution_code": code, "description": details["description"], "amount": details["amount"]})
            
        self.calculate_eti() 
        self.calculate_totals()
        return {"income_count": len(income_map), "deduction_count": len(deduction_map), "contribution_count": len(contribution_map), "message": "Certificate data generated."}
        
    def get_income_code(self, salary_component):
        # Placeholder - expand this with actual mappings
        component_mapping = {
            "Basic Salary": "3601", "Basic": "3601", "Overtime": "3607", "Bonus": "3605", "Commission": "3605",
            "Annual Payment": "3605", "Leave Encashment": "3605", 
            "Travel Allowance": "3701", # Example, verify correct code
            "Subsistence Allowance": "3704", # Example, verify correct code
            "Uniform Allowance": "3713", # Example, verify correct code
            # Fringe Benefits (e.g., Use of Motor Vehicle) might have codes like 3802
        }
        return component_mapping.get(salary_component)
    
    def get_income_description(self, income_code):
        # Placeholder - expand this
        descriptions = {"3601": "Gross Remuneration", "3605": "Annual Payment", "3607": "Overtime", "3701": "Travel Allowance (Taxable)"}
        return descriptions.get(income_code, f"Income Code {income_code}")
    
    def get_deduction_code(self, salary_component, is_company_contribution=False):
        # Placeholder - expand this with actual mappings
        # Some codes are specific to employee or employer
        component_mapping_employee = {
            "PAYE": "4102", "Income Tax": "4102", 
            "UIF Contribution": "4141", # Employee UIF
            "Pension Fund": "4001", # Employee Pension
            "Retirement Annuity Fund": "4006", # Employee RA
            "Medical Aid": "4005", # Employee Medical
        }
        component_mapping_employer = {
            "UIF Contribution": "4141", # Employer UIF (often same code as employee for reporting, but context matters)
            "Pension Fund": "4472", # Employer Pension Contribution
            "Medical Aid": "4474", # Employer Medical Contribution
            "SDL": "4142", "Skills Development Levy": "4142", # Skills Development Levy (Employer)
            "Company Contribution": "4497",
            # Group Life, Disability etc. might have codes like 44xx
        }
        if is_company_contribution:
            return component_mapping_employer.get(salary_component)
        else:
            return component_mapping_employee.get(salary_component)

    def get_deduction_description(self, deduction_code):
        # Placeholder - expand this
        descriptions = {
            "4102": "PAYE", "4141": "UIF Contribution", "4001": "Pension Fund Contribution (Current)",
            "4006": "Retirement Annuity Fund Contributions", "4005": "Medical Scheme Fees (Employee Paid)",
            "4472": "Employer's Pension Fund Contributions", 
            "4474": "Employer's Medical Scheme Contributions",
            "4142": "SDL",
            "4497": "Company Contributions"
        }
        return descriptions.get(deduction_code, f"Deduction Code {deduction_code}")
        
    def calculate_eti(self):
        disable_eti_globally = frappe.db.get_single_value("Payroll Settings", "custom_disable_eti_calculation")
        if disable_eti_globally:
            self.eti = 0
            frappe.log_error(message=f"ETI calculation globally disabled. IRP5: {self.name}", title="ETI Calculation")
            return 
        if not self.employee: self.eti = 0; return
        employee = frappe.get_doc("Employee", self.employee)
        if not employee.date_of_birth: self.eti = 0; return
        if not self.to_date: self.eti = 0; return
        end_date, birth_date = getdate(self.to_date), getdate(employee.date_of_birth)
        age_years = end_date.year - birth_date.year - ((end_date.month, end_date.day) < (birth_date.month, birth_date.day))
        if not (18 <= age_years <= 29) and not frappe.db.get_value("Employee", employee.name, "custom_special_economic_zone"):
            self.eti = 0; return
        if not employee.date_of_joining: self.eti = 0; return
        date_of_joining = getdate(employee.date_of_joining)
        if date_of_joining < getdate("2013-10-01"): self.eti = 0; return
        employment_months = (end_date.year - date_of_joining.year) * 12 + end_date.month - date_of_joining.month - (end_date.day < date_of_joining.day)
        if employment_months >= 24: self.eti = 0; return # ETI for first 24 qualifying months (0-23)
            
        total_income = sum(d.amount for d in self.income_details if d.income_code in ["3601", "3801", "3802"]) # Example ETI qualifying income codes
        
        months_in_period = 0
        if not self.from_date or not self.to_date: self.eti = 0; return
        temp_from_date, loop_to_date = getdate(self.from_date), getdate(self.to_date)
        while temp_from_date <= loop_to_date: 
            months_in_period += 1
            temp_from_date = get_first_day(add_months(temp_from_date, 1))
        if months_in_period == 0: self.eti = 0; return
            
        monthly_remuneration = total_income / months_in_period if months_in_period else 0
        is_first_12_months = employment_months < 12
        eti_amount_per_month = self.calculate_eti_amount(monthly_remuneration, is_first_12_months)
        self.eti = eti_amount_per_month * months_in_period
        
    def calculate_eti_amount(self, monthly_remuneration, is_first_12_months):
        if monthly_remuneration < 2000: return 0
        # SARS ETI values for 2023/2024 - these should be configurable or updated yearly
        # Max ETI for first 12 months: R1500. Max ETI for second 12 months: R750 (examples, verify current rates)
        max_eti_first_year = 1500 
        max_eti_second_year = 750

        if is_first_12_months:
            if monthly_remuneration <= 2000: return 0 # Should be covered by first check
            elif monthly_remuneration < 4500: return max_eti_first_year * (monthly_remuneration / 4500) # Simplified, actual formula is tiered
            elif monthly_remuneration <= 6500: return max_eti_first_year * (1 - (monthly_remuneration - 4500) / 2000)
            else: return 0
        else: # Second 12 months
            if monthly_remuneration <= 2000: return 0
            elif monthly_remuneration < 4500: return max_eti_second_year * (monthly_remuneration / 4500)
            elif monthly_remuneration <= 6500: return max_eti_second_year * (1 - (monthly_remuneration - 4500) / 2000)
            else: return 0
        
    @frappe.whitelist()
    def export_pdf(self):
        # ... (rest of export_pdf method remains largely the same, ensure it uses self.certificate_number)
        if self.status == "Draft": frappe.throw(_("Cannot export draft certificate..."))
        if not pdf_generation_available: frappe.throw(_("PDF generation libraries not installed..."))
        try:
            if not self.certificate_number: self.set_certificate_number() # Ensure cert number exists
            pdf_content = self.generate_irp5_pdf()
            file_name = f"{self.certificate_number}.pdf"
            file_doc = save_file(file_name, pdf_content, "IRP5 Certificate", self.name, is_private=True)
            frappe.msgprint(_("IRP5 Certificate PDF has been generated..."))
            return file_doc.file_url # Use file_doc object
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"Error generating IRP5 PDF for {self.name}")
            frappe.throw(_("Error generating PDF: {0}").format(str(e)))

    def generate_irp5_pdf(self):
        # ... (rest of generate_irp5_pdf method remains largely the same)
        # Ensure all self.field references are valid and handle None for amounts
        if not pdf_generation_available: frappe.throw(_("PDF generation libraries not installed."))
        template_path = frappe.get_app_path("kartoza", "kartoza", "print_format", "irp5_certificate", "Template_Employee Income Payroll Certificate - IRP5 form.pdf")
        if not os.path.exists(template_path): frappe.throw(_("IRP5 template not found..."))
            
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFillColor(black)
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
            can.setFont("Arial", 10)
        except: can.setFont("Helvetica", 10)
        
        employee_doc = frappe.get_doc("Employee", self.employee)
        company_doc = frappe.get_doc("Company", self.company)
        
        can.drawString(150, 800, self.certificate_number or "")
        can.drawString(150, 780, self.tax_year or "")
        can.drawString(150, 720, company_doc.company_name or "")
        
        company_vat = frappe.db.get_value("Company", self.company, "custom_vat_number") or ""
        company_paye = frappe.db.get_value("Company", self.company, "custom_paye_reference_number") or ""
        company_sdl = frappe.db.get_value("Company", self.company, "custom_sdl_reference_number") or ""
        
        can.drawString(150, 700, company_paye)
        can.drawString(150, 680, company_sdl)
        can.drawString(150, 660, company_vat)
        can.drawString(150, 640, company_doc.company_address or "")
        
        can.drawString(450, 720, employee_doc.employee_name or "")
        id_number = frappe.db.get_value("Employee", self.employee, "custom_id_number") or ""
        tax_number = frappe.db.get_value("Employee", self.employee, "custom_tax_number") or ""
        
        can.drawString(450, 700, id_number)
        can.drawString(450, 680, tax_number)
        can.drawString(450, 640, employee_doc.get("custom_residential_address") or "")
        
        y_pos = 500
        for income in self.income_details:
            can.drawString(100, y_pos, income.income_code or "")
            can.drawString(150, y_pos, income.description or "")
            can.drawString(400, y_pos, str(income.amount) if income.amount is not None else "0.00")
            y_pos -= 15
            
        y_pos = 300
        for deduction in self.deduction_details:
            can.drawString(100, y_pos, deduction.deduction_code or "")
            can.drawString(150, y_pos, deduction.description or "")
            can.drawString(400, y_pos, str(deduction.amount) if deduction.amount is not None else "0.00")
            y_pos -= 15

        y_pos -= 30  # Add space between tables
        can.drawString(100, y_pos, "Company Contributions")
        y_pos -= 15
        
        for contribution in self.company_contribution_details:
            can.drawString(100, y_pos, contribution.contribution_code or "")
            can.drawString(150, y_pos, contribution.description or "")
            can.drawString(400, y_pos, str(contribution.amount) if contribution.amount is not None else "0.00")
            y_pos -= 15
            
        can.drawString(400, 180, str(self.paye) if self.paye is not None else "0.00")
        can.drawString(400, 160, str(self.uif) if self.uif is not None else "0.00")
        can.drawString(400, 140, str(self.sdl) if self.sdl is not None else "0.00")
        can.drawString(400, 120, str(self.eti) if self.eti is not None else "0.00")
        can.drawString(400, 100, str(self.total_tax_payable) if self.total_tax_payable is not None else "0.00")
        
        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        template = PdfReader(template_path)
        output = PdfWriter()
        page = template.pages[0]
        page.merge_page(overlay.pages[0])
        output.add_page(page)
        
        result_pdf = BytesIO()
        output.write(result_pdf)
        result_pdf.seek(0)
        return result_pdf.getvalue()

@frappe.whitelist()
def bulk_generate_certificates(filters_json=None):
    """
    Generate IRP5 Certificates in bulk for employees matching the given filters.
    filters_json: JSON string with filters (e.g., {"company": "...", "tax_year": "...", "from_date": "...", "to_date": "...", "employee_list": [..]})
    Returns a summary of created/updated certificates.
    """
    import json
    filters = json.loads(filters_json) if filters_json else {}
    company = filters.get("company")
    tax_year = filters.get("tax_year")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    reconciliation_period = filters.get("reconciliation_period")
    employee_list = filters.get("employee_list")
    department = filters.get("department")

    # Build employee filter
    emp_filters = {}
    if company:
        emp_filters["company"] = company
    if department:
        emp_filters["department"] = department
    if employee_list:
        emp_filters["name"] = ["in", employee_list]

    employees = frappe.get_all("Employee", filters=emp_filters, fields=["name"])
    if not employees:
        return {"error": "No employees found for the given filters."}
    # Validate required main fields
    if not tax_year or not from_date or not to_date or not reconciliation_period:
        return {"error": "Tax Year, From Date, To Date, and Reconciliation Period must be set on the main form for bulk generation."}

    created, updated, errors = [], [], []
    for emp in employees:
        try:
            cert_filters = {
                "employee": emp.name,
                "tax_year": tax_year,
                "from_date": from_date,
                "to_date": to_date,
            }
            cert = frappe.get_all("IRP5 Certificate", filters=cert_filters, fields=["name"])
            if cert:
                cert_doc = frappe.get_doc("IRP5 Certificate", cert[0].name)
                cert_doc.reconciliation_period = reconciliation_period or cert_doc.reconciliation_period
                cert_doc.employee = emp.name
                cert_doc.tax_year = tax_year
                cert_doc.from_date = from_date
                cert_doc.to_date = to_date
                cert_doc.generate_certificate_data()
                cert_doc.save()
                updated.append(cert_doc.name)
            else:
                cert_doc = frappe.new_doc("IRP5 Certificate")
                cert_doc.employee = emp.name
                cert_doc.tax_year = tax_year
                cert_doc.from_date = from_date
                cert_doc.to_date = to_date
                cert_doc.reconciliation_period = reconciliation_period
                cert_doc.generate_certificate_data()
                cert_doc.save()
                created.append(cert_doc.name)
        except Exception as e:
            errors.append({"employee": emp.name, "error": str(e)})
    return {"created": created, "updated": updated, "errors": errors, "message": f"Bulk IRP5 generation complete. Created: {len(created)}, Updated: {len(updated)}, Errors: {len(errors)}"}

def save_file(file_name, content, dt, dn, is_private=False):
    from frappe.core.doctype.file.file import create_new_folder
    from frappe.utils.file_manager import save_file as _save_file
    if isinstance(content, bytes): content = base64.b64encode(content).decode('utf-8')
    folder_name = "IRP5 Certificates" # Define folder name
    # Ensure folder exists or can be created by user with permission
    # frappe.get_doc({"doctype": "File Folder", "folder_name": folder_name, "is_private": 1}).insert(ignore_if_duplicate=True)
    file_doc = _save_file(file_name, content, dt, dn, folder=folder_name, is_private=is_private) # Pass folder_name
    return file_doc
