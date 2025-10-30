# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import get_link_to_form, add_months, get_first_day, get_last_day


class BulkIT3bCertificateGeneration(Document):
	@frappe.whitelist()
	def get_periods(self, advanced_filters: list = None) -> list:
		"""Get periods that need IT3b certificates generated"""
		if not advanced_filters:
			advanced_filters = []
		
		# Get all possible periods in the tax year
		periods = self.get_period_list()
		
		# For each period, check if IT3b certificate already exists
		result = []
		for period in periods:
			# Check if certificate exists for this period
			existing = frappe.db.exists(
				"IT3b Certificate",
				{
					"company": self.company,
					"tax_year": self.tax_year,
					"fiscal_period": period,
					"docstatus": ["!=", 2]  # Not cancelled
				}
			)
			
			if not existing:
				# Get EMP201 submissions for this period to show totals
				period_start, period_end = self.get_period_dates(period)
				
				emp201_total = frappe.db.sql("""
					SELECT 
						SUM(gross_paye) as total_paye,
						SUM(gross_uif) as total_uif,
						SUM(gross_sdl) as total_sdl,
						SUM(eti_utilized) as total_eti
					FROM `tabEMP201 Submission`
					WHERE company = %(company)s
					AND submission_period_start_date >= %(start)s
					AND submission_period_end_date <= %(end)s
					AND docstatus = 1
				""", {
					"company": self.company,
					"start": period_start,
					"end": period_end
				}, as_dict=True)
				
				result.append({
					"fiscal_period": period,
					"total_paye": emp201_total[0].total_paye or 0 if emp201_total else 0,
					"total_uif": emp201_total[0].total_uif or 0 if emp201_total else 0,
					"total_sdl": emp201_total[0].total_sdl or 0 if emp201_total else 0,
					"total_eti": emp201_total[0].total_eti or 0 if emp201_total else 0,
					"status": "Pending Generation"
				})
		
		return result
	
	def get_period_list(self):
		"""Get list of periods based on from_period and to_period"""
		all_periods = [
			"March", "April", "May", "June", "July", "August",
			"September", "October", "November", "December", "January", "February"
		]
		
		if self.from_period and self.to_period:
			from_idx = all_periods.index(self.from_period)
			to_idx = all_periods.index(self.to_period)
			
			if from_idx <= to_idx:
				return all_periods[from_idx:to_idx + 1]
			else:
				# Wrap around (e.g., March to February)
				return all_periods[from_idx:] + all_periods[:to_idx + 1]
		
		return all_periods
	
	def get_period_dates(self, period):
		"""Get start and end dates for a fiscal period"""
		months = {
			"March": 3, "April": 4, "May": 5, "June": 6,
			"July": 7, "August": 8, "September": 9, "October": 10,
			"November": 11, "December": 12, "January": 1, "February": 2
		}
		
		month_num = months[period]
		start_year = int(self.tax_year.split("-")[0])
		
		# Adjust year for Jan/Feb (next calendar year)
		if month_num < 3:
			start_year += 1
		
		period_start = get_first_day(f"{start_year}-{month_num:02d}-01")
		period_end = get_last_day(f"{start_year}-{month_num:02d}-01")
		
		return period_start, period_end
	
	@frappe.whitelist()
	def bulk_generate_certificates(self, periods: list) -> None:
		"""Generate IT3b certificates in bulk for selected periods"""
		if not periods:
			frappe.throw(_("No periods selected for generation"))
		
		# If more than 30 periods, enqueue as background job
		if len(periods) <= 30:
			return self._bulk_generate_certificates(periods)
		
		frappe.enqueue(
			self._bulk_generate_certificates,
			timeout=3000,
			periods=periods,
			queue="long"
		)
		frappe.msgprint(
			_("Generation of IT3b Certificates has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue"
		)
	
	def _bulk_generate_certificates(self, periods: list) -> None:
		"""Internal method to generate certificates"""
		success, failure = [], []
		count = 0
		savepoint = "before_it3b_generation"
		
		for period_data in periods:
			try:
				frappe.db.savepoint(savepoint)
				
				# Create IT3b Certificate
				cert = frappe.get_doc({
					"doctype": "IT3b Certificate",
					"company": self.company,
					"tax_year": self.tax_year,
					"fiscal_period": period_data["fiscal_period"],
					"status": "Draft"
				})
				
				# Generate certificate data from EMP201
				cert.insert(ignore_permissions=True)
				cert.generate_certificate_data()
				cert.save(ignore_permissions=True)
				
				success.append({
					"doc": get_link_to_form("IT3b Certificate", cert.name),
					"period": period_data["fiscal_period"]
				})
				
			except Exception as e:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk IT3b Generation - Failed for period {period_data.get('fiscal_period')}: {str(e)}",
					reference_doctype="IT3b Certificate"
				)
				failure.append({
					"period": period_data.get("fiscal_period"),
					"error": str(e)
				})
			
			count += 1
			frappe.publish_progress(
				count * 100 / len(periods),
				title=_("Generating IT3b Certificates...")
			)
		
		# Publish results
		frappe.publish_realtime(
			"completed_bulk_it3b_generation",
			message={"success": success, "failure": failure},
			doctype="Bulk IT3b Certificate Generation",
			after_commit=True
		)
		
		# Show summary message
		if success:
			frappe.msgprint(
				_("Successfully generated {0} IT3b Certificate(s)").format(len(success)),
				indicator="green",
				alert=True
			)
		
		if failure:
			frappe.msgprint(
				_("Failed to generate {0} certificate(s). Check Error Log for details.").format(len(failure)),
				indicator="red",
				alert=True
			)

