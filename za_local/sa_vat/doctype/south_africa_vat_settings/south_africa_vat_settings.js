frappe.ui.form.on("South Africa VAT Settings", {
	company: function (frm) {
		update_vat_registration_number(frm);
	},
	default_vat_report_company: function (frm) {
		update_vat_registration_number(frm);
	},
	onload: function (frm) {
		// Ensure field is visible and in sync when form loads (server already set it; this handles client-side only updates)
		update_vat_registration_number(frm);
	},
});

function update_vat_registration_number(frm) {
	var company = frm.doc.default_vat_report_company || frm.doc.company;
	if (company) {
		frappe.db.get_value("Company", company, "za_vat_number", function (r) {
			if (r && r.za_vat_number != null) {
				frm.set_value("vat_registration_number", r.za_vat_number);
			} else {
				frm.set_value("vat_registration_number", "");
			}
		});
	} else {
		frm.set_value("vat_registration_number", "");
	}
}
