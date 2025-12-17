// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Payment Batch', {
	refresh: function(frm) {
		// Show Generate EFT File button when form is saved and has required fields
		if (!frm.is_new() && frm.doc.payroll_entry && frm.doc.payment_date) {
			frm.add_custom_button(__('Generate EFT File'), async () => {
				if (!frm.doc.bank_format) {
					frappe.msgprint(__('Please select a Bank Format'));
					return;
				}
				frm.clear_custom_button_group();
				frm.toggle_enable(false);
				frappe.show_alert({message: __('Generating EFT file...'), indicator: 'blue'});
				try {
					const bankMap = {
						'Standard Bank': 'standard_bank',
						'ABSA': 'absa',
						'FNB': 'fnb',
						'Nedbank': 'nedbank',
					};
					const bank_format = bankMap[frm.doc.bank_format] || 'fnb';
					const r = await frappe.call({
						method: 'za_local.za_local.utils.integrations.eft_file_generator.generate_eft_file',
						args: {
							payroll_entry: frm.doc.payroll_entry,
							bank_format
						}
					});
					const { file_content, filename } = r.message || {};
					if (!file_content) {
						frappe.msgprint(__('No file content returned'));
						return;
					}
					// Save file to server and attach to this document
					const saved = await frappe.call({
						method: 'frappe.client.save_file',
						args: {
							filename,
							is_private: 1,
							doctype: frm.doc.doctype,
							name: frm.doc.name,
							filedata: btoa(unescape(encodeURIComponent(file_content)))
						}
					});
					const file_url = saved.message && saved.message.file_url;
					await frm.call('set_eft_generated', { file_url });
					await frm.reload_doc();
					frappe.show_alert({message: __('EFT file generated'), indicator: 'green'});
					if (file_url) {
						window.open(file_url, '_blank');
					}
				} catch (e) {
					console.error(e);
					frappe.msgprint({message: __('Failed to generate EFT file'), indicator: 'red'});
				} finally {
					frm.toggle_enable(true);
				}
			});
		}
	}
});
