from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.calculation_engine.views import (
    ComplianceFrameworkViewSet,
    EmissionFactorViewSet,
    CalculationMethodologyViewSet,
    FormulaRuleViewSet,
    CalculationRunViewSet,
    CalculatedRecordViewSet,
    FormulaSimulatorAPIView,
)

router = DefaultRouter()
router.register(r'frameworks', ComplianceFrameworkViewSet, basename='framework')
router.register(r'emission-factors', EmissionFactorViewSet, basename='emission-factor')
router.register(r'methodologies', CalculationMethodologyViewSet, basename='methodology')
router.register(r'formula-rules', FormulaRuleViewSet, basename='formula-rule')
router.register(r'runs', CalculationRunViewSet, basename='calculation-run')
router.register(r'calculated-records', CalculatedRecordViewSet, basename='calculated-record')

urlpatterns = [
    path('', include(router.urls)),
    path('simulate-formula/', FormulaSimulatorAPIView.as_view(), name='simulate-formula'),
]
