from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.auth import get_admin_user
from datetime import datetime
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from alpaca.common.exceptions import APIError
from app.database import get_db
from app.integrations import broker_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def system_health_check():
    """Health check general del sistema"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "trading_bot_api",
            "version": "1.0.0"
        }
    except Exception:
        logger.exception("Health check failed")
        raise


@router.get("/status")
async def system_status(
    current_user: User = Depends(get_admin_user)
):
    """Estado completo del sistema"""
    try:
        from app.execution.scheduler import execution_scheduler

        # Database connectivity check
        db = None
        try:
            db = next(get_db())
            db.execute(text("SELECT 1"))
            database_status = "connected"
        except SQLAlchemyError as db_exc:
            logger.warning("Database connectivity issue: %s", db_exc)
            database_status = str(db_exc)
        finally:
            if db is not None:
                try:
                    db.close()
                except SQLAlchemyError as close_exc:
                    logger.warning("Error closing database connection: %s", close_exc)

        # Broker connectivity check
        try:
            broker_client.get_account()
            broker_status = "connected"
        except APIError as broker_exc:
            logger.warning("Broker connectivity issue: %s", broker_exc)
            broker_status = f"API error: {broker_exc}"

        return {
            "system_status": {
                "api": "running",
                "execution_scheduler": "running" if execution_scheduler.is_running else "stopped",
                "database": database_status,
                "broker": broker_status
            },
            "scheduler_details": execution_scheduler.get_status(),
            "timestamp": datetime.utcnow().isoformat(),
            "checked_by": current_user.username
        }

    except Exception:
        logger.exception("Error getting system status")
        raise

