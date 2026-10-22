"""
Sync Service & Ingestion Pipeline.
Coordinates ERP data extraction, immutable payload snapshotting (SHA-256),
idempotent deduplication, facility auto-provisioning, and normalized warehouse ingestion.
"""

import json
import hashlib
import logging
from typing import Dict, Any
from django.utils import timezone
from apps.erp_connector.models import ERPConnection, SyncBatch, RawIngestedPayload
from apps.erp_connector.client import ERPClient
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord

logger = logging.getLogger(__name__)


class ERPSyncService:
    """
    Enterprise-grade sync service with idempotent extraction, hashing, and warehouse mapping.
    """

    def __init__(self, connection: ERPConnection):
        self.connection = connection
        self.client = ERPClient(connection)

    def execute_sync(self, sync_type: str = "DELTA") -> SyncBatch:
        """
        Executes an end-to-end sync cycle for the given connection.
        Returns the completed SyncBatch.
        """
        start_time = timezone.now()
        
        # 1. Initialize SyncBatch
        batch = SyncBatch.objects.create(
            connection=self.connection,
            sync_type=sync_type,
            status="IN_PROGRESS",
            started_at=start_time,
        )

        self.connection.last_sync_status = "SYNCING"
        self.connection.save(update_fields=["last_sync_status"])

        watermark_str = None
        if sync_type == "DELTA" and self.connection.delta_watermark:
            watermark_str = self.connection.delta_watermark.isoformat()

        records_saved = 0
        records_rejected = 0
        latest_timestamp = None
        batch_hasher = hashlib.sha256()

        try:
            # 2. Fetch records from ERP client
            raw_records = self.client.fetch_records(since=watermark_str)
            batch.records_fetched = len(raw_records)

            for item in raw_records:
                try:
                    # 3. Create Immutable Raw Ingested Snapshot
                    payload_bytes = json.dumps(item, sort_keys=True).encode("utf-8")
                    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
                    batch_hasher.update(payload_bytes)

                    ext_id = item.get("external_record_id", f"REC-{hashlib.md5(payload_bytes).hexdigest()[:8]}")

                    raw_payload, _ = RawIngestedPayload.objects.get_or_create(
                        payload_sha256=payload_hash,
                        defaults={
                            "batch": batch,
                            "connection": self.connection,
                            "payload_type": "UTILITY" if self.connection.connector_type == "SAP_S4HANA" else "WORKFORCE",
                            "external_record_id": ext_id,
                            "raw_json": item,
                        }
                    )

                    # 4. Resolve / Auto-provision Facility
                    plant_code = item.get("plant_code", "PLANT-GENERIC")
                    facility, _ = Facility.objects.get_or_create(
                        code=plant_code,
                        defaults={
                            "name": item.get("plant_name", f"Facility {plant_code}"),
                            "country": item.get("country", "Global"),
                            "region_state": item.get("region_state", ""),
                            "grid_subregion": item.get("grid_subregion", "US_ERCOT"),
                        }
                    )

                    # 5. Ingest into Normalized Warehouse Tables
                    if self.connection.connector_type == "SAP_S4HANA" or "consumption_value" in item:
                        self._ingest_utility_record(facility, item, ext_id)
                    else:
                        self._ingest_workforce_record(facility, item, ext_id)

                    raw_payload.is_processed = True
                    raw_payload.save(update_fields=["is_processed"])
                    records_saved += 1

                    # Track delta watermark
                    delta_ts = item.get("delta_timestamp")
                    if delta_ts and (latest_timestamp is None or delta_ts > latest_timestamp):
                        latest_timestamp = delta_ts

                except Exception as rec_err:
                    logger.error(f"Failed to ingest record {item}: {rec_err}", exc_info=True)
                    records_rejected += 1

            # 6. Finalize Batch & Connection
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            batch.status = "SUCCESS" if records_rejected == 0 else "PARTIAL"
            batch.completed_at = end_time
            batch.duration_ms = duration_ms
            batch.records_saved = records_saved
            batch.records_rejected = records_rejected
            batch.batch_checksum = batch_hasher.hexdigest()
            batch.log_trace = f"Synced {records_saved} records successfully. Rejected: {records_rejected}. Duration: {duration_ms}ms"
            batch.save()

            self.connection.last_sync_at = end_time
            self.connection.last_sync_status = "HEALTHY" if records_rejected == 0 else "PARTIAL"
            self.connection.total_records_synced += records_saved
            if latest_timestamp:
                self.connection.delta_watermark = timezone.now()
            self.connection.save()

            return batch

        except Exception as e:
            end_time = timezone.now()
            batch.status = "FAILED"
            batch.completed_at = end_time
            batch.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            batch.log_trace = f"Batch failed with error: {str(e)}"
            batch.save()

            self.connection.last_sync_status = "FAILED"
            self.connection.last_error_message = str(e)
            self.connection.save(update_fields=["last_sync_status", "last_error_message"])
            raise

    def _ingest_utility_record(self, facility: Facility, item: Dict[str, Any], ext_id: str):
        """Maps ERP record to FacilityUtilityRecord."""
        FacilityUtilityRecord.objects.update_or_create(
            external_sync_id=ext_id,
            defaults={
                "facility": facility,
                "utility_type": item.get("utility_type", "ELECTRICITY_PURCHASED"),
                "scope_category": item.get("scope_category", "SCOPE_2_LOCATION"),
                "start_date": item.get("start_date", "2024-01-01"),
                "end_date": item.get("end_date", "2024-01-31"),
                "consumption_value": item.get("consumption_value", 0.0),
                "consumption_unit": item.get("consumption_unit", "KWH"),
                "source_erp_system": self.connection.connector_type,
                "sap_document_number": item.get("sap_document_number", ext_id),
                "meter_identifier": item.get("meter_identifier", ""),
                "is_renewable_backed": item.get("is_renewable_backed", False),
                "data_quality_score": item.get("data_quality_score", "METER_READING"),
            }
        )

    def _ingest_workforce_record(self, facility: Facility, item: Dict[str, Any], ext_id: str):
        """Maps HR payload to WorkforceMetricRecord."""
        WorkforceMetricRecord.objects.update_or_create(
            external_sync_id=ext_id,
            defaults={
                "facility": facility,
                "period_start": item.get("period_start", "2024-01-01"),
                "period_end": item.get("period_end", "2024-01-31"),
                "total_headcount": item.get("total_headcount", 100),
                "female_headcount": item.get("female_headcount", 50),
                "male_headcount": item.get("male_headcount", 50),
                "non_binary_headcount": item.get("non_binary_headcount", 0),
                "lost_time_injuries": item.get("lost_time_injuries", 0),
                "recordable_incidents": item.get("recordable_incidents", 0),
                "total_hours_worked": item.get("total_hours_worked", 160000.0),
                "training_hours_total": item.get("training_hours_total", 500.0),
                "employee_turnover_count": item.get("employee_turnover_count", 5),
                "source_hr_system": self.connection.connector_type,
            }
        )
