// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Housing Benefit', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Recalculate'), () => {
				frm.call('calculate_monthly_benefit').then(() => frm.refresh());
			});
		}
	},
});
