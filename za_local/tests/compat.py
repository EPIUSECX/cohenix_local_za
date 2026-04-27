from unittest import TestCase

try:
	from frappe.tests import UnitTestCase
except ImportError:
	UnitTestCase = TestCase
