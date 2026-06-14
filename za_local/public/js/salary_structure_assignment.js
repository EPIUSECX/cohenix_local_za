frappe.ui.form.on('Salary Structure Assignment', {
	onload: function(frm) {
		hide_flexible_benefits_fields(frm);
	},
	refresh: function(frm) {
		hide_flexible_benefits_fields(frm);
	}
});

// Hide the unused "Flexible Benefits" fields (not used in SA payroll). On the
// Salary Structure Assignment these live in their own "Employee Benefits" section
// (employee_benefits_section), so hiding that Section Break field hides the whole
// section cleanly — without the brittle DOM-section hiding / MutationObserver the
// old code used, which risked hiding unrelated fields. Also hidden via property
// setters; this is a form-level fallback.
function hide_flexible_benefits_fields(frm) {
	['employee_benefits_section', 'employee_benefits', 'max_benefits'].forEach(function(fieldname) {
		if (frm.fields_dict[fieldname]) {
			frm.toggle_display(fieldname, false);
		}
	});
}
