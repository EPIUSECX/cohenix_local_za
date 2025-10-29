// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip", {
	refresh: function(frm) {
		// Status indicator
		set_status_indicator(frm);
		
		// Custom buttons
		add_custom_buttons(frm);
		
		// Auto-calculate on refresh
		if (!frm.is_new()) {
			frm.trigger("calculate_totals");
		}
	},
	
	from_date: function(frm) {
		validate_dates(frm);
	},
	
	to_date: function(frm) {
		validate_dates(frm);
	},
	
	calculate_totals: function(frm) {
		// Trigger recalculation of all totals
		calculate_all_totals(frm);
	}
});

// Child table triggers for auto-calculation
frappe.ui.form.on("Business Trip Allowance", {
	region: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.region) {
			// Fetch rates from region
			frappe.db.get_value("Business Trip Region", row.region, ["daily_allowance_rate", "incidental_allowance_rate"])
				.then(r => {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "daily_rate", r.message.daily_allowance_rate);
						frappe.model.set_value(cdt, cdn, "incidental_rate", r.message.incidental_allowance_rate);
						calculate_allowance_row_total(frm, cdt, cdn);
					}
				});
		}
	},
	
	daily_rate: function(frm, cdt, cdn) {
		calculate_allowance_row_total(frm, cdt, cdn);
	},
	
	incidental_rate: function(frm, cdt, cdn) {
		calculate_allowance_row_total(frm, cdt, cdn);
	},
	
	allowances_remove: function(frm) {
		frm.trigger("calculate_totals");
	}
});

frappe.ui.form.on("Business Trip Journey", {
	transport_mode: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		// Fetch mileage rate if private car
		if (row.transport_mode === "Car (Private)") {
			frappe.call({
				method: "za_local.sa_payroll.doctype.business_trip_settings.business_trip_settings.get_mileage_rate",
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "mileage_rate", r.message);
					}
				}
			});
		}
	},
	
	distance_km: function(frm, cdt, cdn) {
		calculate_mileage_claim(frm, cdt, cdn);
	},
	
	mileage_rate: function(frm, cdt, cdn) {
		calculate_mileage_claim(frm, cdt, cdn);
	},
	
	receipt_amount: function(frm) {
		frm.trigger("calculate_totals");
	},
	
	journeys_remove: function(frm) {
		frm.trigger("calculate_totals");
	}
});

frappe.ui.form.on("Business Trip Accommodation", {
	amount: function(frm) {
		frm.trigger("calculate_totals");
	},
	
	accommodations_remove: function(frm) {
		frm.trigger("calculate_totals");
	}
});

frappe.ui.form.on("Business Trip Other Expense", {
	amount: function(frm) {
		frm.trigger("calculate_totals");
	},
	
	other_expenses_remove: function(frm) {
		frm.trigger("calculate_totals");
	}
});

// Helper functions
function set_status_indicator(frm) {
	let indicator_map = {
		"Draft": "grey",
		"Submitted": "blue",
		"Approved": "green",
		"Expense Claim Created": "purple",
		"Cancelled": "red"
	};
	
	let color = indicator_map[frm.doc.status] || "grey";
	frm.set_indicator(__(frm.doc.status), color);
}

function add_custom_buttons(frm) {
	if (frm.doc.docstatus === 0 && frm.doc.from_date && frm.doc.to_date) {
		// Generate Allowances button
		frm.add_custom_button(__("Generate Allowances"), function() {
			frappe.call({
				method: "za_local.sa_payroll.doctype.business_trip.business_trip.generate_allowances_for_date_range",
				args: {
					business_trip_name: frm.doc.name
				},
				callback: function(r) {
					frm.reload_doc();
				}
			});
		});
	}
	
	if (frm.doc.docstatus === 1 && !frm.doc.expense_claim) {
		// Create Expense Claim button
		frm.add_custom_button(__("Create Expense Claim"), function() {
			frappe.call({
				method: "za_local.sa_payroll.doctype.business_trip.business_trip.create_expense_claim_from_trip",
				args: {
					business_trip_name: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frm.reload_doc();
						frappe.show_alert({
							message: __("Expense Claim {0} created", [r.message]),
							indicator: "green"
						});
					}
				}
			});
		}, __("Actions"));
	}
	
	if (frm.doc.expense_claim) {
		// View Expense Claim button
		frm.add_custom_button(__("View Expense Claim"), function() {
			frappe.set_route("Form", "Expense Claim", frm.doc.expense_claim);
		});
	}
}

function validate_dates(frm) {
	if (frm.doc.from_date && frm.doc.to_date) {
		if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
			frappe.msgprint(__("To Date cannot be before From Date"));
			frm.set_value("to_date", null);
		}
	}
}

function calculate_allowance_row_total(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total = flt(row.daily_rate) + flt(row.incidental_rate);
	frappe.model.set_value(cdt, cdn, "total", total);
	frm.trigger("calculate_totals");
}

function calculate_mileage_claim(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (row.transport_mode === "Car (Private)" && row.distance_km && row.mileage_rate) {
		let claim = flt(row.distance_km) * flt(row.mileage_rate);
		frappe.model.set_value(cdt, cdn, "mileage_claim", claim);
	}
	frm.trigger("calculate_totals");
}

function calculate_all_totals(frm) {
	// Calculate allowances
	let total_allowance = 0;
	let total_incidental = 0;
	
	(frm.doc.allowances || []).forEach(row => {
		total_allowance += flt(row.daily_rate);
		total_incidental += flt(row.incidental_rate);
	});
	
	frm.set_value("total_allowance", total_allowance);
	frm.set_value("total_incidental", total_incidental);
	
	// Calculate journeys
	let total_mileage = 0;
	let total_receipts = 0;
	
	(frm.doc.journeys || []).forEach(row => {
		if (row.transport_mode === "Car (Private)") {
			total_mileage += flt(row.mileage_claim);
		} else {
			total_receipts += flt(row.receipt_amount);
		}
	});
	
	frm.set_value("total_mileage_claim", total_mileage);
	frm.set_value("total_receipt_claims", total_receipts);
	
	// Calculate accommodation
	let total_accommodation = 0;
	(frm.doc.accommodations || []).forEach(row => {
		total_accommodation += flt(row.amount);
	});
	frm.set_value("total_accommodation", total_accommodation);
	
	// Calculate other expenses
	let total_other = 0;
	(frm.doc.other_expenses || []).forEach(row => {
		total_other += flt(row.amount);
	});
	frm.set_value("total_other_expenses", total_other);
	
	// Calculate grand total
	let grand_total = total_allowance + total_incidental + total_mileage + total_receipts + total_accommodation + total_other;
	frm.set_value("grand_total", grand_total);
}

