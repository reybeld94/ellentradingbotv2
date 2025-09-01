"""Background scheduler configuration"""
import logging

try:  # pragma: no cover - optional dependency
    from fastapi_apscheduler import APScheduler
except Exception:  # pragma: no cover - allow absence in tests
    APScheduler = None  # type: ignore

from app.services.bracket_reconciliation_service import run_bracket_reconciliation

logger = logging.getLogger(__name__)

scheduler = APScheduler() if APScheduler else None

if scheduler:
    @scheduler.task('cron', id='bracket_reconciliation', minute='*/15')
    async def scheduled_bracket_reconciliation():
        """Reconciliación automática de bracket orders cada 15 minutos"""
        await run_bracket_reconciliation()
else:
    async def scheduled_bracket_reconciliation():  # pragma: no cover - fallback
        logger.warning("APScheduler not available; bracket reconciliation not scheduled")
