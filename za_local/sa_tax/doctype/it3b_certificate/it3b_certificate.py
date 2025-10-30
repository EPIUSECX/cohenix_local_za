# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt, get_first_day, get_last_day, add_months


class IT3bCertificate(Document):
	def autoname(self):
		"""Generate certificate number based on company, tax year, and period"""
		if not self.certificate_number:
			self.set_certificate_number()
		
	def validate(self):
		"""Validate IT3b Certificate"""
		self.validate_period()
		self.calculate_totals()
		
	def before_submit(self):
		"""Actions before submission"""
		if not self.certificate_number:
			self.set_certificate_number()
		self.status = "Submitted"
		
	def set_certificate_number(self):
		"""Generate unique certificate number"""
		company_abbr = frappe.db.get_value("Company", self.company, "abbr")
		period_code = self.fiscal_period[:3].upper()
		year_code = self.tax_year.split("-")[0][-2:]  # Last 2 digits of start year
		
		# Find next sequential number
		existing = frappe.get_all(
			"IT3b Certificate",
			filters={
				"company": self.company,
				"tax_year": self.tax_year,
				"fiscal_period": self.fiscal_period,
				"name": ["!=", self.name]
			},
			order_by="creation desc",
			limit=1
		)
		
		seq = 1
		if existing:
			# Extract sequence from last certificate
			last_cert = frappe.db.get_value("IT3b Certificate", existing[0].name, "certificate_number")
			if last_cert:
				try:
					seq = int(last_cert.split("-")[-1]) + 1
				except:
					seq = 1
					
		self.certificate_number = f"IT3B-{company_abbr}-{year_code}{period_code}-{seq:04d}"
		
	def validate_period(self):
		"""Validate fiscal period and tax year"""
		if not self.tax_year or not self.fiscal_period:
			frappe.throw(_("Tax Year and Fiscal Period are required"))
			
		# Ensure tax year format is YYYY-YYYY
		if "-" not in self.tax_year or len(self.tax_year.split("-")) != 2:
			frappe.throw(_("Tax Year must be in format YYYY-YYYY"))
			
	def calculate_totals(self):
		"""Calculate total payable to SARS"""
		self.total_payable = (
			flt(self.total_paye) +
			flt(self.total_uif) +
			flt(self.total_sdl) -
			flt(self.total_eti)
		)
		
	@frappe.whitelist()
	def generate_certificate_data(self):
		"""Generate IT3b certificate data from EMP201 submissions"""
		from frappe.utils import add_months, get_first_day, get_last_day
		
		# Get period date range
		period_start, period_end = self.get_period_dates()
		
		# Fetch EMP201 submissions for the period
		emp201_submissions = frappe.get_all(
			"EMP201 Submission",
			filters={
				"company": self.company,
				"submission_period_start_date": [">=", period_start],
				"submission_period_end_date": ["<=", period_end],
				"docstatus": 1
			},
			fields=["name", "gross_paye", "gross_uif", "gross_sdl", "eti_utilized"]
		)
		
		if not emp201_submissions:
			frappe.msgprint(_("No submitted EMP201 records found for this period"))
			return
			
		# Sum up totals
		self.total_paye = sum(flt(sub.gross_paye) for sub in emp201_submissions)
		self.total_uif = sum(flt(sub.gross_uif) for sub in emp201_submissions)
		self.total_sdl = sum(flt(sub.gross_sdl) for sub in emp201_submissions)
		self.total_eti = sum(flt(sub.eti_utilized) for sub in emp201_submissions)
		
		self.calculate_totals()
		frappe.msgprint(_("Certificate data generated successfully"))
		
	def get_period_dates(self):
		"""Get start and end dates for the fiscal period"""
		# SA tax year runs from March 1 to February 28/29
		months = {
			"March": 3, "April": 4, "May": 5, "June": 6,
			"July": 7, "August": 8, "September": 9, "October": 10,
			"November": 11, "December": 12, "January": 1, "February": 2
		}
		
		month_num = months[self.fiscal_period]
		start_year = int(self.tax_year.split("-")[0])
		
		# Adjust year for Jan/Feb (next calendar year)
		if month_num < 3:
			start_year += 1
			
		period_start = get_first_day(f"{start_year}-{month_num:02d}-01")
		period_end = get_last_day(f"{start_year}-{month_num:02d}-01")
		
		return period_start, period_end
		
	@frappe.whitelist()
	def export_pdf(self):
		"""Export IT3b certificate as PDF"""
		try:
			# Generate PDF using print format
			from frappe.utils.pdf import get_pdf
			
			# Get the IT3b Certificate Print format HTML
			html = frappe.get_print(
				"IT3b Certificate",
				self.name,
				print_format="IT3b Certificate Print",
				doc=self,
				no_letterhead=False
			)
			
			# Generate PDF
			pdf = get_pdf(html)
			
			# Save as file attachment
			file_name = f"IT3B_{self.certificate_number or self.name}.pdf"
			
			# Create file doc
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": file_name,
				"attached_to_doctype": "IT3b Certificate",
				"attached_to_name": self.name,
				"content": pdf,
				"is_private": 1
			})
			file_doc.save(ignore_permissions=True)
			
			frappe.msgprint(
				_("PDF generated successfully: {0}").format(file_name),
				indicator="green",
				alert=True
			)
			
			return {
				"file_url": file_doc.file_url,
				"file_name": file_name
			}
			
		except Exception as e:
			frappe.log_error(f"IT3b PDF Generation Error: {str(e)}", "IT3b Certificate PDF Export")
			frappe.throw(_("Failed to generate PDF: {0}").format(str(e)))

