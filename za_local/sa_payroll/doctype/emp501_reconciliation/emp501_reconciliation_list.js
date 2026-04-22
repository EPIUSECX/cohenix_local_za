frappe.listview_settings['EMP501 Reconciliation'] = {
    onload: function(listview) {
        // This is a workaround for a stubborn routing issue.
        // If the user is trying to create a new document, but is redirected to the list view,
        // this script will detect that and force the route to the new document form.
        if (frappe.get_route() && frappe.get_route()[1] === 'new-emp501-reconciliation') {
            frappe.set_route('Form', 'EMP501 Reconciliation', 'new-emp501-reconciliation');
        }
    }
};
