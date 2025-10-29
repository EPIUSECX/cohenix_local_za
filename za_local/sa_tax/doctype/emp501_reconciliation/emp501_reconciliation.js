// Copyright (c) 2025, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('EMP501 Reconciliation', {
    refresh: function(frm) {
        // Add custom buttons based on document status
        if (frm.doc.docstatus === 0) {
            // Draft state
            frm.add_custom_button(__('Fetch EMP201 Submissions'), function() {
                frm.call({
                    doc: frm.doc,
                    method: 'fetch_emp201_submissions',
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: __(`${r.message} EMP201 submissions fetched`),
                                indicator: 'green'
                            });
                            frm.refresh();
                        }
                    }
                });
            }, __('Actions'));
        }
        
        if (frm.doc.docstatus === 1) {
            // Submitted state
            if (frm.doc.status === "Submitted") { // Check against custom status
                frm.add_custom_button(__('Generate IRP5 Certificates'), function() {
                    frm.call({
                        doc: frm.doc,
                        method: 'generate_irp5_certificates',
                        callback: function(r) {
                            if (r.message) {
                                frappe.show_alert({
                                    message: __(`${r.message} IRP5 certificates processed`),
                                    indicator: 'green'
                                });
                                frm.refresh();
                            }
                        }
                    });
                }, __('Actions'));
                
                frm.add_custom_button(__('Submit to SARS'), function() {
                    frappe.confirm(
                        __('Are you sure you want to submit this EMP501 reconciliation to SARS?'),
                        function() {
                            frm.call({
                                doc: frm.doc,
                                method: 'submit_to_sars',
                                callback: function(r) {
                                    if (r.message && r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: __(r.message.message),
                                            indicator: 'green'
                                        });
                                        frm.refresh();
                                    }
                                }
                            });
                        }
                    );
                }).addClass('btn-primary');
            }
            
            // Add button to download CSV for SARS e-Filing
            frm.add_custom_button(__('Download CSV for e-Filing'), function() {
                frappe.call({
                    method: 'za_local.utils.emp501_utils.generate_emp501_csv',
                    args: {
                        emp501: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.file_url) {
                            window.open(r.message.file_url);
                        }
                    }
                });
            }, __('Actions'));
        }
    },
    
    tax_year: function(frm) {
        if (frm.doc.tax_year && frm.doc.reconciliation_period) {
            frm.trigger("get_dates");
        }
    },
    
    reconciliation_period: function(frm) {
        if (frm.doc.tax_year && frm.doc.reconciliation_period) {
            frm.trigger("get_dates");
        }
    },

    get_dates: function(frm) {
        frappe.call({
            method: "za_local.sa_tax.doctype.emp501_reconciliation.emp501_reconciliation.get_period_dates",
            args: {
                tax_year: frm.doc.tax_year,
                reconciliation_period: frm.doc.reconciliation_period
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("from_date", r.message.from_date);
                    frm.set_value("to_date", r.message.to_date);
                }
            }
        });
    },
    
    company: function(frm) {
        // Fetch reference numbers from company via a whitelisted server method
        if (frm.doc.company) {
            // Add a flag to prevent multiple triggers
            if (frm.company_set === frm.doc.company) {
                return;
            }
            frm.company_set = frm.doc.company;

            frappe.call({
                method: 'za_local.sa_tax.doctype.emp501_reconciliation.emp501_reconciliation.get_company_tax_details',
                args: {
                    company: frm.doc.company
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('paye_reference_number', r.message.tax_id);
                        frm.set_value('sdl_reference_number', r.message.custom_sdl_reference_number);
                        frm.set_value('uif_reference_number', r.message.custom_uif_reference_number);

                        if (!r.message.custom_sdl_reference_number && !frm.sdl_warning_shown) {
                            frappe.msgprint({
                                title: __('Missing SDL Number'),
                                indicator: 'orange',
                                message: __('The SDL Reference Number is missing for the selected company. Please update it in the Company form.')
                            });
                            frm.sdl_warning_shown = true;
                        }
                        if (!r.message.custom_uif_reference_number && !frm.uif_warning_shown) {
                            frappe.msgprint({
                                title: __('Missing UIF Number'),
                                indicator: 'orange',
                                message: __('The UIF Reference Number is missing for the selected company. Please update it in the Company form.')
                            });
                            frm.uif_warning_shown = true;
                        }
                    }
                }
            });
        }
    }
});
