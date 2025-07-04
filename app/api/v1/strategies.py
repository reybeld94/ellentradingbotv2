
# backend/app/api/v1/strategies.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...services.trade_service import TradeService
from ...core.auth import get_current_verified_user

router = APIRouter()

@router.get("/strategies/{strategy_id}/metrics")
async def get_strategy_metrics(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Return trading metrics for a given strategy."""
    service = TradeService(db)
    return {
        "strategy_id": strategy_id,
        "total_pl": service.calculate_total_pl(strategy_id),
        "win_rate": service.calculate_win_rate(strategy_id),
        "profit_factor": service.calculate_profit_factor(strategy_id),
        "drawdown": service.calculate_drawdown(strategy_id),
    }

