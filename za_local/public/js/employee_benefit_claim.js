frappe.ui.form.on('Employee Benefit Claim', {
	async kilometer(frm) {
		const response = await frappe.call({
			method: 'frappe.client.get_value',
			args: {
				doctype: 'HR Settings',
				filters: { name: 'HR Settings' },
				fieldname: ['amount_per_kilometer'],
			},
		});
		const amount_per_kilometer = Number(response.message?.amount_per_kilometer || 0);
		if (!amount_per_kilometer) {
			frappe.throw(__("Set Amount Per Kilometer in HR Settings"));
		}
		await frm.set_value("claimed_amount", (frm.doc.kilometer || 0) * amount_per_kilometer);
	},
});
