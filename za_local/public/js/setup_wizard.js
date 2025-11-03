frappe.provide("za_local.setup");

frappe.setup.on("before_load", function () {
	// Always add slide when za_local is installed
	// If user has za_local, they're running a SA company
	frappe.setup.add_slide(za_local.setup.za_localization_slide);
});

za_local.setup.za_localization_slide = {
	name: "za_localization",
	title: __("South African Localization"),
	icon: "fa fa-flag",
	
	fields: [
		{
			fieldname: "za_intro",
			fieldtype: "HTML",
			options: `<h3>${__("Configure South African Compliance")}</h3>
				<p>${__("Select which default configurations to load. All can be customized later.")}</p>`
		},
		{ fieldtype: "Section Break", label: __("Salary Components") },
		{
			fieldname: "za_load_salary_components",
			label: __("Create Default Salary Components"),
			fieldtype: "Check",
			default: 1,
			description: __("PAYE, UIF (Employee & Employer), SDL")
		},
		{
			fieldname: "za_load_earnings_components",
			label: __("Create Earnings Components"),
			fieldtype: "Check",
			default: 1,
			description: __("Basic Salary, Housing, Transport, Bonuses, etc.")
		},
		{ fieldtype: "Section Break", label: __("Tax Configuration") },
		{
			fieldname: "za_load_tax_slabs",
			label: __("Load 2024-2025 Tax Slabs"),
			fieldtype: "Check",
			default: 1,
			description: __("7 SARS income tax brackets (18% - 45%)")
		},
		{
			fieldname: "za_load_tax_rebates",
			label: __("Load Tax Rebates"),
			fieldtype: "Check",
			default: 1,
			description: __("Primary, Secondary, Tertiary rebates")
		},
		{
			fieldname: "za_load_medical_credits",
			label: __("Load Medical Tax Credits"),
			fieldtype: "Check",
			default: 1,
			description: __("Main member and dependant credits")
		},
		{
			fieldname: "za_load_holiday_list",
			label: __("Load South African Holiday List"),
			fieldtype: "Check",
			default: 1,
			description: __("2024 and 2025 public holidays")
		},
		{ fieldtype: "Section Break", label: __("Master Data") },
		{
			fieldname: "za_load_business_trip_regions",
			label: __("Load Business Trip Regions"),
			fieldtype: "Check",
			default: 1,
			description: __("16 SA cities + international rates")
		}
	],
	
	onload: function(slide) {
		// Set default values
		slide.get_field("za_load_salary_components").set_value(1);
		slide.get_field("za_load_earnings_components").set_value(1);
		slide.get_field("za_load_tax_slabs").set_value(1);
		slide.get_field("za_load_tax_rebates").set_value(1);
		slide.get_field("za_load_medical_credits").set_value(1);
		slide.get_field("za_load_holiday_list").set_value(1);
		slide.get_field("za_load_business_trip_regions").set_value(1);
	}
};

