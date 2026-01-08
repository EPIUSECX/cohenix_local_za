frappe.provide("za_local.setup");

frappe.setup.on("before_load", function () {
	// Register slide; visibility is controlled by its before_show hook (country == South Africa)
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
	before_show: function () {
		// Show this slide when:
		// 1. Country is explicitly South Africa, OR
		// 2. Country is not set yet (fresh install) - za_local should run for SA localization
		const country =
			(frappe.wizard && frappe.wizard.values && frappe.wizard.values.country) ||
			frappe.defaults.get_default("country");
		
		// Show if country is South Africa or not set (fresh install)
		// This ensures the wizard runs even if country isn't selected yet
		return country === "South Africa" || !country;
	},

	onload: function(slide) {
		const hrmsCheckbox = slide.get_field("za_enable_hrms_payroll");
		const hrmsFields = [
			"za_load_salary_components",
			"za_load_earnings_components",
			"za_load_holiday_list",
			"za_load_tax_slabs",
			"za_load_tax_rebates",
			"za_load_medical_credits"
		];
		
		function setFieldState(fieldname, checked, enabled) {
			const field = slide.get_field(fieldname);
			if (!field) return;
			
			field.set_value(checked ? 1 : 0);
			
			// Disable input when not applicable (e.g. HRMS not installed)
			if (field.df) {
				field.df.read_only = enabled ? 0 : 1;
				field.df.hidden = 0;
			}
			
			field.refresh_input && field.refresh_input();
		}
		
		function applyHrmsState(enabled) {
			// Parent checkbox always enabled visually, but can be read-only when HRMS missing
			setFieldState("za_enable_hrms_payroll", enabled, true);
			hrmsFields.forEach(function (fieldname) {
				setFieldState(fieldname, enabled, enabled);
			});
		}
		
		// Non‑HRMS features are always available and should default ON
		setFieldState("za_load_business_trip_regions", true, true);
		
		// Check if HRMS is installed and configure HR‑dependent fields accordingly
		let hrmsAvailable = false;
		frappe.call({
			method: "za_local.utils.hrms_detection.is_hrms_installed",
			callback: function (r) {
				hrmsAvailable = !!r.message;
				
				if (hrmsAvailable) {
					// HRMS present: enable HR/Payroll and all dependent options by default
					applyHrmsState(true);
				} else {
					// HRMS missing: leave HR options off and make them read‑only
					applyHrmsState(false);
					if (hrmsCheckbox && hrmsCheckbox.df) {
						hrmsCheckbox.df.read_only = 1;
						hrmsCheckbox.refresh_input && hrmsCheckbox.refresh_input();
					}
				}
			}
		});
		
		// When HRMS is available, allow user to toggle HR/Payroll and its dependent fields
		if (hrmsCheckbox && hrmsCheckbox.$input) {
			hrmsCheckbox.$input.on("change", function () {
				if (!hrmsAvailable) {
					// If HRMS is not installed, force it back to off
					applyHrmsState(false);
				} else {
					applyHrmsState(hrmsCheckbox.get_value());
				}
			});
		}
	}
};

