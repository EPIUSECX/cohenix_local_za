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
		{ fieldtype: "Section Break", label: __("Feature Selection") },
		{
			fieldname: "za_enable_hrms_payroll",
			label: __("Enable ZA HR/Payroll Localisation (requires HRMS)"),
			fieldtype: "Check",
			default: 0,
			description: __("Enable payroll processing, leave management, and employee features. Requires Frappe HRMS app to be installed. If unchecked, only tax/VAT/COIDA features will be available.")
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
		// Check if HRMS is installed to pre-select HRMS option
		frappe.call({
			method: "za_local.utils.hrms_detection.is_hrms_installed",
			callback: function(r) {
				if (r.message) {
					const hrmsField = slide.get_field("za_enable_hrms_payroll");
					if (hrmsField) {
						hrmsField.set_value(1);
					}
				}
			}
		});
		
		// Set default values for non-HRMS features (always available)
		slide.get_field("za_load_tax_slabs").set_value(1);
		slide.get_field("za_load_tax_rebates").set_value(1);
		slide.get_field("za_load_medical_credits").set_value(1);
		slide.get_field("za_load_business_trip_regions").set_value(1);
		
		// Setup conditional visibility for HRMS-dependent fields
		const hrmsCheckbox = slide.get_field("za_enable_hrms_payroll");
		const hrmsFields = [
			"za_load_salary_components",
			"za_load_earnings_components",
			"za_load_holiday_list"
		];
		
		function toggleHrmsFields() {
			const enabled = hrmsCheckbox.get_value();
			hrmsFields.forEach(function(fieldname) {
				const field = slide.get_field(fieldname);
				if (field) {
					field.df.hidden = !enabled;
					field.refresh();
					if (!enabled) {
						field.set_value(0);
					} else {
						field.set_value(1);
					}
				}
			});
		}
		
		hrmsCheckbox.$input.on("change", toggleHrmsFields);
		toggleHrmsFields(); // Initial state
	}
};

