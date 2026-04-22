frappe.ui.form.on('Workplace Injury', {
	refresh: function(frm) {
		// Check if HRMS is installed
		frappe.call({
			method: 'za_local.utils.hrms_detection.is_hrms_installed',
			callback: function(r) {
				if (!r.message) {
					// Hide leave-related fields if HRMS is not installed
					frm.set_df_property('requires_leave', 'hidden', 1);
					frm.set_df_property('leave_days', 'hidden', 1);
					frm.set_df_property('leave_application', 'hidden', 1);
					
					// Clear leave requirement if it was set
					if (frm.doc.requires_leave) {
						frm.set_value('requires_leave', 0);
					}
				}
			}
		});
	}
});

