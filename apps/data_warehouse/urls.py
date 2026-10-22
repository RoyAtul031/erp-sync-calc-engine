from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.data_warehouse.views import (
    FacilityViewSet,
    FacilityUtilityRecordViewSet,
    WorkforceMetricRecordViewSet,
)

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'utilities', FacilityUtilityRecordViewSet, basename='utility-record')
router.register(r'workforce', WorkforceMetricRecordViewSet, basename='workforce-record')

urlpatterns = [
    path('', include(router.urls)),
]
