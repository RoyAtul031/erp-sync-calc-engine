"""
Celery asynchronous and periodic scheduled calculation tasks.
"""

import logging
from celery import shared_task
from apps.calculation_engine.models import CalculationMethodology
from apps.calculation_engine.engine import DeterministicCalculationEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.calculation_engine.tasks.run_active_methodologies_task")
def run_active_methodologies_task(self):
    """
    Scheduled nightly Celery Beat task.
    Re-runs calculation models against latest warehouse records across all active methodologies.
    """
    active_methodologies = CalculationMethodology.objects.filter(is_active=True)
    summary = {}
    logger.info(f"Triggering scheduled calculation for {active_methodologies.count()} methodologies.")

    for method in active_methodologies:
        try:
            engine = DeterministicCalculationEngine(method)
            run = engine.run_full_calculation(initiated_by="CELERY_BEAT_SCHEDULER")
            summary[str(method.id)] = {
                "name": method.name,
                "run_id": str(run.id),
                "total_tco2e": float(run.total_ghg_emissions_tco2e),
                "duration_ms": run.duration_ms,
            }
        except Exception as e:
            logger.error(f"Calculation failed for methodology {method.name}: {e}", exc_info=True)
            summary[str(method.id)] = {"name": method.name, "status": "FAILED", "error": str(e)}

    return summary


@shared_task(bind=True, name="apps.calculation_engine.tasks.run_single_methodology_task")
def run_single_methodology_task(self, methodology_id: str, initiated_by: str = "API_USER"):
    """
    On-demand asynchronous calculation run triggered via REST API or Dashboard.
    """
    try:
        method = CalculationMethodology.objects.get(id=methodology_id)
        engine = DeterministicCalculationEngine(method)
        run = engine.run_full_calculation(initiated_by=initiated_by)
        return {
            "status": run.status,
            "run_id": str(run.id),
            "total_scope_1_tco2e": float(run.total_scope_1_tco2e),
            "total_scope_2_location_tco2e": float(run.total_scope_2_location_tco2e),
            "total_scope_2_market_tco2e": float(run.total_scope_2_market_tco2e),
            "total_ghg_emissions_tco2e": float(run.total_ghg_emissions_tco2e),
            "avg_gender_diversity_pct": float(run.avg_gender_diversity_pct),
            "avg_ltifr": float(run.avg_ltifr),
            "records_computed": run.records_computed,
            "duration_ms": run.duration_ms,
        }
    except CalculationMethodology.DoesNotExist:
        return {"status": "ERROR", "message": f"Methodology {methodology_id} not found."}
    except Exception as e:
        logger.error(f"Async calculation failed for {methodology_id}: {e}", exc_info=True)
        return {"status": "FAILED", "error": str(e)}
