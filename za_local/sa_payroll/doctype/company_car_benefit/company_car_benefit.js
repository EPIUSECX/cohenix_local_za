// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company Car Benefit', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Recalculate'), function() {
				frm.call('calculate_monthly_benefit').then(() => {
					frm.refresh();
				});
			});
		}
	},
	
	private_km_per_month: function(frm) {
		frm.trigger('calculate_usage');
	},
	
	business_km_per_month: function(frm) {
		frm.trigger('calculate_usage');
	},
	
	calculate_usage: function(frm) {
		const private_km = flt(frm.doc.private_km_per_month);
		const business_km = flt(frm.doc.business_km_per_month);
		const total = private_km + business_km;
		
		frm.set_value('total_km_per_month', total);
		
		if (total > 0) {
			frm.set_value('private_use_percentage', (private_km / total) * 100);
		}
	},
	
	purchase_price: function(frm) {
		frm.trigger('calculate_monthly_benefit');
	},
	
	co2_emissions: function(frm) {
		if (frm.doc.co2_emissions) {
			frappe.call({
				method: 'za_local.sa_payroll.doctype.company_car_benefit.company_car_benefit.get_co2_multiplier',
				args: {
					co2_emissions: frm.doc.co2_emissions
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('CO2 Bracket: {0}, Multiplier: {1}x', 
								[r.message.bracket, r.message.multiplier]),
							indicator: 'blue'
						});
					}
				}
			});
		}
		frm.trigger('calculate_monthly_benefit');
	},
	
	calculate_monthly_benefit: function(frm) {
		if (frm.doc.purchase_price && frm.doc.co2_emissions) {
			frm.call('calculate_monthly_benefit').then(() => {
				frm.refresh_fields(['monthly_taxable_value', 'calculation_method']);
			});
		}
	}
});

