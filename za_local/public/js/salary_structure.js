frappe.ui.form.on('Salary Structure', {
	onload: function(frm) {
		// Filter Company Contribution salary components
		if (frm.fields_dict['company_contribution']) {
			frm.fields_dict['company_contribution'].grid.get_field('salary_component').get_query = function(doc) {
				return {
					filters: {
						"type": "Company Contribution"
					}
				};
			};
		}

		hide_flexible_benefits_fields(frm);
	},
	refresh: function(frm) {
		hide_flexible_benefits_fields(frm);
	}
});

// Hide the unused "Flexible Benefits" FIELDS (cafeteria-style benefits are not
// used in SA payroll). Hide the fields only — never the containing section.
// On Salary Structure these fields share a section with Payroll Frequency and the
// "Salary Slip Based on Timesheet" controls, so hiding the section (as the old
// code did via DOM manipulation and a MutationObserver) wrongly hid Payroll
// Frequency. These fields are also hidden via property setters; this is belt-and-
// suspenders at the form level.
function hide_flexible_benefits_fields(frm) {
	['employee_benefits', 'max_benefits'].forEach(function(fieldname) {
		if (frm.fields_dict[fieldname]) {
			frm.toggle_display(fieldname, false);
		}
	});
}
