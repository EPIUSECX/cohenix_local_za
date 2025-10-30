// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk IT3b Certificate Generation', {
	onload: function(frm) {
		// Set default tax year if not set
		if (!frm.doc.tax_year) {
			const today = new Date();
			const currentMonth = today.getMonth() + 1;
			const currentYear = today.getFullYear();
			
			// SA tax year runs March to February
			if (currentMonth >= 3) {
				frm.set_value('tax_year', `${currentYear}-${currentYear + 1}`);
			} else {
				frm.set_value('tax_year', `${currentYear - 1}-${currentYear}`);
			}
		}
		
		// Initialize filter list
		frm.trigger('setup_filter_list');
	},
	
	refresh: function(frm) {
		frm.disable_save();
		frm.page.clear_indicator();
		
		if (frm.doc.company && frm.doc.tax_year) {
			frm.trigger('render_periods_table');
		}
	},
	
	company: function(frm) {
		if (frm.doc.company && frm.doc.tax_year) {
			frm.trigger('render_periods_table');
		}
	},
	
	tax_year: function(frm) {
		if (frm.doc.company && frm.doc.tax_year) {
			frm.trigger('render_periods_table');
		}
	},
	
	from_period: function(frm) {
		if (frm.doc.company && frm.doc.tax_year) {
			frm.trigger('render_periods_table');
		}
	},
	
	to_period: function(frm) {
		if (frm.doc.company && frm.doc.tax_year) {
			frm.trigger('render_periods_table');
		}
	},
	
	setup_filter_list: function(frm) {
		// Advanced filters can be added here if needed
		frm.fields_dict.filter_list.$wrapper.html(
			'<p style="padding: 10px; color: #888;">Additional filters can be added in future versions.</p>'
		);
	},
	
	render_periods_table: function(frm) {
		// Get periods
		frappe.call({
			method: 'get_periods',
			doc: frm.doc,
			args: {
				advanced_filters: []
			},
			callback: function(r) {
				if (r.message) {
					frm.trigger('make_periods_table', r.message);
				}
			}
		});
	},
	
	make_periods_table: function(frm, periods) {
		const wrapper = frm.fields_dict.periods_html.$wrapper;
		wrapper.empty();
		
		if (periods.length === 0) {
			wrapper.html(
				'<div class="alert alert-info">All periods have IT3b certificates generated. No pending periods found.</div>'
			);
			return;
		}
		
		// Create table HTML
		let html = `
			<div class="periods-table">
				<table class="table table-bordered">
					<thead>
						<tr>
							<th style="width: 5%;">
								<input type="checkbox" class="select-all-periods">
							</th>
							<th style="width: 20%;">Fiscal Period</th>
							<th style="width: 15%;">Total PAYE</th>
							<th style="width: 15%;">Total UIF</th>
							<th style="width: 15%;">Total SDL</th>
							<th style="width: 15%;">Total ETI</th>
							<th style="width: 15%;">Status</th>
						</tr>
					</thead>
					<tbody>
		`;
		
		periods.forEach((period, idx) => {
			html += `
				<tr data-period-idx="${idx}">
					<td>
						<input type="checkbox" class="select-period" data-period='${JSON.stringify(period)}'>
					</td>
					<td><strong>${period.fiscal_period}</strong></td>
					<td>R ${format_currency(period.total_paye)}</td>
					<td>R ${format_currency(period.total_uif)}</td>
					<td>R ${format_currency(period.total_sdl)}</td>
					<td>R ${format_currency(period.total_eti)}</td>
					<td><span class="indicator orange">${period.status}</span></td>
				</tr>
			`;
		});
		
		html += `
					</tbody>
				</table>
				<div style="margin-top: 15px;">
					<button class="btn btn-primary btn-generate-certificates" style="margin-right: 10px;">
						<i class="fa fa-plus"></i> Generate Selected Certificates
					</button>
					<span class="selected-count" style="color: #888;"></span>
				</div>
			</div>
		`;
		
		wrapper.html(html);
		
		// Bind events
		wrapper.find('.select-all-periods').on('change', function() {
			const isChecked = $(this).is(':checked');
			wrapper.find('.select-period').prop('checked', isChecked);
			frm.trigger('update_selected_count');
		});
		
		wrapper.find('.select-period').on('change', function() {
			frm.trigger('update_selected_count');
		});
		
		wrapper.find('.btn-generate-certificates').on('click', function() {
			frm.trigger('generate_selected_certificates');
		});
		
		frm.trigger('update_selected_count');
	},
	
	update_selected_count: function(frm) {
		const wrapper = frm.fields_dict.periods_html.$wrapper;
		const selected = wrapper.find('.select-period:checked').length;
		const total = wrapper.find('.select-period').length;
		
		wrapper.find('.selected-count').text(`${selected} of ${total} period(s) selected`);
		
		if (selected > 0) {
			wrapper.find('.btn-generate-certificates').prop('disabled', false);
		} else {
			wrapper.find('.btn-generate-certificates').prop('disabled', true);
		}
	},
	
	generate_selected_certificates: function(frm) {
		const wrapper = frm.fields_dict.periods_html.$wrapper;
		const selected_periods = [];
		
		wrapper.find('.select-period:checked').each(function() {
			selected_periods.push(JSON.parse($(this).attr('data-period')));
		});
		
		if (selected_periods.length === 0) {
			frappe.msgprint(__('Please select at least one period'));
			return;
		}
		
		// Confirm generation
		frappe.confirm(
			__('Generate IT3b Certificates for {0} period(s)?', [selected_periods.length]),
			function() {
				frappe.call({
					method: 'bulk_generate_certificates',
					doc: frm.doc,
					args: {
						periods: selected_periods
					},
					callback: function(r) {
						// Refresh the table
						frm.trigger('render_periods_table');
					}
				});
			}
		);
	}
});

// Listen for realtime updates
frappe.realtime.on('completed_bulk_it3b_generation', function(data) {
	if (data.success && data.success.length > 0) {
		let message = `<strong>Successfully Generated:</strong><ul>`;
		data.success.forEach(item => {
			message += `<li>${item.period}: ${item.doc}</li>`;
		});
		message += `</ul>`;
		
		if (data.failure && data.failure.length > 0) {
			message += `<br><strong>Failed:</strong><ul>`;
			data.failure.forEach(item => {
				message += `<li>${item.period}: ${item.error}</li>`;
			});
			message += `</ul>`;
		}
		
		frappe.msgprint({
			title: __('Bulk Generation Complete'),
			message: message,
			indicator: 'green'
		});
	}
});

