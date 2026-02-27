// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tax Directive', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === 'Active') {
			frm.add_custom_button(__('Cancel Directive'), function() {
				frappe.confirm(
					__('Are you sure you want to cancel this tax directive?'),
					function() {
						frappe.call({
							method: 'frappe.client.cancel',
							args: {
								doctype: frm.doctype,
								name: frm.docname
							},
							callback: function() {
								frm.reload_doc();
							}
						});
					}
				);
			});
		}
	},
	
	directive_type: function(frm) {
		// Clear fields based on directive type
		if (frm.doc.directive_type !== 'Reduced Tax Rate') {
			frm.set_value('tax_rate_override', 0);
		}
		if (frm.doc.directive_type !== 'Fixed Amount') {
			frm.set_value('fixed_amount', 0);
		}
		if (frm.doc.directive_type !== 'Garnishee Order') {
			frm.set_value('garnishee_creditor', '');
			frm.set_value('garnishee_amount', 0);
			frm.set_value('garnishee_percentage', 0);
		}
	},
	
	effective_to: function(frm) {
		if (frm.doc.effective_from && frm.doc.effective_to) {
			if (frappe.datetime.get_day_diff(frm.doc.effective_to, frm.doc.effective_from) < 0) {
				frappe.msgprint(__('Effective To date cannot be before Effective From date'));
				frm.set_value('effective_to', '');
			}
		}
	}
});

