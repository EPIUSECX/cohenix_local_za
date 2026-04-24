frappe.ui.form.on("South Africa VAT Settings", {
	onload(frm) {
		ensure_default_vat_rates(frm);
		update_vat_registration_number(frm);
	},
	refresh(frm) {
		ensure_default_vat_rates(frm);
		update_vat_registration_number(frm);

		frm.add_custom_button(__("Sync VAT Accounts"), function () {
			frm.call({
				method: "sync_vat_accounts",
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Syncing tracked VAT tax accounts for this company..."),
				callback() {
					frm.reload_doc();
				},
			});
		}, __("South Africa"));

		frm.add_custom_button(__("Bootstrap Company VAT Setup"), function () {
			frm.call({
				method: "bootstrap_defaults",
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Creating recommended VAT templates and syncing tax accounts..."),
				callback() {
					frm.reload_doc();
				},
			});
		}, __("South Africa"));
	},
	company(frm) {
		update_vat_registration_number(frm);
	},
	default_vat_report_company(frm) {
		update_vat_registration_number(frm);
	},
	enable_zero_rated_items(frm) {
		ensure_default_vat_rates(frm);
	},
	enable_exempt_items(frm) {
		ensure_default_vat_rates(frm);
	},
	standard_vat_rate(frm) {
		ensure_default_vat_rates(frm);
	},
});

function update_vat_registration_number(frm) {
	const company = frm.doc.default_vat_report_company || frm.doc.company;
	if (!company) {
		frm.set_value("vat_registration_number", "");
		return;
	}

	frappe.db.get_value("Company", company, "za_vat_number", function (r) {
		frm.set_value("vat_registration_number", (r && r.za_vat_number) || "");
	});
}

function ensure_default_vat_rates(frm) {
	const rows = (frm.doc.vat_rates || []).filter((row) =>
		Boolean((row.rate_name || "").trim() || row.rate || row.is_standard_rate || row.is_zero_rated || row.is_exempt),
	);

	if (rows.length !== (frm.doc.vat_rates || []).length) {
		frm.doc.vat_rates = rows;
	}

	if (!frm.doc.standard_vat_rate) {
		frm.doc.standard_vat_rate = 15;
	}

	const existing = new Set(rows.map((row) => (row.rate_name || "").trim().toLowerCase()));
	const additions = [];

	if (!existing.has("standard rate")) {
		additions.push({
			rate_name: "Standard Rate",
			rate: frm.doc.standard_vat_rate || 15,
			is_standard_rate: 1,
			description: __("Standard VAT rate for South Africa"),
		});
	}

	if (cint(frm.doc.enable_zero_rated_items ?? 1) && !existing.has("zero rate")) {
		additions.push({
			rate_name: "Zero Rate",
			rate: 0,
			is_zero_rated: 1,
			description: __("Zero-rated items (0% VAT)"),
		});
	}

	if (cint(frm.doc.enable_exempt_items ?? 1) && !existing.has("exempt")) {
		additions.push({
			rate_name: "Exempt",
			rate: 0,
			is_exempt: 1,
			description: __("VAT exempt items"),
		});
	}

	if (!additions.length && rows.length === (frm.doc.vat_rates || []).length) {
		return;
	}

	for (const row of additions) {
		frm.add_child("vat_rates", row);
	}

	for (const row of frm.doc.vat_rates || []) {
		if ((row.rate_name || "").trim().toLowerCase() === "standard rate") {
			row.rate = frm.doc.standard_vat_rate || 15;
			row.is_standard_rate = 1;
		}
	}

	frm.refresh_field("vat_rates");
}
