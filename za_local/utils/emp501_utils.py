"""
EMP501 Utility Functions

Utilities for generating and validating EMP501 (Employer Reconciliation Declaration)
submissions to SARS.
"""

import frappe
import csv
from frappe.utils import format_date, getdate
from tempfile import NamedTemporaryFile


@frappe.whitelist()
def generate_emp501_csv(emp501_name):
    """
    Generate a CSV file for EMP501 submission to SARS e-Filing.
    
    Args:
        emp501_name (str): Name of the EMP501 Reconciliation document
        
    Returns:
        dict: Information about the generated file
    """
    emp501 = frappe.get_doc("EMP501 Reconciliation", emp501_name)
    
    if not emp501:
        frappe.throw("EMP501 Reconciliation not found")
    
    # Create CSV file
    with NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_file:
        try:
            writer = csv.writer(temp_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Write header row
            writer.writerow([
                "Record Type", "Tax Year", "Period", "PAYE Reference", "SDL Reference", 
                "UIF Reference", "Trading Name", "Submission Date", "PAYE Total", 
                "SDL Total", "UIF Total", "ETI Total"
            ])
            
            # Write EMP501 summary row
            writer.writerow([
                "EMP501",
                emp501.tax_year,
                emp501.reconciliation_period,
                emp501.paye_reference_number,
                emp501.sdl_reference_number,
                emp501.uif_reference_number,
                frappe.db.get_value("Company", emp501.company, "company_name"),
                format_date(emp501.submission_date),
                f"{emp501.total_paye:.2f}",
                f"{emp501.total_sdl:.2f}",
                f"{emp501.total_uif:.2f}",
                f"{emp501.total_eti:.2f}"
            ])
            
            # Add EMP201 records
            for emp201_ref in emp501.emp201_submissions:
                emp201 = frappe.get_doc("EMP201 Submission", emp201_ref.emp201_submission)
                
                # Format period as YYYYMM
                month_map = {
                    "January": "01", "February": "02", "March": "03", "April": "04",
                    "May": "05", "June": "06", "July": "07", "August": "08",
                    "September": "09", "October": "10", "November": "11", "December": "12"
                }
                
                period_year = str(getdate(emp201.submission_period_start_date).year)
                period_month = month_map.get(emp201.month, "00")
                period_yyyymm = f"{period_year}{period_month}"
                
                writer.writerow([
                    "EMP201",
                    emp501.tax_year,
                    period_yyyymm,
                    emp501.paye_reference_number,
                    emp501.sdl_reference_number,
                    emp501.uif_reference_number,
                    frappe.db.get_value("Company", emp501.company, "company_name"),
                    format_date(emp201.submission_date),
                    f"{emp201_ref.paye:.2f}",
                    f"{emp201_ref.sdl:.2f}",
                    f"{emp201_ref.uif:.2f}",
                    f"{emp201_ref.eti:.2f}"
                ])
            
            # Add IRP5 certificate records
            for irp5_ref in emp501.irp5_certificates:
                irp5 = frappe.get_doc("IRP5 Certificate", irp5_ref.irp5_certificate)
                
                employee_name = frappe.db.get_value("Employee", irp5.employee, "employee_name") or ""
                tax_number = irp5.get("tax_number") or ""
                id_number = irp5.get("id_number") or ""
                
                writer.writerow([
                    irp5.get("certificate_type", "IRP5"),
                    emp501.tax_year,
                    irp5.get("certificate_type", "IRP5"),
                    tax_number,
                    id_number,
                    employee_name,
                    irp5.certificate_number,
                    format_date(irp5.get("issue_date") or emp501.submission_date),
                    f"{irp5.total_income:.2f}",
                    f"{irp5.paye:.2f}",
                    f"{irp5.uif:.2f}",
                    f"{irp5.get('eti', 0):.2f}"
                ])
            
            temp_file.flush()
            
            # Save file
            with open(temp_file.name, 'rb') as f:
                file_content = f.read()
            
            file_name = f"EMP501_{emp501.tax_year}_{emp501.reconciliation_period}.csv"
            
            frappe.local.response.filename = file_name
            frappe.local.response.filecontent = file_content
            frappe.local.response.type = "download"
            
            return {
                "success": True,
                "message": "EMP501 CSV generated successfully",
                "filename": file_name
            }
            
        except Exception as e:
            frappe.log_error(f"Error generating EMP501 CSV: {str(e)}", "EMP501 Generation")
            frappe.throw(f"Error generating EMP501 CSV: {str(e)}")


def validate_emp501_reconciliation(emp501):
    """
    Validate EMP501 reconciliation against EMP201 submissions and IRP5 certificates.
    
    Args:
        emp501: EMP501 Reconciliation document
        
    Returns:
        dict: Validation results
    """
    validation_errors = []
    
    # Validate EMP201 totals
    emp201_total_paye = sum(ref.paye for ref in emp501.emp201_submissions)
    emp201_total_uif = sum(ref.uif for ref in emp501.emp201_submissions)
    emp201_total_sdl = sum(ref.sdl for ref in emp501.emp201_submissions)
    emp201_total_eti = sum(ref.eti for ref in emp501.emp201_submissions)
    
    tolerance = 0.01  # Allow 1 cent tolerance
    
    if abs(emp501.total_paye - emp201_total_paye) > tolerance:
        validation_errors.append(
            f"PAYE mismatch: EMP501 total ({emp501.total_paye}) vs EMP201 total ({emp201_total_paye})"
        )
    
    if abs(emp501.total_uif - emp201_total_uif) > tolerance:
        validation_errors.append(
            f"UIF mismatch: EMP501 total ({emp501.total_uif}) vs EMP201 total ({emp201_total_uif})"
        )
    
    if abs(emp501.total_sdl - emp201_total_sdl) > tolerance:
        validation_errors.append(
            f"SDL mismatch: EMP501 total ({emp501.total_sdl}) vs EMP201 total ({emp201_total_sdl})"
        )
    
    if abs(emp501.total_eti - emp201_total_eti) > tolerance:
        validation_errors.append(
            f"ETI mismatch: EMP501 total ({emp501.total_eti}) vs EMP201 total ({emp201_total_eti})"
        )
    
    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "emp201_totals": {
            "paye": emp201_total_paye,
            "uif": emp201_total_uif,
            "sdl": emp201_total_sdl,
            "eti": emp201_total_eti
        }
    }


def fetch_emp201_submissions(company, from_date, to_date):
    """
    Fetch EMP201 submissions for a company within a date range.
    
    Args:
        company (str): Company name
        from_date (date): Period start date
        to_date (date): Period end date
        
    Returns:
        list: List of EMP201 Submission documents
    """
    submissions = frappe.get_all(
        "EMP201 Submission",
        filters={
            "company": company,
            "submission_period_start_date": [">=", from_date],
            "submission_period_end_date": ["<=", to_date],
            "docstatus": 1
        },
        fields=["*"],
        order_by="submission_period_start_date"
    )
    
    return submissions


def fetch_irp5_certificates(company, tax_year):
    """
    Fetch IRP5 certificates for a company for a tax year.
    
    Args:
        company (str): Company name
        tax_year (str): Tax year (e.g., "2024/2025")
        
    Returns:
        list: List of IRP5 Certificate documents
    """
    certificates = frappe.get_all(
        "IRP5 Certificate",
        filters={
            "company": company,
            "tax_year": tax_year,
            "docstatus": 1
        },
        fields=["*"],
        order_by="employee"
    )
    
    return certificates

