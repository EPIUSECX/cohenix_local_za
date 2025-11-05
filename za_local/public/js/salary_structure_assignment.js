frappe.ui.form.on('Salary Structure Assignment', {
	onload: function(frm) {
		// Hide Flexible Benefits section - not used in South African payroll
		// Flexible benefits are typically fixed deductions or company contributions, not claim-based
		// This feature is for cafeteria-style benefit plans (common in US/UK), not SA payroll
		hide_flexible_benefits_section(frm);
		
		// Set up MutationObserver to watch for dynamically added elements
		setup_flexible_benefits_observer(frm);
	},
	refresh: function(frm) {
		// Ensure Flexible Benefits section stays hidden on refresh
		hide_flexible_benefits_section(frm);
	}
})

function hide_flexible_benefits_section(frm) {
	// Method 1: Use Frappe's built-in toggle_display (hides the fields)
	if (frm.fields_dict['employee_benefits']) {
		frm.toggle_display('employee_benefits', false);
	}
	
	if (frm.fields_dict['employee_benefits_section']) {
		frm.toggle_display('employee_benefits_section', false);
	}
	
	if (frm.fields_dict['max_benefits']) {
		frm.toggle_display('max_benefits', false);
	}
	
	// Method 2: Aggressively hide the entire Flexible Benefits section
	// Use multiple timeouts to catch different rendering phases
	var hide_attempts = [0, 50, 100, 200, 300, 500, 1000, 2000];
	
	hide_attempts.forEach(function(delay) {
		setTimeout(function() {
			// Find ALL form sections
			if (frm.layout && frm.layout.wrapper) {
				frm.layout.wrapper.find('.form-section').each(function() {
					var $section = $(this);
					
					// Get section label - try multiple selectors
					var section_label = '';
					var $label = $section.find('.section-head .section-title, .section-head .label, h6.section-title, .section-title, .label-section-title');
					if ($label.length) {
						section_label = $label.first().text().trim().toLowerCase();
					} else {
						// Fallback: get all text and check
						section_label = $section.text().trim().toLowerCase();
					}
					
					// Check if this section contains employee_benefits field (Flexible Benefits child table)
					var has_flexible_benefit = $section.find('[data-fieldname="employee_benefits"]').length > 0;
					
					// Check if this section contains max_benefits field
					var has_max_benefits = $section.find('[data-fieldname="max_benefits"]').length > 0;
					
					// Check if this is the employee_benefits_section
					var is_benefits_section = $section.find('[data-fieldname="employee_benefits_section"]').length > 0;
					
					// Hide if:
					// 1. Section label is "Employee Benefits" OR "Flexible Benefits" OR
					// 2. Section contains employee_benefits field OR
					// 3. Section contains max_benefits field OR
					// 4. This is the employee_benefits_section
					var should_hide = false;
					
					if (section_label === 'employee benefits' || 
					    section_label === 'flexible benefits' ||
					    section_label.includes('flexible benefit') ||
					    section_label.includes('employee benefit') ||
					    has_flexible_benefit ||
					    has_max_benefits ||
					    is_benefits_section) {
						should_hide = true;
					}
					
					if (should_hide) {
						$section.hide();
						$section.css('display', 'none !important');
						$section.css('visibility', 'hidden');
						$section.addClass('za-hidden-flexible-benefits');
					}
				});
				
				// Also hide by fieldname directly (more aggressive)
				frm.layout.wrapper.find('[data-fieldname="employee_benefits"]').each(function() {
					var $field = $(this);
					var $parent_section = $field.closest('.form-section');
					
					$field.hide();
					$field.css('display', 'none !important');
					if ($parent_section.length) {
						$parent_section.hide();
						$parent_section.css('display', 'none !important');
						$parent_section.addClass('za-hidden-flexible-benefits');
					}
				});
				
				frm.layout.wrapper.find('[data-fieldname="employee_benefits_section"]').each(function() {
					var $field = $(this);
					var $parent_section = $field.closest('.form-section');
					
					$field.hide();
					$field.css('display', 'none !important');
					if ($parent_section.length) {
						$parent_section.hide();
						$parent_section.css('display', 'none !important');
						$parent_section.addClass('za-hidden-flexible-benefits');
					}
				});
				
				frm.layout.wrapper.find('[data-fieldname="max_benefits"]').each(function() {
					var $field = $(this);
					var $parent_section = $field.closest('.form-section');
					
					$field.hide();
					$field.css('display', 'none !important');
					if ($parent_section.length) {
						$parent_section.hide();
						$parent_section.css('display', 'none !important');
						$parent_section.addClass('za-hidden-flexible-benefits');
					}
				});
			}
		}, delay);
	});
}

function setup_flexible_benefits_observer(frm) {
	// Use MutationObserver to watch for dynamically added elements
	if (frm.layout && frm.layout.wrapper && window.MutationObserver) {
		var observer = new MutationObserver(function(mutations) {
			hide_flexible_benefits_section(frm);
		});
		
		observer.observe(frm.layout.wrapper[0], {
			childList: true,
			subtree: true
		});
		
		// Store observer on form for cleanup if needed
		frm._flexible_benefits_observer = observer;
	}
}

