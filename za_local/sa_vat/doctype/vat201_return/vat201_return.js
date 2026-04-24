frappe.ui.form.on("VAT201 Return", {
	onload(frm) {
		update_submission_period(frm);
	},

	refresh(frm) {
		update_submission_period(frm);
		set_form_intro(frm);

		if (frm.doc.docstatus === 1 && frm.doc.status === "Prepared") {
			frm.set_intro(
				__(
					"Direct SARS electronic submission is not supported in this release. Review the return, export your working papers, and file manually through SARS eFiling.",
				),
				"orange",
			);
		}

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get VAT Transactions"), function () {
				if (frm.is_dirty()) {
					frappe.throw(__("Please save before fetching VAT transactions."));
				}

				frm.call({
					method: "get_vat_transactions",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Fetching VAT transactions and classifying them for VAT201..."),
					callback() {
						frm.reload_doc();
					},
				});
			});
		}

		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Open Linked Transactions"), function () {
				route_to_report(frm.doc.name);
			}, __("Exports"));

			frm.add_custom_button(__("Export Summary CSV"), function () {
				frm.call({
					method: "get_summary_rows",
					doc: frm.doc,
					callback(r) {
						if (!r.message) return;
						const rows = [["Box", "Label", "Amount"]].concat(
							r.message.map((row) => [row.box, row.label, row.amount ?? 0]),
						);
						download_csv(`${frm.doc.name}-vat201-summary.csv`, rows);
					},
				});
			}, __("Exports"));

			frm.add_custom_button(__("Export Linked Transactions CSV"), function () {
				frm.call({
					method: "get_linked_transaction_rows",
					doc: frm.doc,
					callback(r) {
						if (!r.message) return;
						const rows = [[
							"GL Entry",
							"Voucher Type",
							"Voucher No",
							"Posting Date",
							"Template",
							"Tax Debit",
							"Tax Credit",
							"Tax Amount",
							"Incl Tax Amount",
							"Classification",
							"Cancelled",
						]].concat(
							r.message.map((row) => [
								row.gl_entry || "",
								row.voucher_type || "",
								row.voucher_no || "",
								row.posting_date || "",
								row.taxes_and_charges || "",
								row.tax_account_debit || 0,
								row.tax_account_credit || 0,
								row.tax_amount || 0,
								row.incl_tax_amount || 0,
								row.classification || "",
								row.is_cancelled ? "Yes" : "No",
							]),
						);
						download_csv(`${frm.doc.name}-vat201-linked-transactions.csv`, rows);
					},
				});
			}, __("Exports"));
		}

		if (frm.doc.status) {
			let indicator = "gray";
			if (frm.doc.status === "Prepared") indicator = "blue";
			else if (frm.doc.status === "Submitted") indicator = "orange";
			else if (frm.doc.status === "Accepted") indicator = "green";
			else if (frm.doc.status === "Rejected") indicator = "red";
			frm.page.set_indicator(__(`Status: ${frm.doc.status}`), indicator);
		}
	},

	company(frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "za_vat_number", function (r) {
				if (r && r.za_vat_number) {
					frm.set_value("vat_registration_number", r.za_vat_number);
				}
			});
		}
	},

	from_date(frm) {
		update_submission_period(frm);
	},

	to_date(frm) {
		update_submission_period(frm);
	},
});

function set_form_intro(frm) {
	const rows = frm.doc.transactions || [];
	const unclassified = rows.filter((entry) => !entry.classification && !entry.is_cancelled);
	if (unclassified.length > 0) {
		frm.set_intro(__("{0} linked transactions still need classification.", [unclassified.length]), "orange");
	} else if (rows.length > 0) {
		frm.set_intro(__("Linked VAT transactions are ready for review and export."), "green");
	}
}

function route_to_report(docname) {
	frappe.route_options = { vat_return: docname };
	frappe.set_route("query-report", "VAT 201 Linked Transactions");
}

function update_submission_period(frm) {
	if (frm.doc.from_date && frm.doc.to_date) {
		const fromLabel = frappe.datetime.str_to_user(frm.doc.from_date);
		const toLabel = frappe.datetime.str_to_user(frm.doc.to_date);
		frm.set_value("submission_period", `${fromLabel} to ${toLabel}`);
	} else {
		frm.set_value("submission_period", null);
	}
}

function download_csv(filename, rows) {
	const csv = rows
		.map((row) =>
			row
				.map((value) => `"${String(value ?? "").replace(/"/g, '""')}"`)
				.join(","),
		)
		.join("\n");
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}
