frappe.ui.form.on("ZA Local Setup", {
	refresh(frm) {
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
});
