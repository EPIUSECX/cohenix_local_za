import frappe
from frappe.tests.utils import FrappeTestCase


class TestEmployeePrivateBenefit(FrappeTestCase):
	def test_doctype_metadata(self):
		meta = frappe.get_meta("Employee Private Benefit")

		self.assertEqual(meta.autoname, "naming_series:")
		self.assertTrue(meta.get_field("employee").reqd)
		self.assertEqual(meta.get_field("naming_series").options, "RA-.YYYY.-")
