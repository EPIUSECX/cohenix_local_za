// Copyright (c) 2025, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('VAT201 Return', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1 && frm.doc.status === "Prepared") {
            frm.add_custom_button(__('Submit to SARS'), function() {
                frappe.confirm(
                    __('Are you sure you want to submit this VAT201 Return to SARS e-Filing?'),
                    function() {
                        // Yes - Submit to SARS
                        frm.call({
                            method: 'submit_to_sars',
                            doc: frm.doc,
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    },
                    function() {
                        // No - Do nothing
                    }
                );
            }).addClass('btn-primary');
        }
        
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Get VAT Transactions'), function() {
                frappe.confirm(
                    __('This will fetch all VAT transactions for the period. Continue?'),
                    function() {
                        // Yes - Get transactions
                        frm.call({
                            method: 'get_vat_transactions',
                            doc: frm.doc,
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    },
                    function() {
                        // No - Do nothing
                    }
                );
            });
        }
        
        // Add dashboard indicators
        if (frm.doc.status) {
            let indicator = "gray";
            if (frm.doc.status === "Draft") indicator = "gray";
            else if (frm.doc.status === "Prepared") indicator = "blue";
            else if (frm.doc.status === "Submitted") indicator = "orange";
            else if (frm.doc.status === "Accepted") indicator = "green";
            else if (frm.doc.status === "Rejected") indicator = "red";
            
            frm.page.set_indicator(__(`Status: ${frm.doc.status}`), indicator);
        }
        
        // Add VAT payable/refundable indicator
        if (frm.doc.vat_payable > 0) {
            frm.page.add_indicator(__(`VAT Payable: ${format_currency(frm.doc.vat_payable)}`), "red");
        } else if (frm.doc.vat_refundable > 0) {
            frm.page.add_indicator(__(`VAT Refundable: ${format_currency(frm.doc.vat_refundable)}`), "green");
        }
    },
    
    company: function(frm) {
        // When company changes, fetch VAT registration number
        if (frm.doc.company) {
            frappe.db.get_value('Company', frm.doc.company, 'custom_vat_number', function(r) {
                if (r && r.custom_vat_number) {
                    frm.set_value('vat_registration_number', r.custom_vat_number);
                } else {
                    // If company doesn't have VAT number, try to get from VAT settings
                    frappe.db.get_single_value('South African VAT Settings', 'vat_registration_number')
                        .then(vat_reg_number => {
                            if (vat_reg_number) {
                                frm.set_value('vat_registration_number', vat_reg_number);
                            }
                        });
                }
            });
        }
    },
    
    standard_rated_supplies: function(frm) {
        // Calculate standard rated output tax
        frappe.db.get_single_value('South African VAT Settings', 'standard_vat_rate')
            .then(standard_rate => {
                if (standard_rate) {
                    const rate = flt(standard_rate) / 100;
                    const output_tax = flt(frm.doc.standard_rated_supplies) * rate;
                    frm.set_value('standard_rated_output', output_tax);
                }
            });
    },
    
    setup: function(frm) {
        // Set query filters for company
        frm.set_query('company', function() {
            return {
                filters: {
                    'country': 'South Africa'
                }
            };
        });
    },
    
    validate: function(frm) {
        // Additional client-side validations
        if (!frm.doc.vat_registration_number) {
            frappe.throw(__('VAT Registration Number is required'));
        }
        
        // Ensure total supplies match the sum of components
        const total_supplies = flt(frm.doc.standard_rated_supplies) + 
                              flt(frm.doc.zero_rated_supplies) + 
                              flt(frm.doc.exempt_supplies);
                              
        if (Math.abs(total_supplies - frm.doc.total_supplies) > 0.01) {
            frappe.throw(__('Total Supplies does not match the sum of Standard Rated, Zero Rated, and Exempt Supplies'));
        }
    }
});
