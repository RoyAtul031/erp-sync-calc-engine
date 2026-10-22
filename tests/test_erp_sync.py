from django.test import TestCase
from apps.erp_connector.models import ERPConnection, SyncBatch, RawIngestedPayload
from apps.erp_connector.services import ERPSyncService
from apps.data_warehouse.models import Facility, FacilityUtilityRecord, WorkforceMetricRecord


class ERPSyncServiceTestCase(TestCase):
    def setUp(self):
        self.sap_connection = ERPConnection.objects.create(
            name="Test SAP S/4HANA",
            connector_type="SAP_S4HANA",
            auth_mode="MOCK_INTERNAL",
        )
        self.workday_connection = ERPConnection.objects.create(
            name="Test Workday HCM",
            connector_type="WORKDAY_HCM",
            auth_mode="MOCK_INTERNAL",
        )

    def test_sap_sync_and_facility_provisioning(self):
        service = ERPSyncService(self.sap_connection)
        batch = service.execute_sync(sync_type="FULL")

        self.assertEqual(batch.status, "SUCCESS")
        self.assertGreater(batch.records_saved, 0)
        self.assertIsNotNone(batch.batch_checksum)

        # Facilities should be auto-provisioned
        self.assertTrue(Facility.objects.filter(code="PLANT-US-01").exists())
        self.assertTrue(Facility.objects.filter(code="PLANT-DE-02").exists())

        # Raw immutable payloads with SHA-256 should be saved
        raw_count = RawIngestedPayload.objects.filter(connection=self.sap_connection).count()
        self.assertEqual(raw_count, batch.records_saved)

        # Utility records should exist
        utility_count = FacilityUtilityRecord.objects.count()
        self.assertGreater(utility_count, 0)

    def test_sync_idempotency(self):
        """Executing sync multiple times should not create duplicate utility records."""
        service = ERPSyncService(self.sap_connection)
        service.execute_sync(sync_type="FULL")
        count_first = FacilityUtilityRecord.objects.count()

        # Re-run sync
        service.execute_sync(sync_type="FULL")
        count_second = FacilityUtilityRecord.objects.count()

        self.assertEqual(count_first, count_second)

    def test_workday_workforce_sync(self):
        service = ERPSyncService(self.workday_connection)
        batch = service.execute_sync(sync_type="FULL")

        self.assertEqual(batch.status, "SUCCESS")
        self.assertGreater(batch.records_saved, 0)

        # Workforce records should be populated
        wf_records = WorkforceMetricRecord.objects.all()
        self.assertGreater(wf_records.count(), 0)
        sample = wf_records.first()
        self.assertGreater(sample.total_headcount, 0)
        self.assertGreater(sample.total_hours_worked, 0)
