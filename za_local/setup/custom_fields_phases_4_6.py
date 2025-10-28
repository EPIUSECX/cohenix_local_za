"""
Phase 4-6 Custom Fields Addition
Add these fields to custom_fields.py
"""

PHASE_4_6_CUSTOM_FIELDS = {
	# Employee Separation
	"Employee Separation": [
		{
			"fieldname": "za_termination_section",
			"label": "SA Termination Calculations",
			"fieldtype": "Section Break",
			"insert_after": "exit_interview_held_on",
			"collapsible": 1
		},
		{
			"fieldname": "za_termination_type",
			"label": "Termination Type",
			"fieldtype": "Select",
			"options": "\nResignation\nDismissal - Misconduct\nDismissal - Operational\nMutual Agreement\nEnd of Contract",
			"insert_after": "za_termination_section"
		},
		{
			"fieldname": "za_notice_period_days",
			"label": "Notice Period (Days)",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "za_termination_type"
		},
		{
			"fieldname": "za_severance_pay",
			"label": "Severance Pay",
			"fieldtype": "Currency",
			"read_only": 1,
			"insert_after": "za_notice_period_days"
		},
		{
			"fieldname": "za_leave_payout",
			"label": "Leave Payout",
			"fieldtype": "Currency",
			"read_only": 1,
			"insert_after": "za_severance_pay"
		}
	],
	
	# Company - Bargaining Council
	"Company": [
		{
			"fieldname": "za_bargaining_council",
			"label": "Bargaining Council",
			"fieldtype": "Link",
			"options": "Bargaining Council",
			"insert_after": "za_seta"
		},
		{
			"fieldname": "za_sectoral_determination",
			"label": "Sectoral Determination",
			"fieldtype": "Select",
			"options": "\nDomestic Workers\nFarm Workers\nPrivate Security\nHospitality\nWholesale/Retail\nOther",
			"insert_after": "za_bargaining_council"
		}
	]
}
