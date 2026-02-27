frappe.ui.form.on('VAT201 Return', {
    onload: function(frm) {
        update_submission_period(frm);
    },

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

        update_submission_period(frm);
    },
    
    company: function(frm) {
        // When company changes, fetch VAT registration number
        if (frm.doc.company) {
            frappe.db.get_value('Company', frm.doc.company, 'za_vat_number', function(r) {
                if (r && r.za_vat_number) {
                    frm.set_value('vat_registration_number', r.za_vat_number);
                }
            });
        }
    },

    from_date: function(frm) {
        update_submission_period(frm);
    },

    to_date: function(frm) {
        update_submission_period(frm);
    },
    
    standard_rated_supplies: function(frm) {
        // Calculate standard rated output tax
        frappe.db.get_single_value('South Africa VAT Settings', 'standard_vat_rate')
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

        if (!frm.doc.from_date || !frm.doc.to_date) {
            frappe.throw(__('From Date and To Date are required'));
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

const update_submission_period = (frm) => {
    if (frm.doc.from_date && frm.doc.to_date) {
        const from_label = frappe.datetime.str_to_user(frm.doc.from_date);
        const to_label = frappe.datetime.str_to_user(frm.doc.to_date);
        frm.set_value('submission_period', `${from_label} to ${to_label}`);
    } else {
        frm.set_value('submission_period', null);
    }
};
