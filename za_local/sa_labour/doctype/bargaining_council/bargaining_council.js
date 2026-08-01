frappe.ui.form.on("Bargaining Council", {
	refresh(frm) {
		if (!frappe.user.has_role("HR Manager") && !frappe.user.has_role("System Manager")) {
			return;
		}

		frm.add_custom_button(__("Import Common Councils"), () => {
			frappe.call({
				method: "za_local.sa_labour.doctype.bargaining_council.bargaining_council.import_common_councils",
			}).then((response) => {
				const stats = response.message || {};
				frappe.msgprint(
					__("Created {0}, updated {1}, skipped {2}, errors {3}.", [
						stats.created || 0,
						stats.updated || 0,
						stats.skipped || 0,
						stats.errors || 0,
					])
				);
			});
		});
	},
});
