from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord


class FacilitySerializer(serializers.ModelSerializer):
    utility_records_count = serializers.IntegerField(source="utility_records.count", read_only=True)
    workforce_records_count = serializers.IntegerField(source="workforce_records.count", read_only=True)

    class Meta:
        model = Facility
        fields = [
            "id",
            "code",
            "name",
            "facility_type",
            "country",
            "region_state",
            "grid_subregion",
            "gross_area_sqft",
            "baseline_headcount",
            "is_active",
            "utility_records_count",
            "workforce_records_count",
            "created_at",
            "updated_at",
        ]


class FacilityUtilityRecordSerializer(serializers.ModelSerializer):
    facility_code = serializers.CharField(source="facility.code", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = FacilityUtilityRecord
        fields = [
            "id",
            "facility",
            "facility_code",
            "facility_name",
            "utility_type",
            "scope_category",
            "start_date",
            "end_date",
            "consumption_value",
            "consumption_unit",
            "source_erp_system",
            "sap_document_number",
            "meter_identifier",
            "is_renewable_backed",
            "data_quality_score",
            "external_sync_id",
            "created_at",
        ]


class WorkforceMetricRecordSerializer(serializers.ModelSerializer):
    facility_code = serializers.CharField(source="facility.code", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    gender_diversity_pct = serializers.SerializerMethodField()

    class Meta:
        model = WorkforceMetricRecord
        fields = [
            "id",
            "facility",
            "facility_code",
            "facility_name",
            "period_start",
            "period_end",
            "total_headcount",
            "female_headcount",
            "male_headcount",
            "non_binary_headcount",
            "gender_diversity_pct",
            "lost_time_injuries",
            "recordable_incidents",
            "total_hours_worked",
            "training_hours_total",
            "employee_turnover_count",
            "source_hr_system",
            "external_sync_id",
            "created_at",
        ]

    @extend_schema_field(serializers.FloatField)
    def get_gender_diversity_pct(self, obj):
        if obj.total_headcount > 0:
            return round((obj.female_headcount / obj.total_headcount) * 100.0, 2)
        return 0.0
