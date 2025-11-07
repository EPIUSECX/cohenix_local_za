# Copyright (c) 2025, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe.utils import getdate, add_months, get_first_day, get_last_day, flt
from frappe import _ # Ensure _ is imported for translations

@frappe.whitelist()
def get_company_tax_details(company):
    details = frappe.db.get_value(
        "Company",
        company,
        ["tax_id", "za_sdl_reference_number", "za_uif_reference_number"],
        as_dict=True,
    )
    return details

@frappe.whitelist()
def get_period_dates(tax_year, reconciliation_period):
	try:
		fiscal_year_doc = frappe.get_doc("Fiscal Year", tax_year)
	except frappe.DoesNotExistError:
		frappe.throw(_("Fiscal Year {0} not found.").format(tax_year))

	if reconciliation_period == "Interim":
		from_date = fiscal_year_doc.year_start_date
		to_date = getdate(f"{fiscal_year_doc.year_start_date.year}-08-31")
	elif reconciliation_period == "Final":
		from_date = fiscal_year_doc.year_start_date
		to_date = fiscal_year_doc.year_end_date
	else:
		return None

	return {"from_date": from_date, "to_date": to_date}

class EMP501Reconciliation(Document):
    def validate(self):
        self.validate_dates() # This should be called after tax_year and reconciliation_period are set
        self.calculate_totals()
        
    def validate_dates(self):
        """
        Validate date ranges for EMP501 Reconciliation based on selected Tax Year and Period.
        Also sets from_date and to_date if they are not already set.
        """
        if not self.tax_year:
            frappe.throw(_("Tax Year must be selected first."), title=_("Missing Tax Year"))

        if not self.reconciliation_period:
            frappe.throw(_("Reconciliation Period must be selected."), title=_("Missing Reconciliation Period"))

        # Fetch the selected Fiscal Year document
        try:
            fiscal_year_doc = frappe.get_doc("Fiscal Year", self.tax_year)
        except frappe.DoesNotExistError:
            frappe.throw(_("Fiscal Year {0} not found. Please ensure it exists.").format(self.tax_year), title=_("Invalid Tax Year"))

        expected_from_date = None
        expected_to_date = None

        # Determine expected from_date and to_date based on fiscal_year_doc and reconciliation_period
        # Assumes fiscal_year_doc.year_start_date is March 1st for SA tax year convention
        if self.reconciliation_period == "Interim":
            expected_from_date = fiscal_year_doc.year_start_date
            # Interim period is March 1st to August 31st of the starting year of the fiscal year
            expected_to_date = getdate(f"{fiscal_year_doc.year_start_date.year}-08-31")
        
        elif self.reconciliation_period == "Final":
            expected_from_date = fiscal_year_doc.year_start_date
            expected_to_date = fiscal_year_doc.year_end_date
        
        else:
            frappe.throw(_("Invalid Reconciliation Period selected."), title=_("Validation Error"))

        # If from_date is not set, auto-populate it
        if not self.from_date:
            self.from_date = expected_from_date
        elif getdate(self.from_date) != expected_from_date:
            frappe.throw(
                _("From Date {0} does not match expected start date {1} for Tax Year {2} and {3} period.").format(
                    frappe.utils.formatdate(self.from_date), frappe.utils.formatdate(expected_from_date), self.tax_year, self.reconciliation_period
                ),
                title=_("Invalid From Date")
            )

        # If to_date is not set, auto-populate it
        if not self.to_date:
            self.to_date = expected_to_date
        elif getdate(self.to_date) != expected_to_date:
            frappe.throw(
                _("To Date {0} does not match expected end date {1} for Tax Year {2} and {3} period.").format(
                    frappe.utils.formatdate(self.to_date), frappe.utils.formatdate(expected_to_date), self.tax_year, self.reconciliation_period
                ),
                title=_("Invalid To Date")
            )
            
    def calculate_totals(self):
        self.total_paye = 0
        self.total_sdl = 0
        self.total_uif = 0
        self.total_eti = 0
        
        if self.emp201_submissions:
            for submission_ref in self.emp201_submissions:
                if submission_ref.emp201_submission:
                    try:
                        emp201 = frappe.get_doc("EMP201 Submission", submission_ref.emp201_submission)
                        self.total_paye += flt(emp201.net_paye_payable)
                        self.total_sdl += flt(emp201.sdl_payable)
                        self.total_uif += flt(emp201.uif_payable)
                        self.total_eti += flt(emp201.eti_utilized_current_month)
                    except frappe.DoesNotExistError:
                        frappe.log_error(f"EMP201 Submission {submission_ref.emp201_submission} not found.", "EMP501 Calculate Totals")
        
        self.total_tax_payable = self.total_paye + self.total_sdl + self.total_uif - self.total_eti
    
    def on_submit(self):
        self.status = "Submitted" 
        
    def on_cancel(self):
        self.status = "Cancelled"
        frappe.msgprint(_("EMP501 Reconciliation {0} has been cancelled.").format(self.name))
        
    @frappe.whitelist()
    def fetch_emp201_submissions(self):
        if not self.from_date or not self.to_date:
            frappe.throw(_("Please ensure Tax Year and Reconciliation Period are selected, then save to populate dates, or set From Date and To Date manually."), 
                        title=_("Missing Date Range"))
        if not self.company:
            frappe.throw(_("Company is required to fetch EMP201 submissions"), 
                        title=_("Missing Company"))
            
        self.emp201_submissions = []
        
        from_date = getdate(self.from_date)
        to_date = getdate(self.to_date)
        
        try:
            emp201_docs = frappe.get_all("EMP201 Submission",
                filters={
                    "company": self.company,
                    "docstatus": 1,
                    "submission_period_start_date": [">=", from_date],
                    "submission_period_end_date": ["<=", to_date]
                },
                fields=["name", "submission_period_start_date as submission_date", "net_paye_payable as paye", 
                        "sdl_payable as sdl", "uif_payable as uif", "eti_utilized_current_month as eti"]
            )
        except Exception as e:
            error_msg = str(e)
            if "Unknown column" in error_msg and "submission_period_start_date" in error_msg:
                 frappe.throw(_("The 'EMP201 Submission' Doctype seems to be missing 'submission_period_start_date' or 'submission_period_end_date'. Please check its definition."), title=_("Field Missing"))
            frappe.log_error(frappe.get_traceback())
            frappe.throw(_("Error fetching EMP201 submissions: {0}").format(e), title=_("Fetch Error"))

        for emp201_doc in emp201_docs:
            self.append("emp201_submissions", {
                "emp201_submission": emp201_doc.name,
                "submission_date": emp201_doc.submission_date,
                "paye": emp201_doc.paye,
                "sdl": emp201_doc.sdl,
                "uif": emp201_doc.uif,
                "eti": emp201_doc.eti
            })
            
        self.calculate_totals()
        return self
    
    @frappe.whitelist()
    def generate_irp5_certificates(self):
        if not self.from_date or not self.to_date or not self.tax_year or not self.company:
            frappe.throw(_("Company, Tax Year, From Date, and To Date are required to generate IRP5s."))
            
        salary_slips = frappe.get_all("Salary Slip",
            filters={
                "company": self.company,
                "start_date": ["<=", self.to_date],
                "end_date": [">=", self.from_date],
                "docstatus": 1
            },
            fields=["distinct employee", "employee_name"]
        )
        
        unique_employees = {sl.employee: sl.employee_name for sl in salary_slips}

        self.irp5_certificates = []
        
        created_count = 0
        for emp_id, emp_name in unique_employees.items():
            existing_cert_name = frappe.db.get_value("IRP5 Certificate", {
                "employee": emp_id,
                "tax_year": self.tax_year,
                "company": self.company,
                "reconciliation_period": self.reconciliation_period
            }, "name")
            
            cert_status = "Previously Generated"
            irp5_cert_name = existing_cert_name

            if not existing_cert_name:
                try:
                    cert = frappe.new_doc("IRP5 Certificate")
                    cert.employee = emp_id
                    cert.tax_year = self.tax_year
                    cert.company = self.company
                    cert.from_date = self.from_date
                    cert.to_date = self.to_date
                    cert.reconciliation_period = self.reconciliation_period
                    cert.insert(ignore_permissions=True)
                    cert_status = cert.status
                    irp5_cert_name = cert.name
                    created_count +=1
                except Exception as e:
                    frappe.log_error(f"Failed to create IRP5 for {emp_id}: {e}", "IRP5 Generation")
                    continue
            
            self.append("irp5_certificates", {
                "irp5_certificate": irp5_cert_name,
                "employee": emp_id,
                "employee_name": emp_name,
                "status": cert_status
            })
        
        self.save()
        frappe.msgprint(_("{0} IRP5 certificates processed. {1} newly created.").format(len(unique_employees), created_count))
        return len(unique_employees)
    
    @frappe.whitelist()
    def submit_to_sars(self):
        if self.docstatus != 1:
             frappe.throw(_("Document must be submitted before sending to SARS."))
            
        sars_settings = frappe.get_single("SARS e-Filing Integration")
        if not sars_settings.get("enabled"):
            frappe.throw(_("SARS e-Filing Integration is not enabled in settings."))
            
        submission_data = {
            "emp501": {
                "reference": self.name,
                "tax_year": self.tax_year,
                "period": self.reconciliation_period,
                "from_date": self.from_date,
                "to_date": self.to_date,
                "paye_reference": self.paye_reference_number,
                "sdl_reference": self.sdl_reference_number,
                "uif_reference": self.uif_reference_number,
                "totals": {
                    "paye": self.total_paye,
                    "sdl": self.total_sdl,
                    "uif": self.total_uif,
                    "eti": self.total_eti,
                    "total_payable": self.total_tax_payable
                }
            }
        }
        
        self.sars_submission_status = "Submitted"
        self.sars_submission_date = frappe.utils.now_datetime()
        self.sars_submission_reference = f"SARS-{frappe.utils.random_string(10).upper()}"
        self.sars_response = json.dumps({"status": "success", "message": "Submission accepted by SARS (mock)"})
        self.save()
        
        frappe.msgprint(_("EMP501 successfully submitted to SARS (mock). Reference: {0}").format(self.sars_submission_reference))
        return {
            "status": "success",
            "message": "EMP501 submitted to SARS successfully (mock)",
            "reference": self.sars_submission_reference
        }
