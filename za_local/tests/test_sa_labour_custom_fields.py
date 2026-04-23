import frappe
from frappe.tests.utils import FrappeTestCase


class TestSALabourCustomFields(FrappeTestCase):
	def test_employee_employment_equity_fields_exist(self):
		meta = frappe.get_meta("Employee")
		fieldnames = {field.fieldname for field in meta.fields if field.fieldname}

		expected = {
			"za_race",
			"za_occupational_level",
			"za_is_disabled",
		}

		self.assertTrue(
			expected.issubset(fieldnames),
			msg=f"Missing Employee employment equity fields: {sorted(expected - fieldnames)}",
		)
