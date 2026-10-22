import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.erp_connector.models import ERPConnection, SyncBatch, RawIngestedPayload
from apps.erp_connector.serializers import (
    ERPConnectionSerializer,
    SyncBatchSerializer,
    RawIngestedPayloadSerializer,
    TriggerSyncRequestSerializer,
)
from apps.erp_connector.services import ERPSyncService
from apps.erp_connector.tasks import sync_single_connection_task, sync_all_erp_connections_task

logger = logging.getLogger(__name__)


class ERPConnectionViewSet(viewsets.ModelViewSet):
    queryset = ERPConnection.objects.all().prefetch_related("sync_batches", "raw_payloads")
    serializer_class = ERPConnectionSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"], url_path="sync-now")
    def sync_now(self, request, pk=None):
        """
        Triggers an immediate sync for this ERP connection.
        Supports both synchronous execution and background Celery task dispatch.
        """
        connection = self.get_object()
        serializer = TriggerSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sync_type = serializer.validated_data.get("sync_type", "DELTA")
        run_async = serializer.validated_data.get("run_async", False)

        if run_async:
            try:
                task = sync_single_connection_task.delay(str(connection.id), sync_type=sync_type)
                return Response({
                    "status": "QUEUED",
                    "task_id": task.id,
                    "message": f"Sync queued in background for {connection.name}."
                }, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                logger.warning(f"Celery dispatch failed ({e}), falling back to synchronous execution.")

        # Synchronous execution
        try:
            service = ERPSyncService(connection)
            batch = service.execute_sync(sync_type=sync_type)
            return Response({
                "status": "SUCCESS",
                "connection": connection.name,
                "batch_id": str(batch.id),
                "records_saved": batch.records_saved,
                "records_rejected": batch.records_rejected,
                "duration_ms": batch.duration_ms,
                "batch_checksum": batch.batch_checksum,
                "log_trace": batch.log_trace,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "FAILED",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="sync-all")
    def sync_all(self, request):
        """
        Triggers sync for all active ERP connections.
        """
        run_async = request.data.get("run_async", False)
        if run_async:
            try:
                task = sync_all_erp_connections_task.delay()
                return Response({"status": "QUEUED", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)
            except Exception:
                pass

        results = []
        for conn in ERPConnection.objects.filter(is_active=True):
            try:
                service = ERPSyncService(conn)
                batch = service.execute_sync(sync_type="DELTA")
                results.append({
                    "connection": conn.name,
                    "status": batch.status,
                    "records_saved": batch.records_saved,
                    "duration_ms": batch.duration_ms
                })
            except Exception as e:
                results.append({"connection": conn.name, "status": "FAILED", "error": str(e)})

        return Response({"status": "COMPLETED", "connections_synced": results})


class SyncBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SyncBatch.objects.all().select_related("connection")
    serializer_class = SyncBatchSerializer
    permission_classes = [permissions.AllowAny]


class RawIngestedPayloadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RawIngestedPayload.objects.all().select_related("connection", "batch")
    serializer_class = RawIngestedPayloadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        sha = self.request.query_params.get("sha256")
        if sha:
            qs = qs.filter(payload_sha256=sha)
        return qs
