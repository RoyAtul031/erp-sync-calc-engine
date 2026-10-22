"""
Celery asynchronous and periodic scheduled sync tasks.
"""

import logging
from celery import shared_task
from apps.erp_connector.models import ERPConnection
from apps.erp_connector.services import ERPSyncService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.erp_connector.tasks.sync_all_erp_connections_task")
def sync_all_erp_connections_task(self):
    """
    Scheduled hourly/daily Celery Beat task.
    Synchronizes all active ERP connections.
    """
    active_connections = ERPConnection.objects.filter(is_active=True)
    results = {}
    logger.info(f"Starting scheduled sync for {active_connections.count()} active ERP connections.")

    for conn in active_connections:
        try:
            service = ERPSyncService(conn)
            batch = service.execute_sync(sync_type="DELTA")
            results[str(conn.id)] = {
                "name": conn.name,
                "status": batch.status,
                "records_saved": batch.records_saved,
                "batch_id": str(batch.id),
            }
        except Exception as e:
            logger.error(f"Sync failed for connection {conn.name}: {e}")
            results[str(conn.id)] = {"name": conn.name, "status": "FAILED", "error": str(e)}

    return results


@shared_task(bind=True, name="apps.erp_connector.tasks.sync_single_connection_task")
def sync_single_connection_task(self, connection_id: str, sync_type: str = "MANUAL"):
    """
    On-demand asynchronous task triggered by API or UI.
    """
    try:
        conn = ERPConnection.objects.get(id=connection_id)
        service = ERPSyncService(conn)
        batch = service.execute_sync(sync_type=sync_type)
        return {
            "status": batch.status,
            "records_saved": batch.records_saved,
            "batch_id": str(batch.id),
            "duration_ms": batch.duration_ms,
        }
    except ERPConnection.DoesNotExist:
        return {"status": "ERROR", "message": f"Connection {connection_id} not found."}
    except Exception as e:
        logger.error(f"Task failed for {connection_id}: {e}", exc_info=True)
        return {"status": "FAILED", "error": str(e)}
