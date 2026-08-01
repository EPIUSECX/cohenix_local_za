"""Backfill missing company-scoped South African payroll tax masters."""

from za_local.sa_setup.statutory_setup import ensure_all_company_tax_configuration


def execute():
	ensure_all_company_tax_configuration()
