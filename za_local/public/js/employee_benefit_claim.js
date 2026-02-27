frappe.ui.form.on('Employee Benefit Claim', {
	kilometer: function(frm){
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'HR Settings',
				'filters': {'name': 'HR Settings'},
				'fieldname': [
								'amount_per_kilometer'
								]
			},
			async:false,
			callback: function(r){
					if(!r.exc){
						r.message["amount_per_kilometer"] = parseFloat(r.message["amount_per_kilometer"])
						if(!r.message["amount_per_kilometer"]){
							frappe.throw("Set Amount Per Kilometer in HR Settings")
						}
						frm.set_value("claimed_amount",frm.doc.kilometer * r.message["amount_per_kilometer"]);
					}
			}
		})
	}
});
