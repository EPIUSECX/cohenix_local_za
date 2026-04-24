/**
 * ZA VAT:
 * - when the same account has multiple tax rows (15% and 0%), each row must
 *   only get amount from items whose rate matches that row
 * - on Sales Invoice, provide SA tax invoice readiness checks and recommended
 *   print-profile handling without disturbing the existing SA defaults
 */
(function () {
	function install_za_get_tax_rate(frm) {
		const cscript = frm.cscript;
		if (!cscript || typeof cscript._get_tax_rate !== "function") return;
		if (cscript._get_tax_rate._za_vat_installed) return;

		cscript._get_tax_rate = function (tax, item_tax_map) {
			if (Object.prototype.hasOwnProperty.call(item_tax_map || {}, tax.account_head)) {
				const item_rate = flt(item_tax_map[tax.account_head], 2);
				if (flt(item_rate) === flt(tax.rate)) return item_rate;
				return 0;
			}
			return tax.rate;
		};
		cscript._get_tax_rate._za_vat_installed = true;
		if (frm.doc.items && frm.doc.items.length && typeof cscript.calculate_taxes_and_totals === "function") {
			cscript.calculate_taxes_and_totals();
		}
	}

	function setup_form(doctype) {
		frappe.ui.form.on(doctype, {
			onload(frm) {
				install_za_get_tax_rate(frm);
			},
			form_render(frm) {
				install_za_get_tax_rate(frm);
			},
		});
	}

	setup_form("Sales Invoice");
	setup_form("Purchase Invoice");

	frappe.ui.form.on("Sales Invoice", {
		refresh(frm) {
			if (![0, 1].includes(frm.doc.docstatus)) return;

			schedule_sa_print_format_update(frm);
			frm.add_custom_button(__("Check SA Tax Invoice"), () => {
				frappe.call({
					method: "za_local.sa_vat.tax_invoice.check_tax_invoice_readiness",
					args: { sales_invoice: frm.doc.name },
					freeze: true,
					freeze_message: __("Reviewing South Africa tax invoice requirements..."),
					callback: ({ message }) => show_tax_invoice_dialog(message),
				});
			}, __("South Africa"));
		},
		company(frm) {
			schedule_sa_print_format_update(frm);
		},
		grand_total(frm) {
			schedule_sa_print_format_update(frm);
		},
		base_grand_total(frm) {
			schedule_sa_print_format_update(frm);
		},
		is_pos(frm) {
			schedule_sa_print_format_update(frm);
		},
		is_return(frm) {
			schedule_sa_print_format_update(frm);
		},
	});

	function show_tax_invoice_dialog(message) {
		if (!message) return;

		const rows = (message.checks || [])
			.map(
				(item) => `
				<tr>
					<td style="padding: 8px 10px; font-weight: 500;">${frappe.utils.escape_html(item.label)}</td>
					<td style="padding: 8px 10px;">
						<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;background:${item.ok ? "#ecfdf3" : "#fff4e5"};color:${item.ok ? "#027a48" : "#b54708"};">
							<span style="width:8px;height:8px;border-radius:999px;background:${item.ok ? "#12b76a" : "#f79009"};"></span>
							${item.ok ? __("Ready") : __("Needs attention")}
						</span>
					</td>
					<td style="padding: 8px 10px; color: #667085;">${frappe.utils.escape_html(item.detail || "")}</td>
				</tr>`,
			)
			.join("");

		const intro = `
			<div style="margin-bottom: 16px;">
				<div style="font-size: 14px; color: #667085;">${__("Recommended invoice type")}</div>
				<div style="font-size: 20px; font-weight: 700; margin-top: 4px;">${frappe.utils.escape_html(
					frappe.model.unscrub(message.invoice_type || ""),
				)}</div>
				${
					message.recommended_print_format
						? `<div style="margin-top: 8px; color: #667085;">${__("Recommended print format")}: <b>${frappe.utils.escape_html(message.recommended_print_format)}</b></div>`
						: ""
				}
			</div>
		`;

		const dialog = new frappe.ui.Dialog({
			title: __("South Africa Tax Invoice Check"),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "result",
					options: `
						${intro}
						<table style="width:100%; border-collapse: collapse;">
							<thead>
								<tr>
									<th style="text-align:left; padding: 8px 10px;">${__("Requirement")}</th>
									<th style="text-align:left; padding: 8px 10px;">${__("Status")}</th>
									<th style="text-align:left; padding: 8px 10px;">${__("Detail")}</th>
								</tr>
							</thead>
							<tbody>${rows}</tbody>
						</table>
					`,
				},
			],
			primary_action_label: __("Close"),
			primary_action() {
				dialog.hide();
			},
		});

		dialog.show();
	}

	function schedule_sa_print_format_update(frm) {
		clearTimeout(frm._za_print_format_timeout);
		frm._za_print_format_timeout = setTimeout(() => {
			apply_sa_default_print_format(frm);
		}, 150);
	}

	function apply_sa_default_print_format(frm) {
		if (!frm.doc.company) return;

		frappe.call({
			method: "za_local.sa_vat.tax_invoice.get_sales_invoice_print_profile",
			args: {
				company: frm.doc.company,
				base_grand_total: frm.doc.base_grand_total,
				grand_total: frm.doc.grand_total,
				is_pos: frm.doc.is_pos,
				is_return: frm.doc.is_return,
			},
			callback: ({ message }) => {
				if (!message) return;
				if (message.preserve_existing_default) return;
				if (message.override_default && message.print_format) {
					cache_original_default_print_format(frm);
					frm.meta.default_print_format = message.print_format;
					return;
				}
				restore_original_default_print_format(frm);
			},
		});
	}

	function cache_original_default_print_format(frm) {
		if (!Object.prototype.hasOwnProperty.call(frm.meta, "_za_original_default_print_format")) {
			frm.meta._za_original_default_print_format = frm.meta.default_print_format || null;
		}
	}

	function restore_original_default_print_format(frm) {
		if (!Object.prototype.hasOwnProperty.call(frm.meta, "_za_original_default_print_format")) {
			return;
		}
		frm.meta.default_print_format = frm.meta._za_original_default_print_format || null;
	}
})();
