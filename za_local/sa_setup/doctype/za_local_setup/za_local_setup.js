frappe.ui.form.on("ZA Local Setup", {
	refresh(frm) {
		frm.trigger("set_hrms_option_visibility");

		if (frm.doc.setup_completed_on) {
			frm.set_intro(
				__(
					"This setup has already been applied. Adjust the options if needed, then use 'Apply Selected Configuration' to run it again."
				),
				"blue"
			);
		} else {
			frm.set_intro(
				__(
					"Choose the South African setup items you want to load, save your selections, then click 'Apply Selected Configuration'."
				),
				"orange"
			);
		}

		if (frm.doc.docstatus !== 0) {
			return;
		}

		frm.add_custom_button(__("Apply Selected Configuration"), () => {
			if (!frm.doc.company) {
				frappe.msgprint({
					title: __("Missing Company"),
					message: __("Please select a company before running ZA Local Setup."),
					indicator: "orange",
				});
				return;
			}

			const runSetup = () => {
				frm.call({
					doc: frm.doc,
					method: "start_setup",
					freeze: true,
					freeze_message: __("Applying South African localisation setup..."),
					callback: () => {
						frm.reload_doc();
					},
				});
			};

			if (frm.is_dirty()) {
				frm.save().then(() => runSetup());
			} else {
				runSetup();
			}
		}).addClass("btn-primary");
	},

	before_save(frm) {
		if (frm.__za_hrms_installed === false) {
			frm.trigger("clear_hrms_options");
		}
	},

	set_hrms_option_visibility(frm) {
		frappe.call({
			method: "za_local.utils.hrms_detection.is_hrms_installed",
			callback: (r) => {
				const has_hrms = Boolean(r.message);
				frm.__za_hrms_installed = has_hrms;

				const fields = [
					"load_salary_components",
					"load_earnings_components",
					"load_tax_slabs",
					"load_tax_rebates",
					"load_medical_credits",
				];
				const layout_fields = ["section_break_4", "column_break_7"];

				[...fields, ...layout_fields].forEach((fieldname) => {
					frm.set_df_property(fieldname, "hidden", !has_hrms);
				});

				if (!has_hrms) {
					frm.trigger("clear_hrms_options");
				}
			},
		});
	},

	clear_hrms_options(frm) {
		[
			"load_salary_components",
			"load_earnings_components",
			"load_tax_slabs",
			"load_tax_rebates",
			"load_medical_credits",
		].forEach((fieldname) => {
			if (frm.doc[fieldname]) {
				frm.set_value(fieldname, 0);
			}
		});
	},
});
