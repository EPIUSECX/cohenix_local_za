frappe.ui.form.on('Salary Structure', {
	onload: function(frm) {
		frm.fields_dict['company_contribution'].grid.get_field('salary_component').get_query = function(doc){
			return{
				filters:{
					"type": "Company Contribution"
				}
			}
		}
	}
})