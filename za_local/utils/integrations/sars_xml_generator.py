"""
SARS XML Generator

Generates XML files for SARS e-Filing submissions:
- EMP501 Annual Reconciliation
- IRP5 Bulk Submission
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate
import xml.etree.ElementTree as ET
from xml.dom import minidom


class SARSXMLGenerator:
    """Base class for SARS XML generation"""
    
    def __init__(self, company):
        self.company = frappe.get_doc("Company", company)
        self.tax_year = None
        
    def generate_emp501_xml(self, emp501_doc):
        """
        Generate EMP501 XML for e-Filing
        
        Schema: SARS EMP501 XSD (available from SARS eFiling)
        """
        root = ET.Element("EMP501")
        root.set("xmlns", "http://sars.gov.za/payroll")
        root.set("version", "1.0")
        
        # Employer details
        employer = ET.SubElement(root, "Employer")
        ET.SubElement(employer, "RegistrationNumber").text = self.company.get("za_paye_registration_number", "")
        ET.SubElement(employer, "TradingName").text = self.company.company_name
        
        # Tax year
        ET.SubElement(root, "TaxYear").text = emp501_doc.tax_year
        
        # Certificate totals
        totals = ET.SubElement(root, "CertificateTotals")
        ET.SubElement(totals, "TotalPAYE").text = str(flt(emp501_doc.total_paye, 2))
        ET.SubElement(totals, "TotalUIF").text = str(flt(emp501_doc.total_uif, 2))
        ET.SubElement(totals, "TotalSDL").text = str(flt(emp501_doc.total_sdl, 2))
        
        # Employee certificates (IRP5s)
        certificates = ET.SubElement(root, "EmployeeCertificates")
        
        irp5_list = frappe.get_all(
            "IRP5 Certificate",
            filters={"tax_year": emp501_doc.tax_year, "company": self.company.name},
            fields=["name"]
        )
        
        for irp5_name in irp5_list:
            irp5 = frappe.get_doc("IRP5 Certificate", irp5_name.name)
            cert = self._add_irp5_to_xml(certificates, irp5)
        
        return self._prettify_xml(root)
    
    def _add_irp5_to_xml(self, parent, irp5):
        """Add IRP5 certificate to XML"""
        cert = ET.SubElement(parent, "Certificate")
        cert.set("number", irp5.certificate_number or "")
        
        # Employee details
        employee = ET.SubElement(cert, "Employee")
        ET.SubElement(employee, "IDNumber").text = irp5.employee_id_number or ""
        ET.SubElement(employee, "Initials").text = irp5.employee_initials or ""
        ET.SubElement(employee, "Surname").text = irp5.employee_surname or ""
        
        # Income details
        income = ET.SubElement(cert, "Income")
        ET.SubElement(income, "Remuneration").text = str(flt(irp5.total_remuneration, 2))
        ET.SubElement(income, "TaxableIncome").text = str(flt(irp5.total_taxable_income, 2))
        ET.SubElement(income, "PAYE").text = str(flt(irp5.total_paye, 2))
        ET.SubElement(income, "UIF").text = str(flt(irp5.total_uif, 2))
        
        return cert
    
    def generate_irp5_bulk_xml(self, tax_year):
        """Generate IRP5 bulk submission XML"""
        frappe.msgprint(_("IRP5 bulk XML generation - To be implemented"))
        return ""
    
    def _prettify_xml(self, elem):
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


@frappe.whitelist()
def generate_emp501_xml(emp501_name):
    """API endpoint to generate EMP501 XML"""
    emp501 = frappe.get_doc("EMP501 Reconciliation", emp501_name)
    generator = SARSXMLGenerator(emp501.company)
    xml_content = generator.generate_emp501_xml(emp501)
    
    filename = f"EMP501_{emp501.tax_year}_{emp501.company}.xml"
    
    return {
        "xml_content": xml_content,
        "filename": filename
    }
