from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.auth import get_admin_user
from datetime import datetime
import logging

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

        return {
            "system_status": {
                "api": "running",
                "execution_scheduler": "running" if execution_scheduler.is_running else "stopped",
                "database": "connected",  # TODO: verificar conexión real
                "broker": "connected"     # TODO: verificar conexión real
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

