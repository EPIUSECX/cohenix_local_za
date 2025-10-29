// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('ZA Local Setup', {
	refresh: function(frm) {
		// Show welcome message for new setup
		if (frm.doc.__islocal) {
			frm.set_intro(__("Welcome to South African Localization! Select which defaults you'd like to load. All settings can be customized later."), 'blue');
		}
		
		// Show completion message
		if (frm.doc.setup_status === 'Completed') {
			frm.set_intro(__("✅ Setup completed successfully on {0}", [frappe.datetime.str_to_user(frm.doc.setup_completed_on)]), 'green');
			frm.disable_save();
		}
		
		// Add custom buttons
		if (frm.doc.setup_status === 'Pending' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Skip Setup'), function() {
				frappe.confirm(
					__('Are you sure you want to skip the setup wizard? You can always run it later from Setup > ZA Local Setup.'),
					function() {
						// Mark as skipped (don't show again)
						frappe.call({
							method: 'za_local.setup.setup_wizard.dismiss_setup_wizard',
							callback: function(r) {
								frappe.msgprint(__('Setup wizard dismissed. You can access it anytime from Setup > ZA Local Setup.'));
								frappe.set_route('Workspace', 'Home');
							}
						});
					}
				);
			});
		}
	},
	
	onload: function(frm) {
		// Set default values for new documents
		if (frm.doc.__islocal) {
			frm.set_value('load_salary_components', 1);
			frm.set_value('load_earnings_components', 1);
			frm.set_value('load_tax_slabs', 1);
			frm.set_value('load_tax_rebates', 1);
			frm.set_value('load_medical_credits', 1);
			frm.set_value('load_business_trip_regions', 1);
		}
	}
});

