// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bargaining Council', {
	refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button('Import Common Councils', () => {
                frappe.call({
                    method: 'za_local.utils.csv_importer.import_csv_data',
                    args: { doctype: 'Bargaining Council', csv_filename: 'bargaining_council_list.csv' },
                    callback: () => frm.reload_doc()
                });
            });
        }
	}
});
