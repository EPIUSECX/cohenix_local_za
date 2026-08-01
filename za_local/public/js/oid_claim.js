frappe.ui.form.on("OID Claim", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !frm.has_perm("write")) {
			return;
		}

		if (frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")) {
			addClaimWorkflowButtons(frm);
		}
		addMedicalReportButton(frm);

		if (frm.doc.workplace_injury) {
			frm.add_custom_button(__("View Workplace Injury"), () => {
				frappe.set_route("Form", "Workplace Injury", frm.doc.workplace_injury);
			});
		}
	},
});

function addClaimWorkflowButtons(frm) {
	if (["Submitted", "Under Review"].includes(frm.doc.claim_status)) {
		if (frm.doc.claim_status === "Submitted") {
			frm.add_custom_button(__("Move to Under Review"), () => {
				updateClaimStatus(frm, { status: "Under Review" });
			});
		}

		frm.add_custom_button(__("Approve Claim"), () => {
			frappe.prompt(
				[
					{
						fieldname: "compensation_amount",
						label: __("Compensation Amount"),
						fieldtype: "Currency",
						reqd: 1,
					},
				],
				(values) => updateClaimStatus(frm, { status: "Approved", ...values }),
				__("Approve OID Claim"),
				__("Approve")
			);
		}, __("Actions"));

		frm.add_custom_button(__("Reject Claim"), () => {
			frappe.confirm(__("Reject this OID Claim? This transition cannot be reversed."), () => {
				updateClaimStatus(frm, { status: "Rejected" });
			});
		}, __("Actions"));
	}

	if (frm.doc.claim_status === "Approved") {
		frm.add_custom_button(__("Mark as Paid"), () => {
			frappe.prompt(
				[
					{
						fieldname: "payment_date",
						label: __("Payment Date"),
						fieldtype: "Date",
						reqd: 1,
						default: frappe.datetime.get_today(),
					},
				],
				(values) => updateClaimStatus(frm, { status: "Paid", ...values }),
				__("Record COIDA Payment"),
				__("Mark as Paid")
			);
		}, __("Actions"));
	}
}

function updateClaimStatus(frm, args) {
	return frm.call("update_claim_status", args).then(() => frm.reload_doc());
}

function addMedicalReportButton(frm) {
	frm.add_custom_button(__("Add Medical Report"), () => {
		frappe.prompt(
			[
				{
					fieldname: "report_date",
					label: __("Report Date"),
					fieldtype: "Date",
					reqd: 1,
					default: frappe.datetime.get_today(),
				},
				{
					fieldname: "medical_provider",
					label: __("Medical Provider"),
					fieldtype: "Data",
					reqd: 1,
				},
				{
					fieldname: "report_type",
					label: __("Report Type"),
					fieldtype: "Select",
					options: "Initial Assessment\nProgress Report\nSpecialist Report\nFinal Report",
					reqd: 1,
				},
				{
					fieldname: "diagnosis",
					label: __("Diagnosis"),
					fieldtype: "Small Text",
					reqd: 1,
				},
			],
			(values) => frm.call("add_medical_report", values).then(() => frm.reload_doc()),
			__("Add Medical Report"),
			__("Add")
		);
	});
}
