frappe.query_reports["EMP201 Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: "\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember\nJanuary\nFebruary",
		},
		{
			fieldname: "from_date",
			label: __("Posting Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Posting Date To"),
			fieldtype: "Date",
		},
	],
};
