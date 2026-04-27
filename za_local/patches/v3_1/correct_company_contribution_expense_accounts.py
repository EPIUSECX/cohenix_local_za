import frappe

COMPONENT_EXPENSE_ACCOUNTS = {
	"UIF Employer Contribution": "UIF Employer Expense",
	"SDL Contribution": "SDL Expense",
	"Pension Fund Employer Contribution": "Pension Fund Employer Expense",
	"Medical Aid Employer Contribution": "Medical Aid Employer Expense",
}


def execute():
	companies = frappe.get_all("Company", pluck="name")
	for company in companies:
		ensure_expense_accounts(company)
		repair_component_accounts(company)


def ensure_expense_accounts(company):
	from za_local.accounts.setup_chart import load_sa_chart_of_accounts

	load_sa_chart_of_accounts(company)


def repair_component_accounts(company):
	for component, account_name in COMPONENT_EXPENSE_ACCOUNTS.items():
		if not frappe.db.exists("Salary Component", component):
			continue

		account = frappe.db.get_value(
			"Account",
			{"company": company, "account_name": account_name},
			"name",
		)
		if not account:
			continue

		row_name = frappe.db.get_value(
			"Salary Component Account",
			{"parent": component, "company": company},
			"name",
		)
		if row_name:
			frappe.db.set_value("Salary Component Account", row_name, "account", account)
			continue

		doc = frappe.get_doc("Salary Component", component)
		doc.append("accounts", {"company": company, "account": account})
		doc.save(ignore_permissions=True)
