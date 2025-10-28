frappe.ui.form.on('Salary Structure', {
	onload: function(frm) {
		frm.fields_dict['company_contribution'].grid.get_field('salary_component').get_query = function(doc){
			return{
				filters:{
					"is_company_contribution": 1
				}
			}
		}
	}
})