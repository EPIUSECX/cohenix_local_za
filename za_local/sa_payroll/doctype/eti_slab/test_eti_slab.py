import json
from pathlib import Path

import frappe

from za_local.sa_payroll.doctype.irp5_certificate.irp5_certificate import IRP5Certificate
from za_local.tests.compat import UnitTestCase


class TestETISlab(UnitTestCase):
	def test_seeded_eti_slabs_match_sars_2025_table(self):
		fixture_path = Path(frappe.get_app_path("za_local", "sa_setup", "data", "eti_slabs_2025.json"))
		slabs = {row["title"]: row for row in json.loads(fixture_path.read_text())}

		first_period = slabs["ETI 2025-2026 First 12 Months"]
		second_period = slabs["ETI 2025-2026 Second 12 Months"]

		self.assertEqual("2025-04-01", first_period["start_date"])
		self.assertEqual("2025-04-01", second_period["start_date"])
		self.assertEqual(7499.99, first_period["eti_slab_details"][2]["to_amount"])
		self.assertEqual(7500, first_period["eti_slab_details"][3]["from_amount"])
		self.assertEqual(1500, first_period["eti_slab_details"][1]["eti_amount"])
		self.assertEqual(75, first_period["eti_slab_details"][2]["percentage"])
		self.assertEqual(750, second_period["eti_slab_details"][1]["eti_amount"])
		self.assertEqual(37.5, second_period["eti_slab_details"][2]["percentage"])

	def test_irp5_fallback_eti_formula_matches_sars_2025_table(self):
		calculate = IRP5Certificate.calculate_eti_amount

		self.assertEqual(1200, calculate(None, 2000, True))
		self.assertEqual(1500, calculate(None, 2500, True))
		self.assertEqual(1500, calculate(None, 5499.99, True))
		self.assertEqual(750, calculate(None, 6500, True))
		self.assertEqual(0, calculate(None, 7500, True))

		self.assertEqual(600, calculate(None, 2000, False))
		self.assertEqual(750, calculate(None, 2500, False))
		self.assertEqual(375, calculate(None, 6500, False))
		self.assertEqual(0, calculate(None, 7500, False))
