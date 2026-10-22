from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.erp_connector.views import (
    ERPConnectionViewSet,
    SyncBatchViewSet,
    RawIngestedPayloadViewSet,
)
from apps.erp_connector.mock_erp_api import MockSAPUtilityAPIView, MockWorkdayWorkforceAPIView

router = DefaultRouter()
router.register(r'connections', ERPConnectionViewSet, basename='erp-connection')
router.register(r'batches', SyncBatchViewSet, basename='sync-batch')
router.register(r'raw-payloads', RawIngestedPayloadViewSet, basename='raw-payload')

urlpatterns = [
    # Main connector endpoints
    path('', include(router.urls)),

    # High-Fidelity Simulated External ERP Endpoints (SAP S/4HANA & Workday HCM)
    path('mock-erp/sap/utility-metering/', MockSAPUtilityAPIView.as_view(), name='mock-sap-utility'),
    path('mock-erp/workday/workforce-metrics/', MockWorkdayWorkforceAPIView.as_view(), name='mock-workday-workforce'),
]
