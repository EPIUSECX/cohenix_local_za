frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (
			frm.doc.docstatus !== 1 ||
			!(frm.doc.salary_slips_submitted || frm.doc.__onload?.submitted_ss)
		) {
			return;
		}

		frm.remove_custom_button(__("Make Bank Entry"));
		frm.add_custom_button(__("Make Bank Entry"), async () => {
			try {
				const employee_list = frm.doc.employees.map((row) => row.employee);
				const [employee_response, flags_response] = await Promise.all([
					frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "Employee",
							filters: { name: ["in", employee_list] },
							fields: ["name", "za_payroll_payable_bank_account", "employee_name"],
							limit_page_length: 0,
						},
					}),
					frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "Payroll Employee Detail",
							filters: { parent: frm.doc.name },
							fields: [
								"employee",
								"za_is_bank_entry_created",
								"za_is_company_contribution_created",
							],
							limit_page_length: 0,
						},
					}),
				]);

				const employees = employee_response.message || [];
				const flag_map = Object.fromEntries(
					(flags_response.message || []).map((item) => [
						item.employee,
						{
							is_bank_entry_created: item.za_is_bank_entry_created || 0,
							is_company_contribution_created: item.za_is_company_contribution_created || 0,
						},
					])
				);
				const bank_accounts = [
					...new Set(
						employees
							.map((employee) => employee.za_payroll_payable_bank_account)
							.filter(Boolean)
					),
				];
				if (!bank_accounts.length) {
					frappe.msgprint({
						message: __("No employees have bank accounts configured. Please configure bank accounts on Employee records."),
						indicator: "orange",
						title: __("Bank Account Required"),
					});
					return;
				}

				const bank_response = await frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "Bank Account",
						filters: { name: ["in", bank_accounts] },
						fields: ["name", "account"],
						limit_page_length: 0,
					},
				});
				const company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
				const bank_map = Object.fromEntries(
					(bank_response.message || []).map((bank) => [bank.name, company_currency])
				);
				const account_map = {};
				employees.forEach((employee) => {
					const bank_account = employee.za_payroll_payable_bank_account;
					if (!bank_account) {
						return;
					}
					const flags = flag_map[employee.name] || {};
					account_map[bank_account] ||= [];
					account_map[bank_account].push({
						employee: employee.name,
						employee_name: employee.employee_name,
						account_currency: bank_map[bank_account] || company_currency,
						is_bank_entry_created: flags.is_bank_entry_created || 0,
						is_company_contribution_created: flags.is_company_contribution_created || 0,
					});
				});
				show_bank_entry_dialog(frm, account_map);
			} catch {
				show_payroll_request_error();
			}
		}).addClass("btn-primary");
	},
});

