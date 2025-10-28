// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('IT3b Certificate', {
	refresh: function(frm) {
		if (!frm.doc.__islocal && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Generate Certificate Data'), function() {
				frm.call('generate_certificate_data').then(() => {
					frm.refresh();
				});
			});
		}
		
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Export PDF'), function() {
				frm.call('export_pdf');
			});
			
			frm.add_custom_button(__('Mark as Filed'), function() {
				frappe.db.set_value(frm.doctype, frm.docname, 'status', 'Filed with SARS')
					.then(() => {
						frm.reload_doc();
					});
			});
		}
	},
	
	company: function(frm) {
		if (frm.doc.company && frm.doc.tax_year && frm.doc.fiscal_period) {
			frm.trigger('set_certificate_number');
		}
	},
	
	tax_year: function(frm) {
		if (frm.doc.company && frm.doc.tax_year && frm.doc.fiscal_period) {
			frm.trigger('set_certificate_number');
		}
	},
	
	fiscal_period: function(frm) {
		if (frm.doc.company && frm.doc.tax_year && frm.doc.fiscal_period) {
			frm.trigger('set_certificate_number');
		}
	}
});

