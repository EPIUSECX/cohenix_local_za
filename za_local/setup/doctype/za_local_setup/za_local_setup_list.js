// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.listview_settings['ZA Local Setup'] = {
	add_fields: ['setup_status', 'company'],
	get_indicator: function(doc) {
		const status_colors = {
			'Pending': 'orange',
			'In Progress': 'blue',
			'Completed': 'green'
		};
		return [__(doc.setup_status), status_colors[doc.setup_status], 'setup_status,=,' + doc.setup_status];
	}
};

