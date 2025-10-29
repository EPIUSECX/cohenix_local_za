// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip Settings", {
	refresh: function(frm) {
		// Add button to view current SARS rates
		frm.add_custom_button(__("SARS Rates Reference"), function() {
			frappe.msgprint({
				title: __("SARS Business Travel Allowance Rates (2024)"),
				indicator: "blue",
				message: `
					<h4>Mileage Allowance</h4>
					<p><strong>Standard Rate:</strong> R4.25 per kilometer</p>
					<p><em>For business use of private vehicle</em></p>
					
					<h4>Daily Meal Allowance</h4>
					<p><strong>Local Travel:</strong> R300 - R500 per day</p>
					<p><strong>International:</strong> Varies by country (R800 - R1,300)</p>
					
					<h4>Incidental Allowance</h4>
					<p><strong>Standard:</strong> R50 - R150 per day</p>
					
					<p style="margin-top: 20px; font-size: 12px; color: #888;">
						<em>Note: These are standard industry rates. Check current SARS guidelines for official rates.</em>
					</p>
				`
			});
		});
		
		// Show warning if mileage rate differs significantly from SARS rate
		if (frm.doc.mileage_allowance_rate && 
		    (frm.doc.mileage_allowance_rate < 3.50 || frm.doc.mileage_allowance_rate > 5.00)) {
			frm.dashboard.set_headline_alert(
				`Mileage rate (R${frm.doc.mileage_allowance_rate}) differs from SARS standard rate (R4.25/km)`,
				"orange"
			);
		}
	},
	
	mileage_allowance_rate: function(frm) {
		// Validate against SARS rate
		if (frm.doc.mileage_allowance_rate) {
			const sars_rate = 4.25;
			const difference = Math.abs(frm.doc.mileage_allowance_rate - sars_rate);
			
			if (difference > 0.50) {
				frappe.msgprint({
					title: __("Rate Variance Alert"),
					indicator: "orange",
					message: `Your mileage rate (R${frm.doc.mileage_allowance_rate}) differs by R${difference.toFixed(2)} from the SARS standard rate of R${sars_rate}.`
				});
			}
		}
	}
});

