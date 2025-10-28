/**
 * South African Employee Form Script
 * 
 * Handles SA-specific field queries and validations
 */

frappe.ui.form.on("Employee", {
	onload: function(frm) {
		// Set query for payroll payable bank account
		frm.set_query('za_payroll_payable_bank_account', function(doc) {
			return {
				filters: {
					"is_company_account": 1,
					"account": ["!=", null]
				}
			};
		});
	},
	
	za_id_number: function(frm) {
		// Validate SA ID number format
		if (frm.doc.za_id_number && frm.doc.za_id_number.length !== 13) {
			frappe.msgprint(__('South African ID number must be 13 digits'));
		}
	}
});