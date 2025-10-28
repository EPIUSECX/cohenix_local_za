// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Low Interest Loan Benefit', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Get Official Rate'), function() {
				frm.call('get_official_rate').then(() => {
					frm.refresh();
				});
			});
			
			frm.add_custom_button(__('Recalculate'), function() {
				frm.call('calculate_interest_benefit').then(() => {
					frm.refresh();
				});
			});
		}
	},
	
	loan_amount: function(frm) {
		frm.trigger('calculate_benefit');
	},
	
	interest_rate: function(frm) {
		frm.trigger('calculate_benefit');
	},
	
	official_interest_rate: function(frm) {
		frm.trigger('calculate_benefit');
	},
	
	calculate_benefit: function(frm) {
		if (frm.doc.loan_amount && frm.doc.interest_rate && frm.doc.official_interest_rate) {
			const loan = flt(frm.doc.loan_amount);
			const actual = flt(frm.doc.interest_rate) / 100;
			const official = flt(frm.doc.official_interest_rate) / 100;
			
			if (official > actual) {
				const annual_benefit = (official - actual) * loan;
				const monthly_benefit = annual_benefit / 12;
				frm.set_value('monthly_interest_benefit', monthly_benefit);
				
				frappe.show_alert({
					message: __('Monthly Benefit: R{0}', [monthly_benefit.toFixed(2)]),
					indicator: 'green'
				});
			} else {
				frm.set_value('monthly_interest_benefit', 0);
				frappe.show_alert({
					message: __('No benefit - actual rate >= official rate'),
					indicator: 'orange'
				});
			}
		}
	}
});
