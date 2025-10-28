"""
EFT (Electronic Funds Transfer) File Generator

Generates bank payment files in multiple South African bank formats:
- Standard Bank
- ABSA
- FNB
- Nedbank
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate
from datetime import datetime


class EFTFileGenerator:
    """Base class for EFT file generation"""
    
    def __init__(self, payroll_entry):
        self.payroll_entry = frappe.get_doc("Payroll Entry", payroll_entry)
        self.company = frappe.get_doc("Company", self.payroll_entry.company)
        self.bank_account = None
        
    def generate_file(self, bank_format="standard_bank"):
        """Generate EFT file in specified bank format"""
        if bank_format == "standard_bank":
            return self.generate_standard_bank()
        elif bank_format == "absa":
            return self.generate_absa()
        elif bank_format == "fnb":
            return self.generate_fnb()
        elif bank_format == "nedbank":
            return self.generate_nedbank()
        else:
            frappe.throw(_("Unsupported bank format: {0}").format(bank_format))
    
    def get_salary_slips(self):
        """Get all salary slips for the payroll entry"""
        return frappe.get_all(
            "Salary Slip",
            filters={
                "payroll_entry": self.payroll_entry.name,
                "docstatus": 1
            },
            fields=["name", "employee", "employee_name", "net_pay", "bank_name", 
                   "bank_ac_no", "branch_code"]
        )
    
    def generate_standard_bank(self):
        """
        Generate Standard Bank EFT file format
        
        Format:
        - Header record (1 line)
        - Beneficiary records (1 per employee)
        - Trailer record (1 line)
        """
        lines = []
        salary_slips = self.get_salary_slips()
        
        # Header record
        header = self._generate_standard_bank_header(len(salary_slips))
        lines.append(header)
        
        # Beneficiary records
        for slip in salary_slips:
            beneficiary = self._generate_standard_bank_beneficiary(slip)
            lines.append(beneficiary)
        
        # Trailer record
        total_amount = sum([flt(slip.net_pay) for slip in salary_slips])
        trailer = self._generate_standard_bank_trailer(len(salary_slips), total_amount)
        lines.append(trailer)
        
        return "\n".join(lines)
    
    def _generate_standard_bank_header(self, record_count):
        """Generate Standard Bank header record"""
        # Format: Fixed width fields
        # Record Type (1) + Creation Date (8) + User Reference (20) + ...
        creation_date = formatdate(getdate(), "yyyyMMdd")
        user_ref = self.payroll_entry.name[:20].ljust(20)
        
        header = (
            "1"  # Record type
            + creation_date
            + user_ref
            + str(record_count).zfill(6)
            + "0" * 50  # Reserved/filler
        )
        return header
    
    def _generate_standard_bank_beneficiary(self, slip):
        """Generate Standard Bank beneficiary record"""
        # Format: Fixed width fields
        # Record Type (2) + Branch Code (6) + Account Number (11) + Amount (13) + ...
        
        branch_code = (slip.branch_code or "").zfill(6)[:6]
        account_number = (slip.bank_ac_no or "").ljust(11)[:11]
        amount = str(int(flt(slip.net_pay) * 100)).zfill(13)  # Amount in cents
        beneficiary_name = slip.employee_name[:32].ljust(32)
        
        record = (
            "2"  # Record type
            + branch_code
            + account_number
            + amount
            + beneficiary_name
            + "0" * 20  # Reserved/filler
        )
        return record
    
    def _generate_standard_bank_trailer(self, record_count, total_amount):
        """Generate Standard Bank trailer record"""
        total_cents = str(int(flt(total_amount) * 100)).zfill(15)
        
        trailer = (
            "3"  # Record type
            + str(record_count).zfill(6)
            + total_cents
            + "0" * 50  # Reserved/filler
        )
        return trailer
    
    def generate_absa(self):
        """Generate ABSA EFT file format"""
        # Similar structure to Standard Bank with ABSA-specific field positions
        frappe.msgprint(_("ABSA format generation - To be implemented"))
        return ""
    
    def generate_fnb(self):
        """Generate FNB EFT file format"""
        frappe.msgprint(_("FNB format generation - To be implemented"))
        return ""
    
    def generate_nedbank(self):
        """Generate Nedbank EFT file format"""
        frappe.msgprint(_("Nedbank format generation - To be implemented"))
        return ""


@frappe.whitelist()
def generate_eft_file(payroll_entry, bank_format="standard_bank"):
    """
    API endpoint to generate EFT file
    
    Args:
        payroll_entry: Payroll Entry name
        bank_format: Bank format (standard_bank/absa/fnb/nedbank)
        
    Returns:
        dict: file_content and filename
    """
    generator = EFTFileGenerator(payroll_entry)
    file_content = generator.generate_file(bank_format)
    
    filename = f"EFT_{payroll_entry}_{formatdate(getdate(), 'yyyyMMdd')}.txt"
    
    return {
        "file_content": file_content,
        "filename": filename
    }
