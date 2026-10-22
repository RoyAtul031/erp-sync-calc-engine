import ast
import operator
import logging
from decimal import Decimal
from typing import Dict, Any, Tuple
from django.utils import timezone
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord
from apps.calculation_engine.models import (
    CalculationMethodology,
    FormulaRule,
    EmissionFactor,
    CalculationRun,
    CalculatedRecord,
)

logger = logging.getLogger(__name__)


class SafeMathEvaluator:
    """
    Deterministic AST-based math evaluator.
    Safely executes user-customized formulas without using Python eval().
    Supports +, -, *, /, **, unary -, and functions: round, min, max, abs.
    """
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    SAFE_FUNCTIONS = {
        "round": round,
        "min": min,
        "max": max,
        "abs": abs,
    }

    @classmethod
    def evaluate(cls, expression: str, variables: Dict[str, float]) -> Tuple[float, str]:
        """
        Parses expression into AST, checks safety, substitutes variables, and computes result.
        Returns (result, resolved_formula_string).
        """
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid math syntax in expression '{expression}': {e}")

        # Substitute variables in text for traceability representation
        resolved_str = expression
        # Sort by length descending so longer variable names don't get partially replaced
        for var_name in sorted(variables.keys(), key=len, reverse=True):
            resolved_str = resolved_str.replace(var_name, str(variables[var_name]))

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return float(node.value)
                raise ValueError(f"Non-numeric literal not allowed: {node.value}")
            elif isinstance(node, ast.Name):
                if node.id in variables:
                    val = variables[node.id]
                    if val is None:
                        val = 0.0
                    return float(val)
                elif node.id in cls.SAFE_FUNCTIONS:
                    return cls.SAFE_FUNCTIONS[node.id]
                raise ValueError(f"Undefined variable in formula: '{node.id}'")
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in cls.SAFE_OPERATORS:
                    raise ValueError(f"Operator {op_type.__name__} is not allowed")
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                if op_type is ast.Div and right == 0:
                    return 0.0  # Handle division by zero deterministically
                return cls.SAFE_OPERATORS[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in cls.SAFE_OPERATORS:
                    raise ValueError(f"Unary operator {op_type.__name__} is not allowed")
                operand = _eval_node(node.operand)
                return cls.SAFE_OPERATORS[op_type](operand)
            elif isinstance(node, ast.Call):
                func = _eval_node(node.func)
                args = [_eval_node(arg) for arg in node.args]
                return func(*args)
            else:
                raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

        result = _eval_node(tree)
        return float(result), resolved_str


class DeterministicCalculationEngine:
    """
    Core deterministic calculation engine for Scope 1, Scope 2, and Social ESG KPIs.
    Guarantees reproducible math, full lineage snapshots, and multi-framework compliance.
    """

    UNIT_CONVERSIONS = {
        # Volume to Liters
        ("GALLONS", "LITERS"): 3.78541,
        ("LITERS", "LITERS"): 1.0,
        # Energy to kWh
        ("MWH", "KWH"): 1000.0,
        ("KWH", "KWH"): 1.0,
        ("THERMS", "KWH"): 29.3001,
        # Volume to m3
        ("M3", "M3"): 1.0,
    }

    def __init__(self, methodology: CalculationMethodology):
        self.methodology = methodology
        self.framework = methodology.framework
        self.rules_cache = {rule.rule_code: rule for rule in methodology.formula_rules.filter(is_active=True)}
        self._load_factors_cache()

    def _load_factors_cache(self):
        """Pre-cache emission factors for the methodology's framework."""
        factors = EmissionFactor.objects.filter(framework=self.framework, is_active=True)
        self.factors = {f.activity_key: f for f in factors}

    def get_emission_factor(self, activity_key: str, fallback_value: float = 1.0) -> Tuple[float, str, str]:
        """Returns (factor_value, factor_unit, source_citation)."""
        factor_obj = self.factors.get(activity_key)
        if factor_obj:
            return float(factor_obj.factor_value), factor_obj.factor_unit, factor_obj.source_citation
        # Fallback to general factor if specific subregion isn't found
        logger.warning(f"Emission factor not found for {activity_key} under {self.framework.code}. Using fallback.")
        return fallback_value, "standard_factor", "Default Standard"

    def normalize_utility_consumption(self, record: FacilityUtilityRecord) -> Tuple[float, str, str]:
        """
        Normalizes consumption units to standard compliance metric base (Liters for fuels, kWh for electricity, m3 for gas).
        Returns (normalized_value, base_unit, trace_log).
        """
        val = float(record.consumption_value)
        unit = record.consumption_unit.upper()

        if record.utility_type in ["DIESEL_GENERATOR", "DIESEL_FLEET"]:
            multiplier = self.UNIT_CONVERSIONS.get((unit, "LITERS"), 1.0)
            norm_val = val * multiplier
            trace = f"{val} {unit} * {multiplier} = {norm_val:.3f} LITERS"
            return norm_val, "LITERS", trace

        elif record.utility_type == "ELECTRICITY_PURCHASED":
            multiplier = self.UNIT_CONVERSIONS.get((unit, "KWH"), 1.0)
            norm_val = val * multiplier
            trace = f"{val} {unit} * {multiplier} = {norm_val:.3f} KWH"
            return norm_val, "KWH", trace

        elif record.utility_type == "NATURAL_GAS":
            norm_val = val
            trace = f"{val} {unit} (standard volumetric base)"
            return norm_val, unit, trace

        return val, unit, f"{val} {unit} (direct)"

    def calculate_utility_record(self, record: FacilityUtilityRecord, run: CalculationRun) -> CalculatedRecord:
        """
        Computes Scope 1 or Scope 2 emissions for a single utility record deterministically.
        """
        norm_val, base_unit, unit_trace = self.normalize_utility_consumption(record)
        facility = record.facility

        # 1. Determine Rule and Emission Factor
        if record.utility_type == "DIESEL_GENERATOR":
            rule_code = "SCOPE_1_DIESEL"
            kpi_category = "SCOPE_1"
            factor_val, factor_unit, citation = self.get_emission_factor("DIESEL_LITER", 2.687)
        elif record.utility_type == "DIESEL_FLEET":
            rule_code = "SCOPE_1_DIESEL_FLEET"
            kpi_category = "SCOPE_1"
            factor_val, factor_unit, citation = self.get_emission_factor("DIESEL_LITER", 2.687)
        elif record.utility_type == "NATURAL_GAS":
            rule_code = "SCOPE_1_NAT_GAS"
            kpi_category = "SCOPE_1"
            factor_val, factor_unit, citation = self.get_emission_factor("NATURAL_GAS_M3", 2.023)
        elif record.utility_type == "ELECTRICITY_PURCHASED":
            # Check market-based vs location-based
            if record.is_renewable_backed:
                rule_code = "SCOPE_2_MARKET"
                kpi_category = "SCOPE_2_MARKET"
                factor_val = 0.0  # Zero emission factor for certified renewables
                factor_unit = "kgCO2e / kWh"
                citation = "Renewable Energy Certificate (REC) Contract / PPA Zero Emission Factor"
            else:
                rule_code = "SCOPE_2_LOCATION"
                kpi_category = "SCOPE_2_LOCATION"
                # Subregion grid factor lookup
                grid_key = f"GRID_{facility.grid_subregion.upper()}"
                factor_val, factor_unit, citation = self.get_emission_factor(grid_key, 0.416)
        else:
            rule_code = "SCOPE_1_DEFAULT"
            kpi_category = "SCOPE_1"
            factor_val, factor_unit, citation = 1.0, "kgCO2e", "Default"

        # 2. Retrieve Formula Rule from Methodology
        rule = self.rules_cache.get(rule_code)
        expression = rule.expression if rule else "(consumption * emission_factor) / 1000.0"
        output_unit = rule.output_unit if rule else "tCO2e"

        # 3. Evaluate Safely
        variables = {
            "consumption": norm_val,
            "emission_factor": factor_val,
            "gwp": 1.0,
        }
        result_num, formula_evaluated = SafeMathEvaluator.evaluate(expression, variables)

        # 4. Construct Verifiable Audit Trace
        calculation_trace = {
            "facility_code": facility.code,
            "facility_name": facility.name,
            "grid_subregion": facility.grid_subregion,
            "raw_input": {
                "consumption_value": float(record.consumption_value),
                "consumption_unit": record.consumption_unit,
                "sap_document_number": record.sap_document_number,
                "meter_identifier": record.meter_identifier,
                "period": f"{record.start_date} to {record.end_date}",
            },
            "unit_normalization_step": unit_trace,
            "emission_factor_applied": {
                "factor_value": factor_val,
                "factor_unit": factor_unit,
                "source_citation": citation,
                "compliance_framework": self.framework.code,
            },
            "formula_evaluated": formula_evaluated,
            "raw_expression": expression,
            "result_tco2e": round(result_num, 4),
            "calculated_at": timezone.now().isoformat(),
        }

        # 5. Persist Granular CalculatedRecord
        return CalculatedRecord(
            run=run,
            facility=facility,
            utility_record=record,
            formula_rule=rule,
            rule_code=rule_code,
            kpi_category=kpi_category,
            inputs_snapshot=variables,
            formula_evaluated=formula_evaluated,
            result_value=Decimal(str(round(result_num, 4))),
            result_unit=output_unit,
            calculation_trace=calculation_trace,
        )

    def calculate_workforce_record(self, record: WorkforceMetricRecord, run: CalculationRun) -> list:
        """
        Computes Social & Safety KPIs (Gender Diversity %, LTIFR).
        """
        records_to_create = []
        facility = record.facility

        # KPI 1: Gender Diversity %
        rule_diversity = self.rules_cache.get("GENDER_DIVERSITY_PCT")
        expr_diversity = rule_diversity.expression if rule_diversity else "(female_headcount / total_headcount) * 100.0"
        vars_diversity = {
            "female_headcount": float(record.female_headcount),
            "total_headcount": float(record.total_headcount) if record.total_headcount > 0 else 1.0,
        }
        res_diversity, eval_diversity = SafeMathEvaluator.evaluate(expr_diversity, vars_diversity)

        trace_diversity = {
            "facility_code": facility.code,
            "period": f"{record.period_start} to {record.period_end}",
            "female_headcount": record.female_headcount,
            "total_headcount": record.total_headcount,
            "formula_evaluated": eval_diversity,
            "result_percentage": round(res_diversity, 2),
            "calculated_at": timezone.now().isoformat(),
        }

        records_to_create.append(
            CalculatedRecord(
                run=run,
                facility=facility,
                workforce_record=record,
                formula_rule=rule_diversity,
                rule_code="GENDER_DIVERSITY_PCT",
                kpi_category="SOCIAL_DIVERSITY",
                inputs_snapshot=vars_diversity,
                formula_evaluated=eval_diversity,
                result_value=Decimal(str(round(res_diversity, 2))),
                result_unit="%",
                calculation_trace=trace_diversity,
            )
        )

        # KPI 2: Lost Time Injury Frequency Rate (LTIFR) = (LTI * 1,000,000) / Exposure Hours
        rule_safety = self.rules_cache.get("LTIFR_SAFETY")
        expr_safety = rule_safety.expression if rule_safety else "(lost_time_injuries * 1000000.0) / total_hours_worked"
        vars_safety = {
            "lost_time_injuries": float(record.lost_time_injuries),
            "total_hours_worked": float(record.total_hours_worked) if record.total_hours_worked > 0 else 200000.0,
        }
        res_safety, eval_safety = SafeMathEvaluator.evaluate(expr_safety, vars_safety)

        trace_safety = {
            "facility_code": facility.code,
            "lost_time_injuries": record.lost_time_injuries,
            "total_hours_worked": float(record.total_hours_worked),
            "formula_evaluated": eval_safety,
            "result_ltifr": round(res_safety, 3),
            "standard": "OSHA / ILO Frequency Rate (per 1,000,000 operational hours)",
            "calculated_at": timezone.now().isoformat(),
        }

        records_to_create.append(
            CalculatedRecord(
                run=run,
                facility=facility,
                workforce_record=record,
                formula_rule=rule_safety,
                rule_code="LTIFR_SAFETY",
                kpi_category="SOCIAL_SAFETY",
                inputs_snapshot=vars_safety,
                formula_evaluated=eval_safety,
                result_value=Decimal(str(round(res_safety, 3))),
                result_unit="injuries_per_million_hours",
                calculation_trace=trace_safety,
            )
        )

        return records_to_create

    def run_full_calculation(self, initiated_by: str = "MANUAL_TRIGGER") -> CalculationRun:
        """
        Executes a full deterministic batch calculation over all warehouse data.
        Returns the completed CalculationRun object.
        """
        start_time = timezone.now()

        run = CalculationRun.objects.create(
            methodology=self.methodology,
            status="RUNNING",
            initiated_by=initiated_by,
            started_at=start_time,
        )

        calculated_items = []
        scope_1_total = Decimal("0.0")
        scope_2_loc_total = Decimal("0.0")
        scope_2_mkt_total = Decimal("0.0")

        # Process all utility consumption records
        utility_records = FacilityUtilityRecord.objects.all().select_related("facility")
        for u_rec in utility_records:
            calc_rec = self.calculate_utility_record(u_rec, run)
            calculated_items.append(calc_rec)
            
            if calc_rec.kpi_category == "SCOPE_1":
                scope_1_total += calc_rec.result_value
            elif calc_rec.kpi_category == "SCOPE_2_LOCATION":
                scope_2_loc_total += calc_rec.result_value
            elif calc_rec.kpi_category == "SCOPE_2_MARKET":
                scope_2_mkt_total += calc_rec.result_value

        # Process all workforce records
        workforce_records = WorkforceMetricRecord.objects.all().select_related("facility")
        diversity_sum = Decimal("0.0")
        diversity_count = 0
        ltifr_sum = Decimal("0.0")
        ltifr_count = 0

        for w_rec in workforce_records:
            wf_calcs = self.calculate_workforce_record(w_rec, run)
            for item in wf_calcs:
                calculated_items.append(item)
                if item.rule_code == "GENDER_DIVERSITY_PCT":
                    diversity_sum += item.result_value
                    diversity_count += 1
                elif item.rule_code == "LTIFR_SAFETY":
                    ltifr_sum += item.result_value
                    ltifr_count += 1

        # Bulk save all calculated records for maximum performance
        CalculatedRecord.objects.bulk_create(calculated_items)

        end_time = timezone.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update CalculationRun summary metrics
        run.status = "COMPLETED"
        run.completed_at = end_time
        run.duration_ms = duration_ms
        run.total_scope_1_tco2e = scope_1_total
        run.total_scope_2_location_tco2e = scope_2_loc_total
        run.total_scope_2_market_tco2e = scope_2_mkt_total
        run.total_ghg_emissions_tco2e = scope_1_total + scope_2_loc_total
        run.avg_gender_diversity_pct = (diversity_sum / diversity_count) if diversity_count > 0 else Decimal("0.0")
        run.avg_ltifr = (ltifr_sum / ltifr_count) if ltifr_count > 0 else Decimal("0.0")
        run.records_processed = utility_records.count() + workforce_records.count()
        run.records_computed = len(calculated_items)
        run.save()

        return run
