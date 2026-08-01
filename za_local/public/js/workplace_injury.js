frappe.ui.form.on("Workplace Injury", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !frm.has_perm("write")) {
			return;
		}

		if (!frm.doc.oid_claim) {
			frm.add_custom_button(__("Create OID Claim"), () => {
				frappe.confirm(__("Create an OID Claim for this workplace injury?"), () => {
					frm.call("create_oid_claim_after_submit").then((response) => {
						if (response.message) {
							frm.reload_doc();
						}
					});
				});
			});
		} else {
			frm.add_custom_button(__("View OID Claim"), () => {
				frappe.set_route("Form", "OID Claim", frm.doc.oid_claim);
			});
		}

		if (!frm.doc.leave_application) {
			frm.add_custom_button(__("Create Leave Application"), () => {
				frappe.prompt(
					[
						{
							fieldname: "leave_days",
							label: __("Leave Days"),
							fieldtype: "Int",
							reqd: 1,
							default: frm.doc.leave_days || 7,
						},
					],
					(values) => {
						frm.call("create_leave_application_after_submit", values).then((response) => {
							if (response.message) {
								frm.reload_doc();
							}
						});
					},
					__("Create Injury Leave"),
					__("Create")
				);
			});
		} else {
			frm.add_custom_button(__("View Leave Application"), () => {
				frappe.set_route("Form", "Leave Application", frm.doc.leave_application);
			});
		}
	},

	medical_attention_required(frm) {
		frm.toggle_reqd("medical_provider", frm.doc.medical_attention_required);
		frm.toggle_reqd("expected_recovery_date", frm.doc.medical_attention_required);
	},

	requires_leave(frm) {
		frm.toggle_reqd("leave_days", frm.doc.requires_leave);
		setLeaveDaysFromRecoveryDate(frm);
	},

	expected_recovery_date(frm) {
		setLeaveDaysFromRecoveryDate(frm);
	},
});

function setLeaveDaysFromRecoveryDate(frm) {
	if (!frm.doc.requires_leave || !frm.doc.expected_recovery_date || !frm.doc.injury_date) {
		return;
	}
	frm.set_value(
		"leave_days",
		frappe.datetime.get_diff(frm.doc.expected_recovery_date, frm.doc.injury_date) + 1
	);
}
