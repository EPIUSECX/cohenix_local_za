// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company Car Benefit', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Recalculate'), () => {
				frm.call('calculate_monthly_benefit').then(() => frm.refresh());
			});
		}
	},

	private_km_per_month: calculate_usage,
	business_km_per_month: calculate_usage,
});

function calculate_usage(frm) {
	const private_km = flt(frm.doc.private_km_per_month);
	const business_km = flt(frm.doc.business_km_per_month);
	const total = private_km + business_km;
	frm.set_value('total_km_per_month', total);
	frm.set_value('private_use_percentage', total ? private_km / total * 100 : 0);
}
