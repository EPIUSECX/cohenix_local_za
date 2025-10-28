// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Housing Benefit', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Recalculate'), function() {
				frm.call('calculate_monthly_benefit').then(() => {
					frm.refresh();
				});
			});
		}
	},
	
	monthly_rental_value: function(frm) {
		frm.trigger('calculate_monthly_benefit');
	},
	
	electricity_contribution: function(frm) {
		frm.trigger('calculate_monthly_benefit');
	},
	
	water_contribution: function(frm) {
		frm.trigger('calculate_monthly_benefit');
	},
	
	owned_by: function(frm) {
		if (frm.doc.owned_by) {
			frappe.call({
				method: 'za_local.sa_payroll.doctype.housing_benefit.housing_benefit.get_housing_tax_rate',
				args: {
					owned_by: frm.doc.owned_by
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('Tax Treatment: {0}', [r.message.treatment]),
							indicator: 'blue'
						});
					}
				}
			});
		}
		frm.trigger('calculate_monthly_benefit');
	},
	
	calculate_monthly_benefit: function(frm) {
		if (frm.doc.monthly_rental_value && frm.doc.owned_by) {
			frm.call('calculate_monthly_benefit').then(() => {
				frm.refresh_fields(['monthly_taxable_value', 'calculation_method']);
			});
		}
	}
});
