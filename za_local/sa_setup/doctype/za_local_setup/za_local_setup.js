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
			frm.trigger("confirm_and_run_setup");
		}).addClass("btn-primary");

		frm.trigger("add_publish_guide_button");
	},

	add_publish_guide_button(frm) {
		// Only offer the action when the Frappe Wiki app is installed on this site.
		frappe.call({
			method: "za_local.practitioner_guide.stage.is_wiki_available",
			callback: (r) => {
				if (!r || !r.message) {
					return;
				}
				frm.add_custom_button(
					__("Publish Practitioner Guide"),
					() => {
						frappe.call({
							method: "za_local.practitioner_guide.stage.publish_practitioner_guide",
							freeze: true,
							freeze_message: __("Publishing the SA Practitioner Guide to Wiki..."),
							callback: (res) => {
								const result = res && res.message;
								if (window.za_local && window.za_local.show_action_feedback) {
									window.za_local.show_action_feedback(
										result,
										__("Practitioner Guide Published")
									);
								} else if (result) {
									frappe.msgprint({
										title: result.title || __("Practitioner Guide Published"),
										message: result.message,
										indicator: result.indicator || "green",
									});
								}
							},
						});
					},
					__("Documentation")
				);
			},
		});
	},

	confirm_and_run_setup(frm) {
		const option_fields = [
			"load_salary_components",
			"load_earnings_components",
			"load_tax_slabs",
			"load_tax_rebates",
			"load_medical_credits",
			"load_eti_slabs",
			"load_sars_payroll_codes",
			"load_salary_component_classifications",
			"load_retirement_funds",
			"load_business_trip_regions",
			"load_seta_list",
			"load_bargaining_councils",
			"load_vat_vendor_types",
			"load_chart_of_accounts",
		];
		const selected = option_fields
			.filter((f) => frm.doc[f])
			.map((f) => (frm.fields_dict[f] ? frm.fields_dict[f].df.label : f));

		const list_html = selected.length
			? "<ul>" + selected.map((l) => `<li>${frappe.utils.escape_html(l)}</li>`).join("") + "</ul>"
			: `<p>${__("No optional data sets selected — only the required VAT fields, print formats and navigation will be applied.")}</p>`;

		const msg =
			`<p>${__("The following will be applied for company {0}:", [frappe.utils.escape_html(frm.doc.company)])}</p>` +
			list_html +
			`<p class="text-muted">${__("This runs in the background — you can keep working, and progress is shown here.")}</p>`;

		frappe.confirm(msg, () => {
			if (frm.is_dirty()) {
				frm.save().then(() => frm.trigger("queue_setup"));
			} else {
				frm.trigger("queue_setup");
			}
		});
	},

	queue_setup(frm) {
		// Re-register cleanly so repeated runs don't stack handlers.
		frappe.realtime.off("za_local_setup_progress");
		frappe.realtime.off("za_local_setup_done");

		frappe.realtime.on("za_local_setup_progress", (data) => {
			if (!data) return;
			frappe.show_progress(
				__("Applying ZA Local Setup"),
				data.progress || 0,
				100,
				data.message || __("Working...")
			);
		});

		frappe.realtime.on("za_local_setup_done", (result) => {
			frappe.hide_progress();
			frappe.realtime.off("za_local_setup_progress");
			frappe.realtime.off("za_local_setup_done");
			frm.reload_doc().then(() => {
				if (window.za_local && window.za_local.show_action_feedback) {
					window.za_local.show_action_feedback(result, __("ZA Local Setup Complete"));
				} else if (result) {
					frappe.msgprint({
						title: result.title || __("ZA Local Setup Complete"),
						message: result.message,
						indicator: result.indicator || "green",
					});
				}
			});
		});

		frm.call({
			doc: frm.doc,
			method: "start_setup",
			freeze: true,
			freeze_message: __("Queuing South African localisation setup..."),
			callback: (r) => {
				const result = r && r.message;
				if (result && result.message) {
					frappe.show_alert({ message: result.message, indicator: result.indicator || "blue" }, 7);
				}
				frappe.show_progress(__("Applying ZA Local Setup"), 1, 100, __("Queued..."));
			},
		});
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
					"load_eti_slabs",
					"load_sars_payroll_codes",
					"load_salary_component_classifications",
					"load_retirement_funds",
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
			"load_eti_slabs",
			"load_sars_payroll_codes",
			"load_salary_component_classifications",
			"load_retirement_funds",
		].forEach((fieldname) => {
			if (frm.doc[fieldname]) {
				frm.set_value(fieldname, 0);
			}
		});
	},
});
