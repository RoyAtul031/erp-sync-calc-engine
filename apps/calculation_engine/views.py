import csv
import logging
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.calculation_engine.models import (
    ComplianceFramework,
    EmissionFactor,
    CalculationMethodology,
    FormulaRule,
    CalculationRun,
    CalculatedRecord,
)
from apps.calculation_engine.serializers import (
    ComplianceFrameworkSerializer,
    EmissionFactorSerializer,
    CalculationMethodologySerializer,
    FormulaRuleSerializer,
    CalculationRunSerializer,
    CalculatedRecordSerializer,
    FormulaSimulationSerializer,
)
from apps.calculation_engine.engine import DeterministicCalculationEngine, SafeMathEvaluator
from apps.calculation_engine.tasks import run_single_methodology_task

logger = logging.getLogger(__name__)


class ComplianceFrameworkViewSet(viewsets.ModelViewSet):
    queryset = ComplianceFramework.objects.all().prefetch_related("emission_factors", "methodologies")
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [permissions.AllowAny]


class EmissionFactorViewSet(viewsets.ModelViewSet):
    queryset = EmissionFactor.objects.all().select_related("framework")
    serializer_class = EmissionFactorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        framework_code = self.request.query_params.get("framework")
        category = self.request.query_params.get("category")
        if framework_code:
            qs = qs.filter(framework__code=framework_code)
        if category:
            qs = qs.filter(category=category)
        return qs


class CalculationMethodologyViewSet(viewsets.ModelViewSet):
    queryset = CalculationMethodology.objects.all().select_related("framework").prefetch_related("formula_rules", "runs")
    serializer_class = CalculationMethodologySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"], url_path="run-calculation")
    def run_calculation(self, request, pk=None):
        """
        Executes a deterministic calculation run using this methodology.
        Computes Scope 1, Scope 2, and Social ESG KPIs across all warehouse records.
        """
        methodology = self.get_object()
        run_async = request.data.get("run_async", False)

        if run_async:
            try:
                task = run_single_methodology_task.delay(str(methodology.id), initiated_by="API_ASYNC_REQUEST")
                return Response({
                    "status": "QUEUED",
                    "task_id": task.id,
                    "message": f"Calculation run queued for methodology '{methodology.name}'."
                }, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                logger.warning(f"Celery dispatch failed ({e}), running synchronously.")

        try:
            engine = DeterministicCalculationEngine(methodology)
            run = engine.run_full_calculation(initiated_by=request.data.get("initiated_by", "API_USER"))
            serializer = CalculationRunSerializer(run)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Calculation failed for methodology {methodology.id}: {e}", exc_info=True)
            return Response({"status": "FAILED", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FormulaRuleViewSet(viewsets.ModelViewSet):
    queryset = FormulaRule.objects.all().select_related("methodology")
    serializer_class = FormulaRuleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        methodology_id = self.request.query_params.get("methodology")
        if methodology_id:
            qs = qs.filter(methodology_id=methodology_id)
        return qs


class CalculationRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CalculationRun.objects.all().select_related("methodology", "methodology__framework").prefetch_related("calculated_records")
    serializer_class = CalculationRunSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["get"], url_path="export-csv")
    def export_csv(self, request, pk=None):
        """
        Exports a full SOX / CSRD compliant audit spreadsheet with complete formula derivation,
        certified emission factor citations, and raw ERP source document references.
        """
        run = self.get_object()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="ESG_Audit_Run_{run.id}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Calculation Run ID",
            "Methodology",
            "Compliance Framework",
            "Facility Code",
            "Facility Name",
            "Grid Region",
            "KPI Category",
            "Rule Code",
            "Raw ERP Document Reference",
            "Raw Consumption Measured",
            "Consumption Unit",
            "Normalization Step",
            "Emission Factor Applied",
            "Emission Factor Unit",
            "Official Factor Citation",
            "Evaluated AST Equation",
            "Audited Result Value",
            "Result Unit",
            "Timestamp UTC"
        ])

        for rec in run.calculated_records.select_related("facility", "utility_record").all():
            trace = rec.calculation_trace or {}
            raw = trace.get("raw_input", {})
            factor = trace.get("emission_factor_applied", {})
            writer.writerow([
                str(run.id),
                run.methodology.name,
                run.methodology.framework.code,
                rec.facility.code,
                rec.facility.name,
                rec.facility.grid_subregion,
                rec.kpi_category,
                rec.rule_code,
                raw.get("sap_document_number", "WORKDAY_REF"),
                raw.get("consumption_value", ""),
                raw.get("consumption_unit", ""),
                trace.get("unit_normalization_step", ""),
                factor.get("factor_value", ""),
                factor.get("factor_unit", ""),
                factor.get("source_citation", ""),
                rec.formula_evaluated,
                rec.result_value,
                rec.result_unit,
                rec.created_at.isoformat(),
            ])

        return response


class CalculatedRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CalculatedRecord.objects.all().select_related("facility", "utility_record", "workforce_record", "formula_rule")
    serializer_class = CalculatedRecordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        run_id = self.request.query_params.get("run")
        facility_id = self.request.query_params.get("facility")
        kpi_category = self.request.query_params.get("kpi_category")
        rule_code = self.request.query_params.get("rule_code")

        if run_id:
            qs = qs.filter(run_id=run_id)
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        if kpi_category:
            qs = qs.filter(kpi_category=kpi_category)
        if rule_code:
            qs = qs.filter(rule_code=rule_code)
        return qs


class FormulaSimulatorAPIView(APIView):
    """
    Simulates custom mathematical formulas safely via AST before saving.
    Compliance analysts can test and preview expressions in the UI in real time.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=FormulaSimulationSerializer,
        summary="Safe AST Formula Simulation",
        description="Safely tests a mathematical expression against supplied variables using Python AST parser."
    )
    def post(self, request):
        serializer = FormulaSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expression = serializer.validated_data["expression"]
        variables = serializer.validated_data["variables"]

        try:
            result_val, evaluated_str = SafeMathEvaluator.evaluate(expression, variables)
            return Response({
                "is_valid": True,
                "result": round(result_val, 6),
                "formula_evaluated": evaluated_str,
                "expression_raw": expression,
                "variables_supplied": variables,
            })
        except Exception as e:
            return Response({
                "is_valid": False,
                "error": str(e),
                "expression_raw": expression,
                "variables_supplied": variables,
            }, status=status.HTTP_400_BAD_REQUEST)
