"""
SARS XML Generator

Generates XML files for SARS e-Filing submissions:
- EMP501 Annual Reconciliation
- IRP5 Bulk Submission
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate


class SARSXMLGenerator:
    """Base class for SARS XML generation"""

    def __init__(self, company):
        self.company = frappe.get_doc("Company", company)
        self.tax_year = None

    def generate_emp501_xml(self, emp501_doc):
        """
        EMP501 XML is intentionally disabled until SARS BRS validation is implemented.
        """
        frappe.throw(
            _(
                "SARS EMP501 XML/BRS export is not supported in this release. "
                "Use the EMP501 working paper and CSV review export, then file manually through SARS eFiling."
            ),
            title=_("Manual Filing Required"),
        )

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
        ET.SubElement(income, "Remuneration").text = str(flt(irp5.gross_taxable_income, 2))
        ET.SubElement(income, "TaxableIncome").text = str(flt(irp5.gross_taxable_income, 2))
        ET.SubElement(income, "PAYE").text = str(flt(irp5.paye, 2))
        ET.SubElement(income, "UIF").text = str(flt(irp5.uif, 2))

        return cert

    def generate_irp5_bulk_xml(self, tax_year):
        """Generate IRP5 bulk submission XML"""
        frappe.throw(
            _("SARS IRP5 bulk XML/BRS export is not supported in this release."),
            title=_("Manual Filing Required"),
        )

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
