"""BCEA-Compliant Leave Types Setup"""
import frappe
from frappe import _

def setup_sa_leave_types():
    """Create South African BCEA-compliant leave types"""
    
    leave_types = [
        {
            "leave_type_name": "Annual Leave (SA)",
            "max_leaves_allowed": 21,  # 3 weeks per year
            "is_earned_leave": 1,
            "earned_leave_frequency": "Monthly",
            "rounding": 0.5,
            "allow_negative": 0,
            "is_carry_forward": 1,
            "maximum_carry_forwarded_leaves": 21,
            "is_ppl": 0,
            "is_lwp": 0
        },
        {
            "leave_type_name": "Sick Leave (SA)",
            "max_leaves_allowed": 36,  # 36 days per 3-year cycle
            "allow_negative": 0,
            "is_earned_leave": 1,
            "earned_leave_frequency": "Monthly",
            "rounding": 0,
            "is_ppl": 0,
            "is_lwp": 0
        },
        {
            "leave_type_name": "Family Responsibility Leave (SA)",
            "max_leaves_allowed": 3,  # 3 days per year
            "allow_negative": 0,
            "is_ppl": 0,
            "is_lwp": 0
        },
        {
            "leave_type_name": "Maternity Leave (SA)",
            "max_leaves_allowed": 120,  # 4 months
            "allow_negative": 0,
            "is_ppl": 0,
            "is_lwp": 0
        },
        {
            "leave_type_name": "Study Leave (SA)",
            "is_optional_leave": 1,
            "allow_negative": 0
        },
        {
            "leave_type_name": "Unpaid Leave (SA)",
            "is_lwp": 1,
            "allow_negative": 0
        }
    ]
    
    for leave_type in leave_types:
        if not frappe.db.exists("Leave Type", leave_type["leave_type_name"]):
            doc = frappe.get_doc({
                "doctype": "Leave Type",
                **leave_type
            })
            doc.insert(ignore_permissions=True)
            print(f"✓ Created {leave_type['leave_type_name']}")
        else:
            print(f"- {leave_type['leave_type_name']} already exists")
