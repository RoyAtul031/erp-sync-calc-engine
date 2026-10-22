from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
    CalculationRun,
)
from apps.data_warehouse.models import Facility, FacilityUtilityRecord
from apps.calculation_engine.engine import DeterministicCalculationEngine


class FormulaCustomizationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.framework = ComplianceFramework.objects.create(code="GHG_CUSTOM", name="Custom Framework")
        self.methodology = CalculationMethodology.objects.create(
            name="Custom Methodology",
            framework=self.framework,
            is_active=True,
        )
        self.rule = FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="SCOPE_1_DIESEL",
            name="Diesel Scope 1",
            expression="(consumption * emission_factor) / 1000.0",
            output_unit="tCO2e",
        )
        EmissionFactor.objects.create(
            framework=self.framework,
            category="SCOPE_1_COMBUSTION",
            activity_key="DIESEL_LITER",
            display_name="Diesel",
            factor_value=Decimal("2.500"),
            factor_unit="kgCO2e / L",
            effective_year=2024,
        )
        self.facility = Facility.objects.create(code="FAC-01", name="Plant 1")
        self.record = FacilityUtilityRecord.objects.create(
            facility=self.facility,
            utility_type="DIESEL_GENERATOR",
            start_date="2024-01-01",
            end_date="2024-01-31",
            consumption_value=Decimal("1000.0"),
            consumption_unit="LITERS",
        )

    def test_formula_customization_reflects_in_calculation(self):
        # 1. Base run: (1000 * 2.5) / 1000.0 = 2.5 tCO2e
        engine = DeterministicCalculationEngine(self.methodology)
        run1 = CalculationRun.objects.create(methodology=self.methodology)
        calc1 = engine.calculate_utility_record(self.record, run1)
        self.assertEqual(float(calc1.result_value), 2.5)

        # 2. Modify formula rule in DB (e.g., adding 10% safety buffer: (consumption * emission_factor * 1.1) / 1000.0)
        self.rule.expression = "(consumption * emission_factor * 1.1) / 1000.0"
        self.rule.save()

        # 3. Next run: (1000 * 2.5 * 1.1) / 1000.0 = 2.75 tCO2e
        engine2 = DeterministicCalculationEngine(self.methodology)
        run2 = CalculationRun.objects.create(methodology=self.methodology)
        calc2 = engine2.calculate_utility_record(self.record, run2)
        self.assertEqual(float(calc2.result_value), 2.75)

    def test_formula_simulator_api(self):
        response = self.client.post(
            "/api/calculation/simulate-formula/",
            data={
                "expression": "(consumption * emission_factor) / 1000.0",
                "variables": {"consumption": 5000.0, "emission_factor": 3.0},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_valid"])
        self.assertEqual(response.data["result"], 15.0)
