from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.auth import get_admin_user
from datetime import datetime
import logging
from sqlalchemy import text
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
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


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
        except Exception as db_exc:
            database_status = str(db_exc)
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

        # Broker connectivity check
        try:
            broker_client.get_account()
            broker_status = "connected"
        except Exception as broker_exc:
            broker_status = str(broker_exc)

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

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "system_status": {
                "api": "error",
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

