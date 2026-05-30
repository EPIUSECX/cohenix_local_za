frappe.ui.form.on("South Africa VAT Settings", {
	onload(frm) {
		ensure_default_vat_rates(frm);
		sync_company_scope(frm);
		update_vat_registration_number(frm);
		set_default_filing_frequency(frm);
		set_erpnext_vat_queries(frm);
	},
	refresh(frm) {
		ensure_default_vat_rates(frm);
		sync_company_scope(frm);
		update_vat_registration_number(frm);
		set_erpnext_vat_queries(frm);

		frm.add_custom_button(__("Sync VAT Accounts"), function () {
			run_vat_settings_action(frm, {
				method: "sync_vat_accounts",
				freeze: true,
				freeze_message: __("Syncing tracked VAT tax accounts for this company..."),
				fallback_title: __("VAT Accounts Synced"),
			});
		}, __("South Africa"));

		frm.add_custom_button(__("Apply Recommended VAT Setup"), function () {
			run_vat_settings_action(frm, {
				method: "bootstrap_defaults",
				freeze: true,
				freeze_message: __("Applying recommended VAT templates and VAT account tracking..."),
				fallback_title: __("Recommended VAT Setup Applied"),
			});
		}, __("South Africa"));
	},
	company(frm) {
		sync_company_scope(frm);
		update_vat_registration_number(frm, true);
		set_erpnext_vat_queries(frm);
	},
	default_vat_report_company(frm) {
		sync_company_scope(frm);
	},
	vat_vendor_type(frm) {
		set_default_filing_frequency(frm);
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

function run_vat_settings_action(frm, opts) {
	const run = () => {
		frm.call({
			method: opts.method,
			doc: frm.doc,
			freeze: opts.freeze,
			freeze_message: opts.freeze_message,
			callback(r) {
				const result = r && r.message;
				frm.reload_doc().then(() => show_za_feedback(result, opts.fallback_title));
			},
		});
	};

	if (frm.is_dirty()) {
		frm.save().then(run);
		return;
	}
	run();
}

function show_za_feedback(result, fallback_title) {
	if (window.za_local && window.za_local.show_action_feedback) {
		window.za_local.show_action_feedback(result, fallback_title);
		return;
	}

	if (result) {
		frappe.msgprint({
			title: result.title || fallback_title,
			message: result.message || __("The action completed successfully."),
			indicator: result.indicator || "green",
		});
	}
}

function set_erpnext_vat_queries(frm) {
	frm.set_query("company", function () {
		return {
			filters: {
				country: "South Africa",
			},
		};
	});

	const accountFilters = function () {
		return {
			filters: {
				company: frm.doc.company,
				account_type: "Tax",
				is_group: 0,
			},
		};
	};

	frm.set_query("account", "vat_accounts", accountFilters);
	frm.set_query("output_vat_account", accountFilters);
	frm.set_query("input_vat_account", accountFilters);
}

function update_vat_registration_number(frm, force) {
	const company = frm.doc.company;
	if (!company) {
		frm.set_value("vat_registration_number", "");
		return;
	}

	if (!force && frm.doc.vat_registration_number) {
		return;
	}

	frappe.db.get_value("Company", company, ["za_vat_number", "tax_id"], function (r) {
		frm.set_value("vat_registration_number", (r && (r.za_vat_number || r.tax_id)) || "");
	});
}

function sync_company_scope(frm) {
	if (frm.doc.company && frm.doc.default_vat_report_company !== frm.doc.company) {
		frm.set_value("default_vat_report_company", frm.doc.company);
	}
}

function set_default_filing_frequency(frm) {
	if (!frm.doc.vat_vendor_type || frm.doc.vat_filing_frequency) {
		return;
	}

	frappe.db.get_value("VAT Vendor Type", frm.doc.vat_vendor_type, "filing_frequency", (r) => {
		if (r && r.filing_frequency && !frm.doc.vat_filing_frequency) {
			frm.set_value("vat_filing_frequency", r.filing_frequency);
		}
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
