frappe.ui.form.on("Business Trip Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Show Effective Mileage Rate"), () => {
			frappe.call({
				method: "za_local.sa_labour.doctype.business_trip_settings.business_trip_settings.get_mileage_rate",
				args: { date_value: frappe.datetime.get_today() },
			}).then((response) => {
				frappe.msgprint({
					title: __("Effective Mileage Rate"),
					message: __("The effective reimbursement rate is R{0} per kilometre.", [response.message]),
					indicator: "blue",
				});
			});
		});
	},
});
