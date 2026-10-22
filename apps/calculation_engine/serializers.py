from rest_framework import serializers
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
    CalculationRun,
    CalculatedRecord,
)


class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    emission_factors_count = serializers.IntegerField(source="emission_factors.count", read_only=True)
    methodologies_count = serializers.IntegerField(source="methodologies.count", read_only=True)

    class Meta:
        model = ComplianceFramework
        fields = [
            "id",
            "code",
            "name",
            "jurisdiction",
            "version_tag",
            "description",
            "is_default",
            "emission_factors_count",
            "methodologies_count",
            "created_at",
            "updated_at",
        ]


class EmissionFactorSerializer(serializers.ModelSerializer):
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    framework_name = serializers.CharField(source="framework.name", read_only=True)

    class Meta:
        model = EmissionFactor
        fields = [
            "id",
            "framework",
            "framework_code",
            "framework_name",
            "category",
            "activity_key",
            "display_name",
            "factor_value",
            "factor_unit",
            "co2_ratio",
            "ch4_ratio",
            "n2o_ratio",
            "source_citation",
            "effective_year",
            "is_active",
            "created_at",
            "updated_at",
        ]


class FormulaRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaRule
        fields = [
            "id",
            "methodology",
            "rule_code",
            "name",
            "kpi_category",
            "expression",
            "output_unit",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]


class CalculationMethodologySerializer(serializers.ModelSerializer):
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    framework_name = serializers.CharField(source="framework.name", read_only=True)
    formula_rules = FormulaRuleSerializer(many=True, read_only=True)
    runs_count = serializers.IntegerField(source="runs.count", read_only=True)

    class Meta:
        model = CalculationMethodology
        fields = [
            "id",
            "name",
            "framework",
            "framework_code",
            "framework_name",
            "version_label",
            "description",
            "is_active",
            "runs_count",
            "formula_rules",
            "created_at",
            "updated_at",
        ]


class CalculatedRecordSerializer(serializers.ModelSerializer):
    facility_code = serializers.CharField(source="facility.code", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    utility_type = serializers.CharField(source="utility_record.utility_type", read_only=True)
    sap_document_number = serializers.CharField(source="utility_record.sap_document_number", read_only=True)

    class Meta:
        model = CalculatedRecord
        fields = [
            "id",
            "run",
            "facility",
            "facility_code",
            "facility_name",
            "utility_record",
            "utility_type",
            "sap_document_number",
            "workforce_record",
            "rule_code",
            "kpi_category",
            "inputs_snapshot",
            "formula_evaluated",
            "result_value",
            "result_unit",
            "calculation_trace",
            "created_at",
        ]


class CalculationRunSerializer(serializers.ModelSerializer):
    methodology_name = serializers.CharField(source="methodology.name", read_only=True)
    framework_code = serializers.CharField(source="methodology.framework.code", read_only=True)

    class Meta:
        model = CalculationRun
        fields = [
            "id",
            "methodology",
            "methodology_name",
            "framework_code",
            "status",
            "initiated_by",
            "started_at",
            "completed_at",
            "duration_ms",
            "total_scope_1_tco2e",
            "total_scope_2_location_tco2e",
            "total_scope_2_market_tco2e",
            "total_ghg_emissions_tco2e",
            "avg_gender_diversity_pct",
            "avg_ltifr",
            "records_processed",
            "records_computed",
            "error_log",
        ]


class FormulaSimulationSerializer(serializers.Serializer):
    expression = serializers.CharField(max_length=512)
    variables = serializers.DictField(child=serializers.FloatField(), default=dict)
