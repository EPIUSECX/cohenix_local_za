// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip Region", {
	refresh: function(frm) {
		// Show indicator for active/inactive
		if (frm.doc.is_active) {
			frm.set_indicator(__("Active"), "green");
		} else {
			frm.set_indicator(__("Inactive"), "grey");
		}
		
		// Add button to view all regions
		if (!frm.is_new()) {
			frm.add_custom_button(__("View All Regions"), function() {
				frappe.set_route("List", "Business Trip Region");
			});
		}
	},
	
	country: function(frm) {
		// Suggest default rates based on country
		if (frm.doc.country === "South Africa" && !frm.doc.daily_allowance_rate) {
			// Suggest typical SA city rates
			frm.set_value("daily_allowance_rate", 450);
			frm.set_value("incidental_allowance_rate", 50);
			frappe.show_alert({
				message: __("Default rates set for South African region"),
				indicator: "blue"
			});
		} else if (frm.doc.country && frm.doc.country !== "South Africa" && !frm.doc.daily_allowance_rate) {
			// Suggest international rates
			frm.set_value("daily_allowance_rate", 1000);
			frm.set_value("incidental_allowance_rate", 100);
			frappe.show_alert({
				message: __("Default rates set for international region"),
				indicator: "blue"
			});
		}
	}
});

