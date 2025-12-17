frappe.ui.form.on('OID Claim', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1) {
            // Add buttons to update claim status
            if (frm.doc.claim_status !== 'Approved' && frm.doc.claim_status !== 'Rejected' && frm.doc.claim_status !== 'Paid') {
                frm.add_custom_button(__('Approve Claim'), function() {
                    frappe.prompt([
                        {
                            fieldname: 'compensation_amount',
                            label: __('Compensation Amount'),
                            fieldtype: 'Currency',
                            reqd: 1
                        }
                    ],
                    function(values) {
                        frm.call({
                            doc: frm.doc,
                            method: 'update_claim_status',
                            args: {
                                status: 'Approved',
                                compensation_amount: values.compensation_amount
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __('Claim approved successfully'),
                                        indicator: 'green'
                                    });
                                    frm.refresh();
                                }
                            }
                        });
                    },
                    __('Set Compensation Amount'),
                    __('Approve')
                    );
                }).addClass('btn-primary');
                
                frm.add_custom_button(__('Reject Claim'), function() {
                    frappe.confirm(
                        __('Are you sure you want to reject this claim?'),
                        function() {
                            frm.call({
                                doc: frm.doc,
                                method: 'update_claim_status',
                                args: {
                                    status: 'Rejected'
                                },
                                callback: function(r) {
                                    if (r.message) {
                                        frappe.show_alert({
                                            message: __('Claim rejected'),
                                            indicator: 'red'
                                        });
                                        frm.refresh();
                                    }
                                }
                            });
                        }
                    );
                }).addClass('btn-danger');
                
                frm.add_custom_button(__('Under Review'), function() {
                    frm.call({
                        doc: frm.doc,
                        method: 'update_claim_status',
                        args: {
                            status: 'Under Review'
                        },
                        callback: function(r) {
                            if (r.message) {
                                frappe.show_alert({
                                    message: __('Claim status updated to Under Review'),
                                    indicator: 'blue'
                                });
                                frm.refresh();
                            }
                        }
                    });
                });
            }
            
            // Add button to mark as paid if approved
            if (frm.doc.claim_status === 'Approved') {
                frm.add_custom_button(__('Mark as Paid'), function() {
                    frappe.prompt([
                        {
                            fieldname: 'payment_date',
                            label: __('Payment Date'),
                            fieldtype: 'Date',
                            reqd: 1,
                            default: frappe.datetime.get_today()
                        }
                    ],
                    function(values) {
                        frm.call({
                            doc: frm.doc,
                            method: 'update_claim_status',
                            args: {
                                status: 'Paid',
                                payment_date: values.payment_date
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __('Claim marked as paid'),
                                        indicator: 'green'
                                    });
                                    frm.refresh();
                                }
                            }
                        });
                    },
                    __('Set Payment Date'),
                    __('Pay')
                    );
                }).addClass('btn-primary');
            }
            
            // Add button to view workplace injury if linked
            if (frm.doc.workplace_injury) {
                frm.add_custom_button(__('View Workplace Injury'), function() {
                    frappe.set_route('Form', 'Workplace Injury', frm.doc.workplace_injury);
                });
            }
        }
        
        // Add button to add medical report
        frm.add_custom_button(__('Add Medical Report'), function() {
            frappe.prompt([
                {
                    fieldname: 'report_date',
                    label: __('Report Date'),
                    fieldtype: 'Date',
                    reqd: 1,
                    default: frappe.datetime.get_today()
                },
                {
                    fieldname: 'medical_provider',
                    label: __('Medical Provider'),
                    fieldtype: 'Data',
                    reqd: 1
                },
                {
                    fieldname: 'report_type',
                    label: __('Report Type'),
                    fieldtype: 'Select',
                    options: 'Initial Assessment\nProgress Report\nSpecialist Report\nFinal Report',
                    reqd: 1
                },
                {
                    fieldname: 'diagnosis',
                    label: __('Diagnosis'),
                    fieldtype: 'Small Text',
                    reqd: 1
                }
            ],
            function(values) {
                let row = frappe.model.add_child(frm.doc, 'OID Medical Report', 'medical_reports');
                row.report_date = values.report_date;
                row.medical_provider = values.medical_provider;
                row.report_type = values.report_type;
                row.diagnosis = values.diagnosis;
                frm.refresh_field('medical_reports');
                frm.save();
            },
            __('Add Medical Report'),
            __('Add')
            );
        });
    },
    
    workplace_injury: function(frm) {
        // Fetch details from workplace injury
        if (frm.doc.workplace_injury) {
            frappe.db.get_doc('Workplace Injury', frm.doc.workplace_injury)
                .then(injury => {
                    frm.set_value('employee', injury.employee);
                    frm.set_value('injury_date', injury.injury_date);
                    frm.set_value('injury_type', injury.injury_type);
                    frm.set_value('injury_location', injury.injury_location);
                    frm.set_value('injury_description', injury.injury_description);
                });
        }
    },
    
    employee: function(frm) {
        // Get employee details
        if (frm.doc.employee) {
            frappe.db.get_value('Employee', frm.doc.employee, ['company', 'za_id_number'])
                .then(r => {
                    if (r.message) {
                        frm.set_value('company', r.message.company);
                        frm.set_value('id_number', r.message.za_id_number);
                    }
                });
        }
    }
});
