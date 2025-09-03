import logging
from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.auth import get_current_verified_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/market-hours")
async def get_market_hours(
    symbol: str = "SPY",
    current_user: User = Depends(get_current_verified_user),
):
    """Get current market hours and status"""
    try:
        from app.execution.order_executor import OrderExecutor

        executor = OrderExecutor()
        market_status = await executor.get_market_hours(symbol)
        return market_status
    except Exception as e:
        logger.error(f"Error getting market hours: {str(e)}")
        return {"is_open": False, "status": "unknown", "error": str(e)}

