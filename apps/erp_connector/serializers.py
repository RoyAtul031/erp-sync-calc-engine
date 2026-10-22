from rest_framework import serializers
from apps.erp_connector.models import ERPConnection, SyncBatch, RawIngestedPayload


class ERPConnectionSerializer(serializers.ModelSerializer):
    batches_count = serializers.IntegerField(source="sync_batches.count", read_only=True)
    raw_payloads_count = serializers.IntegerField(source="raw_payloads.count", read_only=True)

    class Meta:
        model = ERPConnection
        fields = [
            "id",
            "name",
            "connector_type",
            "base_url",
            "auth_mode",
            "api_token",
            "sync_interval_minutes",
            "is_active",
            "delta_watermark",
            "last_sync_at",
            "last_sync_status",
            "last_error_message",
            "total_records_synced",
            "batches_count",
            "raw_payloads_count",
            "created_at",
            "updated_at",
        ]


class SyncBatchSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source="connection.name", read_only=True)
    connector_type = serializers.CharField(source="connection.connector_type", read_only=True)

    class Meta:
        model = SyncBatch
        fields = [
            "id",
            "connection",
            "connection_name",
            "connector_type",
            "sync_type",
            "status",
            "started_at",
            "completed_at",
            "duration_ms",
            "records_fetched",
            "records_saved",
            "records_rejected",
            "log_trace",
            "batch_checksum",
        ]


class RawIngestedPayloadSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = RawIngestedPayload
        fields = [
            "id",
            "batch",
            "connection",
            "connection_name",
            "payload_type",
            "external_record_id",
            "raw_json",
            "payload_sha256",
            "is_processed",
            "processing_error",
            "ingested_at",
        ]


class TriggerSyncRequestSerializer(serializers.Serializer):
    sync_type = serializers.ChoiceField(choices=["DELTA", "FULL", "MANUAL"], default="DELTA")
    run_async = serializers.BooleanField(default=False, help_text="Enqueue as background Celery task if True, or execute synchronously if False")
