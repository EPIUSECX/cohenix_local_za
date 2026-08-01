// Copyright (c) 2025, Cohenix and contributors
// For license information, please see license.txt

const EFT_ROLES = ["HR Manager", "Accounts Manager", "System Manager"];

frappe.ui.form.on("Payroll Payment Batch", {
	setup(frm) {
		frm.set_query("bank_account", () => ({
			filters: {
				company: frm.doc.company,
				is_company_account: 1,
				disabled: 0,
			},
		}));
	},

	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !can_generate_eft(frm)) {
			return;
		}

		frm.add_custom_button(__("Generate FNB OBE CSV"), async () => {
			try {
				const response = await frappe.call({
					method: "za_local.utils.integrations.eft_file_generator.generate_eft_file",
					args: {payment_batch: frm.doc.name},
					freeze: true,
					freeze_message: __("Validating payroll and generating the private FNB file..."),
				});
				const result = response.message || {};
				await frm.reload_doc();
				frappe.show_alert({
					message: result.reused ? __("Existing private EFT file reused") : __("Private EFT file generated"),
					indicator: "green",
				});
				if (result.file_url) {
					window.open(encodeURI(result.file_url), "_blank", "noopener");
				}
			} catch (error) {
				frappe.show_alert({message: __("EFT file generation failed"), indicator: "red"});
			}
		});
	},

	bank_format(frm) {
		if (frm.doc.bank_format && frm.doc.bank_format !== "FNB OBE CSV") {
			frappe.msgprint({
				title: __("Manual Bank Onboarding Required"),
				message: __("Automated {0} payroll files are disabled until the bank's current official layout has been verified and onboarded.", [frm.doc.bank_format]),
				indicator: "orange",
			});
		}
	},
});

function can_generate_eft(frm) {
	return frm.has_perm("write") && EFT_ROLES.some((role) => frappe.user.has_role(role));
}
