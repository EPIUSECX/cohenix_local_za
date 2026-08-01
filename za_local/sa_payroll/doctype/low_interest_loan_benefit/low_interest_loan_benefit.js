// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Low Interest Loan Benefit', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Refresh Official Rate'), () => {
				frm.call('get_official_rate').then(() => frm.refresh());
			});
			frm.add_custom_button(__('Recalculate'), () => {
				frm.call('calculate_interest_benefit').then(() => frm.refresh());
			});
		}
	},
});
