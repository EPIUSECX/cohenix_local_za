from unittest.mock import patch

import frappe

from za_local.tests.compat import UnitTestCase


class TestEmployeePrivateBenefit(UnitTestCase):
	def test_doctype_metadata(self):
		meta = frappe.get_meta("Employee Private Benefit")

		self.assertEqual(meta.autoname, "naming_series:")
		self.assertTrue(meta.get_field("employee").reqd)
		self.assertEqual(meta.get_field("naming_series").options, "RA-.YYYY.-")

	def test_medical_membership_requires_effective_date(self):
		doc = frappe.new_doc("Employee Private Benefit")
		doc.private_medical_aid = 2_000

		with self.assertRaises(frappe.ValidationError):
			doc.run_method("validate")

	def test_membership_end_cannot_precede_start(self):
		doc = frappe.new_doc("Employee Private Benefit")
		doc.effective_from = "2026-03-01"
		doc.to = "2026-02-28"

		with self.assertRaises(frappe.ValidationError):
			doc.run_method("validate")

	def test_medical_dependants_cannot_be_negative(self):
		doc = frappe.new_doc("Employee Private Benefit")
		doc.medical_aid_dependant = -1

		with self.assertRaises(frappe.ValidationError):
			doc.run_method("validate")

	@patch(
		"za_local.sa_payroll.doctype.employee_private_benefit.employee_private_benefit.frappe.get_all"
	)
	def test_overlapping_active_benefit_period_is_rejected(self, get_all):
		get_all.return_value = [
			frappe._dict(name="RA-2026-0001", effective_from="2026-01-01", to=None)
		]
		doc = frappe.new_doc("Employee Private Benefit")
		doc.employee = "EMP-1"
		doc.effective_from = "2026-06-01"
		doc.to = "2026-12-31"

		with self.assertRaises(frappe.ValidationError):
			doc.run_method("validate")

		self.assertEqual(get_all.call_args.kwargs["filters"][0], ["employee", "=", "EMP-1"])

	@patch(
		"za_local.sa_payroll.doctype.employee_private_benefit.employee_private_benefit.frappe.get_all",
		return_value=[],
	)
	def test_non_overlapping_active_benefit_period_is_allowed(self, _get_all):
		doc = frappe.new_doc("Employee Private Benefit")
		doc.employee = "EMP-1"
		doc.effective_from = "2026-06-01"
		doc.to = "2026-12-31"

		doc.run_method("validate")
