from rest_framework import viewsets, permissions
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord
from apps.data_warehouse.serializers import (
    FacilitySerializer,
    FacilityUtilityRecordSerializer,
    WorkforceMetricRecordSerializer,
)


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().prefetch_related("utility_records", "workforce_records")
    serializer_class = FacilitySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["code", "name", "country", "grid_subregion"]


class FacilityUtilityRecordViewSet(viewsets.ModelViewSet):
    queryset = FacilityUtilityRecord.objects.all().select_related("facility")
    serializer_class = FacilityUtilityRecordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        facility_id = self.request.query_params.get("facility")
        utility_type = self.request.query_params.get("utility_type")
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        if utility_type:
            qs = qs.filter(utility_type=utility_type)
        return qs


class WorkforceMetricRecordViewSet(viewsets.ModelViewSet):
    queryset = WorkforceMetricRecord.objects.all().select_related("facility")
    serializer_class = WorkforceMetricRecordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        facility_id = self.request.query_params.get("facility")
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        return qs
