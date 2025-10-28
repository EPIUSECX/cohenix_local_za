// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fringe Benefit', {
	refresh: function(frm) {
		if (!frm.doc.__islocal && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Calculate Taxable Value'), function() {
				frm.call('calculate_taxable_value').then(() => {
					frm.refresh();
				});
			});
			
			frm.add_custom_button(__('Generate Monthly Breakdown'), function() {
				frm.call('generate_monthly_breakdown').then(() => {
					frm.refresh_field('monthly_breakdown');
				});
			});
		}
	},
	
	benefit_type: function(frm) {
		// Clear linked details when benefit type changes
		if (frm.doc.benefit_type !== 'Company Car') {
			frm.set_value('company_car_details', '');
		}
		if (frm.doc.benefit_type !== 'Housing') {
			frm.set_value('housing_details', '');
		}
		if (frm.doc.benefit_type !== 'Low Interest Loan') {
			frm.set_value('loan_details', '');
		}
	},
	
	from_date: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date) {
			frm.trigger('calculate_taxable_value');
		}
	},
	
	to_date: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date) {
			if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
				frappe.msgprint(__('To Date cannot be before From Date'));
				frm.set_value('to_date', '');
			}
		}
	}
});

