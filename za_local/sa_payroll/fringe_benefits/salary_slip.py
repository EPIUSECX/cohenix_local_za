"""Salary Slip extension for South African fringe benefits."""

from za_local.sa_payroll.fringe_benefits.service import apply_fringe_benefits_to_salary_slip


class FringeBenefitSalarySlipMixin:
	def calculate_component_amounts(self, component_type):
		super().calculate_component_amounts(component_type)
		if component_type == "earnings":
			apply_fringe_benefits_to_salary_slip(self)
