from decimal import Decimal
from django.test import TestCase
from apps.calculation_engine.engine import SafeMathEvaluator, DeterministicCalculationEngine
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
    CalculationRun,
)
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord


class SafeMathEvaluatorTestCase(TestCase):
    def test_standard_math_evaluation(self):
        expr = "(consumption * emission_factor) / 1000.0"
        vars_dict = {"consumption": 10000.0, "emission_factor": 2.5}
        result, evaluated_str = SafeMathEvaluator.evaluate(expr, vars_dict)
        self.assertEqual(result, 25.0)
        self.assertIn("10000.0", evaluated_str)

    def test_division_by_zero_handling(self):
        expr = "(female_headcount / total_headcount) * 100.0"
        vars_dict = {"female_headcount": 50.0, "total_headcount": 0.0}
        result, _ = SafeMathEvaluator.evaluate(expr, vars_dict)
        self.assertEqual(result, 0.0)

    def test_rejects_unsafe_code(self):
        unsafe_expr = "__import__('os').system('echo pwned')"
        with self.assertRaises(ValueError):
            SafeMathEvaluator.evaluate(unsafe_expr, {})


class DeterministicCalculationEngineTestCase(TestCase):
    def setUp(self):
        self.framework = ComplianceFramework.objects.create(
            code="GHG_TEST",
            name="GHG Test Framework",
        )
        self.factor_diesel = EmissionFactor.objects.create(
            framework=self.framework,
            category="SCOPE_1_COMBUSTION",
            activity_key="DIESEL_LITER",
            display_name="Diesel",
            factor_value=Decimal("2.687"),
            factor_unit="kgCO2e / L",
            source_citation="Test EPA Hub",
            effective_year=2024,
        )
        self.factor_ercot = EmissionFactor.objects.create(
            framework=self.framework,
            category="SCOPE_2_LOCATION_GRID",
            activity_key="GRID_US_ERCOT",
            display_name="US ERCOT Grid",
            factor_value=Decimal("0.400"),
            factor_unit="kgCO2e / kWh",
            source_citation="eGRID Test",
            effective_year=2024,
        )

        self.methodology = CalculationMethodology.objects.create(
            name="Test Methodology",
            framework=self.framework,
            is_active=True,
        )
        FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="SCOPE_1_DIESEL",
            name="Diesel Scope 1",
            expression="(consumption * emission_factor) / 1000.0",
            output_unit="tCO2e",
        )
        FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="SCOPE_2_LOCATION",
            name="Grid Scope 2 Location",
            expression="(consumption * emission_factor) / 1000.0",
            output_unit="tCO2e",
        )
        FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="SCOPE_2_MARKET",
            name="Scope 2 Market",
            expression="(consumption * emission_factor) / 1000.0",
            output_unit="tCO2e",
        )
        FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="GENDER_DIVERSITY_PCT",
            name="Diversity",
            expression="(female_headcount / total_headcount) * 100.0",
            output_unit="%",
        )
        FormulaRule.objects.create(
            methodology=self.methodology,
            rule_code="LTIFR_SAFETY",
            name="LTIFR",
            expression="(lost_time_injuries * 1000000.0) / total_hours_worked",
            output_unit="injuries_per_million_hours",
        )

        self.facility = Facility.objects.create(
            code="PLANT-TX",
            name="Texas Facility",
            grid_subregion="US_ERCOT",
        )

    def test_scope_1_calculation(self):
        # 10,000 Liters of Diesel -> 10000 * 2.687 / 1000 = 26.87 tCO2e
        u_rec = FacilityUtilityRecord.objects.create(
            facility=self.facility,
            utility_type="DIESEL_GENERATOR",
            scope_category="SCOPE_1",
            start_date="2024-01-01",
            end_date="2024-01-31",
            consumption_value=Decimal("10000.0"),
            consumption_unit="LITERS",
        )

        engine = DeterministicCalculationEngine(self.methodology)
        run = CalculationRun.objects.create(methodology=self.methodology)
        calc = engine.calculate_utility_record(u_rec, run)

        self.assertEqual(float(calc.result_value), 26.87)
        self.assertEqual(calc.result_unit, "tCO2e")
        self.assertIn("Test EPA Hub", calc.calculation_trace["emission_factor_applied"]["source_citation"])

    def test_scope_2_market_based_zero_for_renewables(self):
        # 50,000 kWh backed by Green Renewable Certificates (REC)
        u_rec = FacilityUtilityRecord.objects.create(
            facility=self.facility,
            utility_type="ELECTRICITY_PURCHASED",
            scope_category="SCOPE_2_MARKET",
            start_date="2024-01-01",
            end_date="2024-01-31",
            consumption_value=Decimal("50000.0"),
            consumption_unit="KWH",
            is_renewable_backed=True,
        )

        engine = DeterministicCalculationEngine(self.methodology)
        run = CalculationRun.objects.create(methodology=self.methodology)
        calc = engine.calculate_utility_record(u_rec, run)

        self.assertEqual(float(calc.result_value), 0.0)
        self.assertEqual(calc.rule_code, "SCOPE_2_MARKET")

    def test_social_workforce_kpi_calculation(self):
        w_rec = WorkforceMetricRecord.objects.create(
            facility=self.facility,
            period_start="2024-01-01",
            period_end="2024-01-31",
            total_headcount=1000,
            female_headcount=450,
            lost_time_injuries=2,
            total_hours_worked=Decimal("500000.0"),
        )

        engine = DeterministicCalculationEngine(self.methodology)
        run = CalculationRun.objects.create(methodology=self.methodology)
        calcs = engine.calculate_workforce_record(w_rec, run)

        div_calc = next(c for c in calcs if c.rule_code == "GENDER_DIVERSITY_PCT")
        self.assertEqual(float(div_calc.result_value), 45.0)

        safety_calc = next(c for c in calcs if c.rule_code == "LTIFR_SAFETY")
        # (2 * 1,000,000) / 500,000 = 4.0
        self.assertEqual(float(safety_calc.result_value), 4.0)

    def test_csv_export_endpoint(self):
        engine = DeterministicCalculationEngine(self.methodology)
        run = engine.run_full_calculation(initiated_by="TEST_RUN")
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.get(f"/api/calculation/runs/{run.id}/export-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Facility Code", response.content.decode("utf-8"))
