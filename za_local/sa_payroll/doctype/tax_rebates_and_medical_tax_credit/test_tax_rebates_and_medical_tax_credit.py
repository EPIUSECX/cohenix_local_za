import frappe

from za_local.tests.compat import UnitTestCase


class TestTaxRebatesandMedicalTaxCredit(UnitTestCase):
	def test_singleton_doctype_metadata(self):
		meta = frappe.get_meta("Tax Rebates and Medical Tax Credit")

		self.assertTrue(meta.issingle)
		self.assertEqual(meta.get_field("tax_rebates_rate").options, "Tax Rebates Rate")
		self.assertEqual(meta.get_field("medical_tax_credit").options, "Medical Tax Credit Rate")
