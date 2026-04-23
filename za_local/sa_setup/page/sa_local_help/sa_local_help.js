frappe.pages["sa-local-help"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("SA Local Help"),
		single_column: true,
	});

	frappe.breadcrumbs.add("SA Localisation");
	$(frappe.render_template("sa_local_help")).appendTo(page.body.addClass("no-border"));
};
