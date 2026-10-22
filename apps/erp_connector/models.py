import uuid
import hashlib
import json
from django.db import models


class ERPConnection(models.Model):
    """
    Configuration and state for an enterprise external ERP / HR connection (SAP, Workday, etc.).
    """
    CONNECTOR_TYPES = [
        ("SAP_S4HANA", "SAP S/4HANA (Plant Maintenance & Utility Accounting)"),
        ("WORKDAY_HCM", "Workday (Human Capital Management & EHS)"),
        ("ORACLE_FUSION", "Oracle Fusion Cloud ERP"),
        ("CUSTOM_REST", "Custom Enterprise REST API"),
    ]

    AUTH_MODES = [
        ("MOCK_INTERNAL", "Internal High-Fidelity ERP Simulator (No External Setup Required)"),
        ("BEARER_TOKEN", "Bearer / API Token"),
        ("BASIC_AUTH", "HTTP Basic Authentication"),
        ("OAUTH2", "OAuth 2.0 Client Credentials"),
    ]

    STATUS_CHOICES = [
        ("HEALTHY", "Healthy / Online"),
        ("SYNCING", "Syncing In Progress"),
        ("FAILED", "Sync Failed / Error"),
        ("PAUSED", "Paused / Inactive"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="e.g. 'SAP S/4HANA Production Hub' or 'Workday Global HR'")
    connector_type = models.CharField(max_length=64, choices=CONNECTOR_TYPES, default="SAP_S4HANA")
    base_url = models.CharField(max_length=512, default="http://localhost:8000/api/mock-erp/sap")
    auth_mode = models.CharField(max_length=32, choices=AUTH_MODES, default="MOCK_INTERNAL")
    api_token = models.CharField(max_length=512, blank=True, help_text="API token or OAuth client key")
    sync_interval_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)

    # Sync state and delta watermark
    delta_watermark = models.DateTimeField(null=True, blank=True, help_text="Timestamp of latest record fetched (for incremental delta sync)")
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="HEALTHY")
    last_error_message = models.TextField(blank=True)
    total_records_synced = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ERP Connection"
        verbose_name_plural = "ERP Connections"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.get_connector_type_display()}]"


class SyncBatch(models.Model):
    """
    Execution run record for an ERP sync job, tracking lineage, timing, and errors.
    """
    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("SUCCESS", "Success"),
        ("PARTIAL", "Partial Success"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(ERPConnection, on_delete=models.CASCADE, related_name="sync_batches")
    sync_type = models.CharField(max_length=32, choices=[("DELTA", "Incremental Delta Sync"), ("FULL", "Full Historical Ingestion"), ("MANUAL", "Manual Trigger")], default="DELTA")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="IN_PROGRESS")
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    records_fetched = models.PositiveIntegerField(default=0)
    records_saved = models.PositiveIntegerField(default=0)
    records_rejected = models.PositiveIntegerField(default=0)

    log_trace = models.TextField(blank=True)
    batch_checksum = models.CharField(max_length=64, blank=True, help_text="SHA256 checksum of raw payload batch")

    class Meta:
        verbose_name = "Sync Batch"
        verbose_name_plural = "Sync Batches"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Batch {self.id} | {self.connection.name} | {self.status} ({self.records_saved} saved)"


class RawIngestedPayload(models.Model):
    """
    Immutable raw snapshot of every single record received from external ERP.
    Essential for audit compliance (GHG Protocol Scope 3 / SOX compliance): enables 100% data reproducibility.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(SyncBatch, on_delete=models.CASCADE, related_name="raw_payloads")
    connection = models.ForeignKey(ERPConnection, on_delete=models.CASCADE, related_name="raw_payloads")
    
    payload_type = models.CharField(max_length=64, choices=[("UTILITY", "Utility Reading / Invoice"), ("WORKFORCE", "Workforce / HR Metric")])
    external_record_id = models.CharField(max_length=255, db_index=True, help_text="SAP Material Document / Workday Worker ID")
    
    raw_json = models.JSONField(help_text="Exact untouched JSON received from ERP")
    payload_sha256 = models.CharField(max_length=64, db_index=True, help_text="SHA-256 hash for deduplication and tamper proofing")
    
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Raw Ingested Payload"
        verbose_name_plural = "Raw Ingested Payloads"
        ordering = ["-ingested_at"]
        indexes = [
            models.Index(fields=["payload_sha256"]),
            models.Index(fields=["external_record_id"]),
        ]

    def save(self, *args, **kwargs):
        if not self.payload_sha256 and self.raw_json:
            encoded = json.dumps(self.raw_json, sort_keys=True).encode("utf-8")
            self.payload_sha256 = hashlib.sha256(encoded).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Raw {self.payload_type} | Ext ID: {self.external_record_id} | Hash: {self.payload_sha256[:10]}..."
