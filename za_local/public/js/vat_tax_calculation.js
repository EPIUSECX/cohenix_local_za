// Copyright (c) 2025, Aerele and contributors
// For license information, please see license.txt
/**
 * ZA VAT: when the same account has multiple tax rows (15% and 0%),
 * each row must only get amount from items whose rate matches that row.
 * This overrides the form controller's _get_tax_rate for client-side calculation.
 */
(function () {
	function install_za_get_tax_rate(frm) {
		var cscript = frm.cscript;
		if (!cscript || typeof cscript._get_tax_rate !== "function") return;
		if (cscript._get_tax_rate._za_vat_installed) return;

		cscript._get_tax_rate = function (tax, item_tax_map) {
			if (Object.prototype.hasOwnProperty.call(item_tax_map || {}, tax.account_head)) {
				var item_rate = flt(item_tax_map[tax.account_head], 2);
				// Only apply this row's rate when the item's rate matches; else this row gets 0
				if (flt(item_rate) === flt(tax.rate)) return item_rate;
				return 0;
			}
			return tax.rate;
		};
		cscript._get_tax_rate._za_vat_installed = true;
		// Re-run tax calculation so amounts use the new logic (fixes Purchase Invoice 15% row showing 0)
		if (frm.doc.items && frm.doc.items.length && typeof cscript.calculate_taxes_and_totals === "function") {
			cscript.calculate_taxes_and_totals();
		}
	}

	function setup_form(doctype) {
		frappe.ui.form.on(doctype, {
			onload: function (frm) {
				install_za_get_tax_rate(frm);
			},
			form_render: function (frm) {
				// cscript may be ready after first render
				install_za_get_tax_rate(frm);
			},
		});
	}
	setup_form("Sales Invoice");
	setup_form("Purchase Invoice");
})();
