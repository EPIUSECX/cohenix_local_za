frappe.ui.form.on('COIDA Annual Return', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Fetch Employee Data'), function() {
                frm.call({
                    doc: frm.doc,
                    method: 'fetch_employee_data',
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Employee data fetched successfully'),
                                indicator: 'green'
                            });
                            frm.refresh();
                        }
                    }
                });
            });
        }
        
        // Add print button for submitted documents
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print COIDA Return'), function() {
                frappe.set_route('print', frm.doctype, frm.docname);
            });
        }
    },
    
    fiscal_year: function(frm) {
        // Set from_date and to_date based on fiscal year
        if (frm.doc.fiscal_year) {
            frappe.db.get_doc('Fiscal Year', frm.doc.fiscal_year)
                .then(fiscal_year => {
                    frm.set_value('from_date', fiscal_year.year_start_date);
                    frm.set_value('to_date', fiscal_year.year_end_date);
                });
        }
    },
    
    company: function(frm) {
        // Get industry class from COIDA Settings
        if (frm.doc.company) {
            frappe.db.get_single_value('COIDA Settings', 'registration_number')
                .then(registration_number => {
                    if (registration_number) {
                        frappe.db.get_list('COIDA Industry Rate', {
                            fields: ['industry_class', 'assessment_rate'],
                            parent: 'COIDA Settings',
                            limit: 1
                        }).then(rates => {
                            if (rates && rates.length > 0) {
                                frm.set_value('industry_class', rates[0].industry_class);
                                frm.set_value('assessment_rate', rates[0].assessment_rate);
                            }
                        });
                    }
                });
        }
    },
    
    total_annual_earnings: function(frm) {
        // Calculate assessment fee
        frm.trigger('calculate_assessment_fee');
    },
    
    assessment_rate: function(frm) {
        // Calculate assessment fee
        frm.trigger('calculate_assessment_fee');
    },
    
    calculate_assessment_fee: function(frm) {
        if (frm.doc.total_annual_earnings && frm.doc.assessment_rate) {
            const assessment_fee = flt(frm.doc.total_annual_earnings) * flt(frm.doc.assessment_rate) / 100;
            frm.set_value('assessment_fee', assessment_fee);
        }
    }
});
