frappe.ui.form.on("Payroll Entry", {
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			// if (frm.custom_buttons) frm.clear_custom_buttons();
			if (
				frm.doc.salary_slips_submitted ||
				(frm.doc.__onload && frm.doc.__onload.submitted_ss)
			) {
				frm.remove_custom_button("Make Bank Entry");
				frm
					.add_custom_button(__("Make Bank Entry"), function () {
						// Fetch employee bank accounts from Employee doctype
						let employee_list = frm.doc.employees.map(row => row.employee);
						
						frappe.call({
							method: "frappe.client.get_list",
							args: {
								doctype: "Employee",
								filters: { name: ["in", employee_list] },
								fields: ["name", "za_payroll_payable_bank_account", "employee_name"],
								limit_page_length: 0
							},
							callback: function(r) {
								if (r.message) {
									// Also fetch bank account details and flags
									// Use whitelisted method that checks permission on parent Payroll Entry
									frappe.call({
										method: "za_local.overrides.payroll_entry.get_payroll_employee_detail_flags",
										args: {
											payroll_entry_name: frm.doc.name
										},
										callback: function(flags_r) {
											let flag_map = {};
											if (flags_r.message) {
												flags_r.message.forEach(item => {
													flag_map[item.employee] = {
														is_bank_entry_created: item.za_is_bank_entry_created || 0,
														is_company_contribution_created: item.za_is_company_contribution_created || 0
													};
												});
											}
											
											// Now fetch bank account currency for each bank account
											let bank_accounts = [];
											r.message.forEach(emp => {
												if (emp.za_payroll_payable_bank_account) {
													if (!bank_accounts.includes(emp.za_payroll_payable_bank_account)) {
														bank_accounts.push(emp.za_payroll_payable_bank_account);
													}
												}
											});
											
											if (bank_accounts.length === 0) {
												frappe.msgprint({
													message: __("No employees have bank accounts configured. Please configure bank accounts on Employee records."),
													indicator: "orange",
													title: __("Bank Account Required")
												});
												return;
											}
											
											frappe.call({
												method: "za_local.overrides.payroll_entry.get_bank_account_currencies",
												args: {
													bank_accounts: bank_accounts,
													company: frm.doc.company,
												},
												callback: function(bank_r) {
													let bank_map = {};
													if (bank_r.message) {
														bank_r.message.forEach(bank => {
															bank_map[bank.name] = bank.account_currency || frappe.get_doc(":Company", frm.doc.company).default_currency;
														});
													}
													
													// Build account_map
													let account_map = {};
													r.message.forEach((emp) => {
														if (emp.za_payroll_payable_bank_account) {
															let flags = flag_map[emp.name] || { is_bank_entry_created: 0, is_company_contribution_created: 0 };
															let account_currency = bank_map[emp.za_payroll_payable_bank_account] || frappe.get_doc(":Company", frm.doc.company).default_currency;
															
															if (emp.za_payroll_payable_bank_account in account_map) {
																account_map[emp.za_payroll_payable_bank_account].push({
																	employee: emp.name,
																	employee_name: emp.employee_name,
																	account_currency: account_currency,
																	is_bank_entry_created: flags.is_bank_entry_created,
																	is_company_contribution_created: flags.is_company_contribution_created,
																});
															} else {
																account_map[emp.za_payroll_payable_bank_account] = [
																	{
																		employee: emp.name,
																		employee_name: emp.employee_name,
																		account_currency: account_currency,
																		is_bank_entry_created: flags.is_bank_entry_created,
																		is_company_contribution_created: flags.is_company_contribution_created,
																	},
																];
															}
														}
													});
													
													// Continue with dialog creation
													show_bank_entry_dialog(frm, account_map);
												}
											});
										}
									});
								}
							}
						});
					})
					.addClass("btn-primary");
			}
		}
	},
});

function show_bank_entry_dialog(frm, account_map) {
	let field_list = [];
	let company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
	
	for (let account in account_map) {
		let is_read_only = 0;
		if (
			account_map[account].length ==
			account_map[account].filter(
				(item) =>
					item.is_bank_entry_created &&
					item.is_company_contribution_created
			).length
		) {
			is_read_only = 1;
		}
		field_list.push({
			label: account,
			fieldname: account,
			fieldtype: "Check",
			read_only: is_read_only,
			change: () => {
				$(".employee-list").empty();
				for (let account in account_map) {
					if (d.get_value(account)) {
						$(".employee-list").append(`
							<div class="col-sm-12" style="border-bottom: 1px solid #d4d4d4;"><b>Employees paid with <a href="/app/bank-account/${account}">${account}</a></b></div>
						`);
						account_map[account].forEach((row) => {
							let is_disabled = false;
							if (
								!(
									row.is_bank_entry_created ||
									row.is_company_contribution_created
								)
							) {
								is_disabled = true;
							}
							$(`.${row.employee}-col`).remove();

							$(".employee-list").append(`
								<div class="col-sm-6 ${row.employee}-col" style="border-bottom: 1px solid #d4d4d4;"><input type="checkbox" class="employee-checkbox" account="${account}" employee="${row.employee}" checked ${!is_disabled?"":"disabled"}><a href="/app/employee/${row.employee}" target="_blank" >${row.employee}: ${row.employee_name}</a></div>
							`);
						});
					}
				}
			},
		});
		field_list.push({
			fieldtype: "Column Break"
		});
		field_list.push({
			label: "Payment Date" + " <small>(" + account + ")</small>",
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
					callback: function (r, rt) {
						if (r.message) {
							d.set_value(account + "_ex_rate", r.message);
						}
					},
				});
			},
		});
		field_list.push({
			fieldtype: "Column Break"
		});
		field_list.push({
			label: "Exchange Rate" + " <small>(" + account + ")</small>",
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
		title: "Enter details",
		fields: field_list,
		size: "extra-large",
		primary_action_label: "Create Bank Entry",
		primary_action(values) {
			let account_emp_map = {};
			$(".employee-checkbox:checkbox:checked").each((i, e) => {
				const acc = $(e).attr("account");
				const emp = $(e).attr("employee");
				if (
					acc in account_emp_map &&
					!account_emp_map[acc]["employees"].includes(emp)
				) {
					account_emp_map[acc]["employees"].push(emp);
				} else {
					account_emp_map[acc] = {};
					account_emp_map[acc]["employees"] = [emp];
				}
			});
			for (const account in account_emp_map) {
				if (!values[account + "_date"]) {
					frappe.throw(`Posting date for ${account} is mandatory`);
				}

				if (!values[account + "_ex_rate"]){
					frappe.throw("Exchange rate cannot be zero")
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
				callback: function (r) {
					if (r.exc) {
						frappe.msgprint({
							message: r.exc,
							indicator: "red",
							title: __("Error")
						});
					} else {
						frappe.set_route("List", "Journal Entry", {
							"Journal Entry Account.reference_name": frm.doc.name,
						});
					}
				},
				freeze: true,
				freeze_message: __("Creating Payment Entries......"),
			});
			d.hide();
			frm.refresh();
		},
	});

	d.show();
}
