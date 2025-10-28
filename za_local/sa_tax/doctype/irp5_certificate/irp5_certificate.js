// Copyright (c) 2025, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('IRP5 Certificate', {
    refresh: function(frm) {
        // Always update UI based on generation_mode
        if (frm.doc.generation_mode === 'Bulk') {
            frm.set_df_property('income_details', 'hidden', 1);
            frm.set_df_property('deduction_details', 'hidden', 1);
            frm.set_df_property('company_contribution_details', 'hidden', 1);
            // Show summary if available
            frm.refresh_field('bulk_generation_summary');
        } else {
            frm.set_df_property('income_details', 'hidden', 0);
            frm.set_df_property('deduction_details', 'hidden', 0);
            frm.set_df_property('company_contribution_details', 'hidden', 0);
            frm.set_value('bulk_generation_summary', null);
            frm.refresh_field('bulk_generation_summary');
        }
        // Add unified Generate Certificate Data button in Draft state
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Generate Certificate Data'), function() {
                if (frm.doc.generation_mode === 'Bulk') {
                    let filters = {
                        company: frm.doc.company,
                        department: frm.doc.department,
                        tax_year: frm.doc.tax_year,
                        from_date: frm.doc.from_date,
                        to_date: frm.doc.to_date,
                        reconciliation_period: frm.doc.reconciliation_period
                    };
                    frappe.call({
                        method: 'kartoza.kartoza.doctype.irp5_certificate.irp5_certificate.bulk_generate_certificates',
                        args: { filters_json: JSON.stringify(filters) },
                        freeze: true,
                        freeze_message: __('Generating IRP5 Certificates for all matching employees...'),
                        callback: function(r) {
                    let summary = '';
                    if (r.message) {
                        summary = `<b>${__(r.message.message || r.message.error || 'Bulk generation complete.')}</b><br>`;
                        if (r.message.created && r.message.created.length) {
                            summary += __('Created: ') + r.message.created.join(', ') + '<br>';
                        }
                        if (r.message.updated && r.message.updated.length) {
                            summary += __('Updated: ') + r.message.updated.join(', ') + '<br>';
                        }
                        if (r.message.errors && r.message.errors.length) {
                            summary += __('Errors: ') + JSON.stringify(r.message.errors) + '<br>';
                        }
                    }
                    if (!summary) {
                        summary = __('No certificates were created or updated.');
                    }
                    frm.set_value('bulk_generation_summary', summary);
                    frm.refresh();
                    frm.refresh_field('bulk_generation_summary');
                        }
                    });
                } else {
                    frm.call({
                        method: 'generate_certificate_data',
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __('Generating Certificate Data...'),
                        callback: function(r) {
                            if (r.message) {
                                let counts = r.message;
                                frappe.show_alert({
                                    message: __(`Certificate data generated: ${counts.income_count} income items, ${counts.deduction_count} deduction items`),
                                    indicator: 'green'
                                }, 5);
                                frm.refresh();
                            }
                        }
                    });
                }
            }).addClass('btn-primary');
        }
    },
    from_date: function(frm) {
        if(frm.doc.from_date && !frm.doc.to_date) {
            // For Interim period: March to August
            if(frm.doc.reconciliation_period === 'Interim') {
                let from_date = frappe.datetime.str_to_obj(frm.doc.from_date);
                let to_date = new Date(from_date.getFullYear(), 7, 31); // August 31
                frm.set_value('to_date', frappe.datetime.obj_to_str(to_date));
            }
            // For Final period: March to February
            else if(frm.doc.reconciliation_period === 'Final') {
                let from_date = frappe.datetime.str_to_obj(frm.doc.from_date);
                let to_year = from_date.getFullYear() + 1;
                // Check for leap year
                let to_day = 28;
                if (to_year % 4 === 0 && (to_year % 100 !== 0 || to_year % 400 === 0)) {
                    to_day = 29;
                }
                let to_date = new Date(to_year, 1, to_day); // February 28/29
                frm.set_value('to_date', frappe.datetime.obj_to_str(to_date));
            }
        }
    },

    reconciliation_period: function(frm) {
        // If tax_year is set, trigger its onchange to re-evaluate from_date and to_date
        // based on the new reconciliation_period
        if (frm.doc.tax_year) {
            frm.trigger('tax_year');
        } 
        // If only from_date is set (and no tax_year), try to auto-calculate to_date
        else if (frm.doc.from_date) {
            frm.trigger('from_date');
        }
    },

    tax_year: function(frm) {
        if (frm.doc.tax_year) {
            frappe.model.with_doc("Fiscal Year", frm.doc.tax_year, function() {
                let fiscal_year_doc = frappe.get_doc("Fiscal Year", frm.doc.tax_year);
                let from_date_val = fiscal_year_doc.year_start_date;
                let to_date_val = fiscal_year_doc.year_end_date;

                if (frm.doc.reconciliation_period === 'Interim' && fiscal_year_doc.year_start_date) {
                    let year_start_obj = frappe.datetime.str_to_obj(fiscal_year_doc.year_start_date);
                    // SARS Interim is March 1 to Aug 31.
                    // This logic assumes the fiscal year starts March 1 for Interim to make sense.
                    if (year_start_obj.getMonth() + 1 === 3 && year_start_obj.getDate() === 1) {
                        from_date_val = fiscal_year_doc.year_start_date;
                        let to_date_interim = new Date(year_start_obj.getFullYear(), 7, 31); // Aug 31
                        to_date_val = frappe.datetime.obj_to_str(to_date_interim);
                    }
                }
                // For 'Final', the full fiscal year dates are usually correct for a March-Feb tax year.
                frm.set_value('from_date', from_date_val);
                frm.set_value('to_date', to_date_val);
                frm.refresh_fields(['from_date', 'to_date']);
            });
        } else {
            frm.set_value('from_date', null);
            frm.set_value('to_date', null);
            frm.refresh_fields(['from_date', 'to_date']);
        }
    },
    onload: function(frm) {
        // Hide Employee field if in Bulk mode on load
        if (frm.doc.generation_mode === 'Bulk') {
            frm.set_df_property('employee', 'hidden', 1);
            frm.set_value('employee', null);
        } else {
            frm.set_df_property('employee', 'hidden', 0);
        }
    },

    generation_mode: function(frm) {
        // React to Generation Mode change immediately
        if (frm.doc.generation_mode === 'Bulk') {
            frm.set_df_property('employee', 'hidden', 1);
            frm.set_value('employee', null);
            frm.set_df_property('income_details', 'hidden', 1);
            frm.set_df_property('deduction_details', 'hidden', 1);
            frm.set_df_property('company_contribution_details', 'hidden', 1);
            frm.refresh_field('bulk_generation_summary');
        } else {
            frm.set_df_property('employee', 'hidden', 0);
            frm.set_df_property('income_details', 'hidden', 0);
            frm.set_df_property('deduction_details', 'hidden', 0);
            frm.set_df_property('company_contribution_details', 'hidden', 0);
            frm.set_value('bulk_generation_summary', null);
            frm.refresh_field('bulk_generation_summary');
        }
        frm.refresh_fields();
    },

    after_save: function(frm) {
        // No-op: unified button is now in refresh handler
    },

    // Add your other handlers (refresh, from_date, to_date, reconciliation_period, tax_year, etc.) here
    // Example:
    // refresh: function(frm) { ... }
    // from_date: function(frm) { ... }
    // etc.
});

// IRP5 Income Detail Child Table
frappe.ui.form.on('IRP5 Income Detail', {
    income_details_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.tax_year = frm.doc.tax_year;
        row.period = frm.doc.reconciliation_period;
        frm.refresh_field('income_details');
    }
});

// IRP5 Deduction Detail Child Table
frappe.ui.form.on('IRP5 Deduction Detail', {
    deduction_details_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.tax_year = frm.doc.tax_year;
        row.period = frm.doc.reconciliation_period;
        frm.refresh_field('deduction_details');
    }
});