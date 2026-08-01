frappe.ui.form.on("COIDA Annual Return", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && frm.has_perm("write")) {
			frm.add_custom_button(__("Fetch Employee Data"), () => {
				frm.call("fetch_employee_data").then((response) => {
					if (!response.message) {
						return;
					}
					frm.refresh_fields();
					frappe.show_alert({
						message: __("COIDA-applicable employee earnings fetched"),
						indicator: "green",
					});
				});
			});
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Print COIDA Return"), () => {
				frappe.set_route("print", frm.doctype, frm.docname);
			});
		}
	},

	company(frm) {
		frm.set_value("assessment_rate", 0);
	},

	industry_class(frm) {
		frm.set_value("assessment_rate", 0);
	},
});