function show_bank_entry_dialog(frm, account_map) {
	let field_list = [];
	let company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
	
	for (let account in account_map) {
		const safe_account = frappe.utils.escape_html(account);
		let is_read_only = 0;
		if (
			account_map[account].length ==
			account_map[account].filter(
				(item) => item.is_bank_entry_created
			).length
		) {
			is_read_only = 1;
		}
		field_list.push({
			label: safe_account,
			fieldname: account,
			fieldtype: "Check",
			read_only: is_read_only,
			change: () => {
				render_employee_list(d, account_map);
			},
		});
		field_list.push({
			fieldtype: "Column Break"
		});
		field_list.push({
			label: __("Payment Date") + " <small>(" + safe_account + ")</small>",
			fieldname: account + "_date",
			fieldtype: "Date",
			read_only: is_read_only,
			default: frm.doc.posting_date,
			change: () => {
				frappe.call({
					method: "erpnext.setup.utils.get_exchange_rate",
					args: {
						from_currency: account_map[account][0].account_currency,
						to_currency: company_currency,
						transaction_date: d.get_value(account + "_date"),
					},
					callback: function (r) {
						if (r.message) {
							d.set_value(account + "_ex_rate", r.message);
						}
					},
					error: show_payroll_request_error,
				});
			},
		});
		field_list.push({
			fieldtype: "Column Break"
		});
		field_list.push({
			label: __("Exchange Rate") + " <small>(" + safe_account + ")</small>",
			fieldname: account + "_ex_rate",
			fieldtype: "Float",
			precision: 9,
			default: 1,
			read_only: is_read_only || company_currency == account_map[account][0].account_currency ? 1 : 0,
		});
		field_list.push({ fieldtype: "Section Break" });
	}
	
	field_list.push({
		fieldname: "employee_list",
		fieldtype: "HTML",
		options: '<div class="container" style="margin:0px;width:100%;"><div class="row employee-list"></div></div>',
	});
	
	const d = new frappe.ui.Dialog({
		title: __("Enter details"),
		fields: field_list,
		size: "extra-large",
		primary_action_label: __("Create Bank Entry"),
		primary_action(values) {
			let account_emp_map = {};
			d.$wrapper.find(".employee-checkbox:checkbox:checked").each((i, e) => {
				const acc = $(e).attr("data-account");
				const emp = $(e).attr("data-employee");
				if (!account_emp_map[acc]) {
					account_emp_map[acc] = { employees: [] };
				}
				if (!account_emp_map[acc].employees.includes(emp)) {
					account_emp_map[acc].employees.push(emp);
				}
			});
			for (const account in account_emp_map) {
				if (!values[account + "_date"]) {
					frappe.throw(__("Posting date for {0} is mandatory", [account]));
				}

				if (!values[account + "_ex_rate"]){
					frappe.throw(__("Exchange rate cannot be zero"));
				}

				account_emp_map[account]["currency"] =
					account_map[account][0].account_currency;
				account_emp_map[account]["posting_date"] =
					values[account + "_date"];
				account_emp_map[account]["exchange_rate"] =
					values[account + "_ex_rate"];
			}
			// Call make_payment_entry via standalone wrapper function
			// This bypasses run_doc_method's permission checks which may be too strict for submitted documents
			frappe.call({
				method: "za_local.overrides.payroll_entry.make_payment_entry_for_payroll",
				args: {
					dt: "Payroll Entry",
					dn: frm.doc.name,
					selected_payment_account: account_emp_map,
				},
				callback: function () {
					d.hide();
					frappe.set_route("List", "Journal Entry", {
						"Journal Entry Account.reference_name": frm.doc.name,
					});
				},
				error: show_payroll_request_error,
				freeze: true,
				freeze_message: __("Creating Payment Entries......"),
			});
		},
	});

	d.show();
}

function show_payroll_request_error() {
	frappe.msgprint({
		title: __("Payroll Request Failed"),
		message: __("The payroll request could not be completed. Review the error message and try again."),
		indicator: "red",
	});
}

function render_employee_list(dialog, account_map) {
	const $employee_list = dialog.$wrapper.find(".employee-list");
	$employee_list.empty();

	for (const account in account_map) {
		if (!dialog.get_value(account)) {
			continue;
		}

		const $account_link = $("<a>", {
			href: `/app/bank-account/${encodeURIComponent(account)}`,
			target: "_blank",
			rel: "noopener noreferrer",
		}).text(account);
		const $heading = $("<div>", { class: "col-sm-12" })
			.css("border-bottom", "1px solid #d4d4d4")
			.append($("<b>").append(__("Employees paid with "), $account_link));
		$employee_list.append($heading);

		account_map[account].forEach((row) => {
			const is_disabled = Boolean(row.is_bank_entry_created);
			const $checkbox = $("<input>", {
				type: "checkbox",
				class: "employee-checkbox",
			})
				.attr("data-account", account)
				.attr("data-employee", row.employee)
				.prop("checked", !is_disabled)
				.prop("disabled", is_disabled);
			const $employee_link = $("<a>", {
				href: `/app/employee/${encodeURIComponent(row.employee)}`,
				target: "_blank",
				rel: "noopener noreferrer",
			}).text(`${row.employee}: ${row.employee_name || ""}`);
			const $employee = $("<div>", { class: "col-sm-6" })
				.css("border-bottom", "1px solid #d4d4d4")
				.append($checkbox, " ", $employee_link);
			$employee_list.append($employee);
		});
	}
}
