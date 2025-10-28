frappe.ui.form.on('Workplace Injury', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1) {
            // Add button to create OID claim if not already created
            if (!frm.doc.oid_claim && !frm.doc.requires_claim) {
                frm.add_custom_button(__('Create OID Claim'), function() {
                    frappe.confirm(
                        __('Do you want to create an OID Claim for this workplace injury?'),
                        function() {
                            frm.set_value('requires_claim', 1);
                            frm.save().then(() => {
                                frappe.show_alert({
                                    message: __('OID Claim will be created when document is saved'),
                                    indicator: 'green'
                                });
                            });
                        }
                    );
                });
            }
            
            // Add button to create leave application if not already created
            if (!frm.doc.leave_application && !frm.doc.requires_leave) {
                frm.add_custom_button(__('Create Leave Application'), function() {
                    frappe.confirm(
                        __('Do you want to create a Leave Application for this workplace injury?'),
                        function() {
                            frm.set_value('requires_leave', 1);
                            
                            // Open dialog to set leave days
                            frappe.prompt([
                                {
                                    fieldname: 'leave_days',
                                    label: __('Leave Days'),
                                    fieldtype: 'Int',
                                    reqd: 1,
                                    default: 7
                                }
                            ],
                            function(values) {
                                frm.set_value('leave_days', values.leave_days);
                                frm.save().then(() => {
                                    frappe.show_alert({
                                        message: __('Leave Application will be created when document is saved'),
                                        indicator: 'green'
                                    });
                                });
                            },
                            __('Set Leave Days'),
                            __('Create')
                            );
                        }
                    );
                });
            }
            
            // Add button to view OID claim if created
            if (frm.doc.oid_claim) {
                frm.add_custom_button(__('View OID Claim'), function() {
                    frappe.set_route('Form', 'OID Claim', frm.doc.oid_claim);
                });
            }
            
            // Add button to view leave application if created
            if (frm.doc.leave_application) {
                frm.add_custom_button(__('View Leave Application'), function() {
                    frappe.set_route('Form', 'Leave Application', frm.doc.leave_application);
                });
            }
        }
    },
    
    employee: function(frm) {
        // Get employee details
        if (frm.doc.employee) {
            frappe.db.get_value('Employee', frm.doc.employee, ['company', 'department', 'designation'])
                .then(r => {
                    if (r.message) {
                        frm.set_value('company', r.message.company);
                        frm.set_value('department', r.message.department);
                        frm.set_value('designation', r.message.designation);
                    }
                });
        }
    },
    
    medical_attention_required: function(frm) {
        // Toggle required fields based on medical attention
        frm.toggle_reqd('medical_provider', frm.doc.medical_attention_required);
        frm.toggle_reqd('expected_recovery_date', frm.doc.medical_attention_required);
    },
    
    requires_leave: function(frm) {
        // Toggle required fields based on leave requirement
        frm.toggle_reqd('leave_days', frm.doc.requires_leave);
        
        // Calculate leave days if expected recovery date is set
        if (frm.doc.requires_leave && frm.doc.expected_recovery_date && frm.doc.injury_date) {
            const recovery_date = frappe.datetime.str_to_obj(frm.doc.expected_recovery_date);
            const injury_date = frappe.datetime.str_to_obj(frm.doc.injury_date);
            const days_diff = frappe.datetime.get_diff(recovery_date, injury_date) + 1;
            frm.set_value('leave_days', days_diff);
        }
    },
    
    expected_recovery_date: function(frm) {
        // Update leave days if leave is required
        if (frm.doc.requires_leave && frm.doc.expected_recovery_date && frm.doc.injury_date) {
            const recovery_date = frappe.datetime.str_to_obj(frm.doc.expected_recovery_date);
            const injury_date = frappe.datetime.str_to_obj(frm.doc.injury_date);
            const days_diff = frappe.datetime.get_diff(recovery_date, injury_date) + 1;
            frm.set_value('leave_days', days_diff);
        }
    }
});
