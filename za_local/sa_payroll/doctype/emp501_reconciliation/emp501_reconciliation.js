frappe.ui.form.on('EMP501 Reconciliation', {
    refresh: function(frm) {
        // Step-by-step workflow with standalone buttons (not in dropdown)
        if (frm.doc.docstatus === 0) {
            // STEP 1: Fetch EMP201 Submissions
            // Show this button if company and tax_year are set (dates will be auto-populated or validated)
            const hasRequiredFields = frm.doc.company && frm.doc.tax_year;
            const hasEMP201Entries = frm.doc.emp201_submissions && frm.doc.emp201_submissions.length > 0;
            
            if (hasRequiredFields && !hasEMP201Entries) {
                frm.add_custom_button(__('Step 1: Fetch Monthly EMP201 Declarations'), function() {
                    // Validate required fields
                    if (!frm.doc.company || !frm.doc.tax_year || !frm.doc.from_date || !frm.doc.to_date) {
                        frappe.msgprint({
                            title: __('Missing Required Fields'),
                            message: __('Please ensure Company, Tax Year, From Date, and To Date are set.'),
                            indicator: 'orange'
                        });
                        return;
                    }
                    
                    // Ensure document is saved
                    if (frm.is_new()) {
                        frappe.confirm(
                            __('The document must be saved first. Save now?'),
                            function() {
                                frm.save().then(function() {
                                    fetchEMP201Submissions(frm);
                                });
                            }
                        );
                    } else {
                        fetchEMP201Submissions(frm);
                    }
                }).addClass('btn-primary');
            }
            
            // STEP 2: Generate IRP5 Certificates
            const hasIRP5Certificates = frm.doc.irp5_certificates && frm.doc.irp5_certificates.length > 0;
            
            if (hasEMP201Entries && !hasIRP5Certificates) {
                frm.add_custom_button(__('Step 2: Generate IRP5 Certificates'), function() {
                    // Validate required fields
                    if (!frm.doc.company || !frm.doc.tax_year || !frm.doc.from_date || !frm.doc.to_date) {
                        frappe.msgprint({
                            title: __('Missing Required Fields'),
                            message: __('Please ensure Company, Tax Year, From Date, and To Date are set.'),
                            indicator: 'orange'
                        });
                        return;
                    }
                    
                    // Ensure document is saved
                    if (frm.is_new()) {
                        frappe.confirm(
                            __('The document must be saved before generating IRP5 certificates. Save now?'),
                            function() {
                                frm.save().then(function() {
                                    generateIRP5Certificates(frm);
                                });
                            }
                        );
                    } else {
                        generateIRP5Certificates(frm);
                    }
                }).addClass('btn-primary');
            }
            
            if (hasRequiredFields && !hasEMP201Entries) {
                frm.dashboard.add_indicator(__('EMP201 coverage must be fetched before IRP5 generation'), 'orange');
                frm.set_intro(__('Compliance flow: submitted salary slips -> monthly EMP201 -> IRP5 certificates -> EMP501 submission.'), 'orange');
            }
            
            // STEP 3: Ready to Submit indicator
            if (hasEMP201Entries && hasIRP5Certificates) {
                frm.dashboard.add_indicator(__('Ready for EMP501 Submission'), 'green');
            }
        }
        
        if (frm.doc.docstatus === 1) {
            frm.set_intro(__('Direct SARS electronic submission is not supported in this release. Use the filing export below and complete submission manually in SARS eFiling.'), 'orange');
            
            // Download CSV for SARS e-Filing (available after submission)
            frm.add_custom_button(__('Download Filing CSV'), function() {
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
            });
        }
        
        // Helper function to fetch EMP201 submissions
        function fetchEMP201Submissions(frm) {
            frm.call({
                doc: frm.doc,
                method: 'fetch_emp201_submissions',
                freeze: true,
                freeze_message: __('Fetching EMP201 Submissions...'),
                callback: function(r) {
                    if (r.message) {
                        let count = r.message.count || 0;
                        let message = r.message.message || __('EMP201 submissions fetched');
                        const missingPeriods = r.message.missing_periods || [];
                        
                        if (count > 0 && missingPeriods.length === 0) {
                            frappe.show_alert({
                                message: __(`Step 1 Complete: ${message} You can now proceed to Step 2.`),
                                indicator: 'green'
                            }, 5);
                        } else {
                            frappe.msgprint({
                                title: __('Incomplete EMP201 Coverage'),
                                message: __('Step 1 is not complete yet. Missing submitted EMP201 declarations for: {0}').replace('{0}', missingPeriods.join(', ') || __('the selected period')),
                                indicator: 'orange'
                            });
                        }
                        frm.refresh();
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to fetch EMP201 submissions. Please check the error log.'),
                        indicator: 'red'
                    });
                }
            });
        }
        
        // Helper function to generate IRP5 certificates
        function generateIRP5Certificates(frm) {
            frappe.confirm(
                __('This will generate IRP5 certificates for all employees with salary slips in the selected period. Existing certificates will be updated. Continue?'),
                function() {
                    frm.call({
                        doc: frm.doc,
                        method: 'generate_irp5_certificates',
                        freeze: true,
                        freeze_message: __('Generating IRP5 Certificates... This may take a few moments.'),
                        callback: function(r) {
                            if (r.message) {
                                let msg = r.message.message || __('IRP5 certificates generated');
                                let details = [];
                                
                                if (r.message.created !== undefined) {
                                    details.push(__('Created: ') + r.message.created);
                                }
                                if (r.message.updated !== undefined) {
                                    details.push(__('Updated: ') + r.message.updated);
                                }
                                if (r.message.error_count && r.message.error_count > 0) {
                                    details.push(__('Errors: ') + r.message.error_count);
                                }
                                
                                let full_message = msg;
                                if (details.length > 0) {
                                    full_message += '<br>' + details.join(', ');
                                }
                                
                                // Show error details if available
                                if (r.message.errors && Array.isArray(r.message.errors) && r.message.errors.length > 0) {
                                    let error_list = r.message.errors.slice(0, 5).map(function(e) {
                                        return '- ' + (e.employee || 'Unknown') + ': ' + (e.error || 'Unknown error');
                                    }).join('<br>');
                                    if (r.message.errors.length > 5) {
                                        error_list += '<br>... and ' + (r.message.errors.length - 5) + ' more errors';
                                    }
                                    full_message += '<br><br><b>' + __('Error Details:') + '</b><br>' + error_list;
                                }
                                
                                if (!r.message.error_count || r.message.error_count === 0) {
                                    full_message += '<br><br>' + __('Step 2 Complete: You can now submit the EMP501 Reconciliation.');
                                }
                                
                                frappe.msgprint({
                                    title: __('IRP5 Generation Complete'),
                                    message: full_message,
                                    indicator: (r.message.error_count && r.message.error_count > 0) ? 'orange' : 'green'
                                });
                                
                                frm.refresh();
                            }
                        },
                        error: function(r) {
                            frappe.msgprint({
                                title: __('Error'),
                                message: __('Failed to generate IRP5 certificates. Please check the error log.'),
                                indicator: 'red'
                            });
                        }
                    });
                }
            );
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
            method: "za_local.sa_payroll.doctype.emp501_reconciliation.emp501_reconciliation.get_period_dates",
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
                method: 'za_local.sa_payroll.doctype.emp501_reconciliation.emp501_reconciliation.get_company_tax_details',
                args: {
                    company: frm.doc.company
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('paye_reference_number', r.message.za_paye_reference_number);
                        frm.set_value('sdl_reference_number', r.message.za_sdl_reference_number);
                        frm.set_value('uif_reference_number', r.message.za_uif_reference_number);

                        if (!r.message.za_paye_reference_number && !frm.paye_warning_shown) {
                            frappe.msgprint({
                                title: __('Missing PAYE Number'),
                                indicator: 'orange',
                                message: __('The PAYE Reference Number is missing for the selected company. Please update it in the Company form.')
                            });
                            frm.paye_warning_shown = true;
                        }
                        if (!r.message.za_sdl_reference_number && !frm.sdl_warning_shown) {
                            frappe.msgprint({
                                title: __('Missing SDL Number'),
                                indicator: 'orange',
                                message: __('The SDL Reference Number is missing for the selected company. Please update it in the Company form.')
                            });
                            frm.sdl_warning_shown = true;
                        }
                        if (!r.message.za_uif_reference_number && !frm.uif_warning_shown) {
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
