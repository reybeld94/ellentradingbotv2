
# backend/app/api/v1/strategies.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.strategy import Strategy
from app.services.trade_service import TradeService
from app.core.auth import get_current_verified_user
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut

router = APIRouter()

@router.get("/strategies", response_model=List[StrategyOut])
async def list_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Return all strategies."""
    return db.query(Strategy).all()


@router.post("/strategies", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Create a new strategy."""
    new_strategy = Strategy(**strategy.model_dump())
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy


@router.put("/strategies/{strategy_id}", response_model=StrategyOut)
async def update_strategy(
    strategy_id: int,
    updates: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Update an existing strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)

    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Delete a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    db.delete(strategy)
    db.commit()
    return None

from app.schemas.metrics import StrategyMetricsSchema


@router.get("/strategies/{strategy_id}/metrics", response_model=StrategyMetricsSchema)
async def get_strategy_metrics(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Return trading metrics for a given strategy."""
    service = TradeService(db)
    wl = service.calculate_avg_win_loss(strategy_id)
    return {
        "strategy_id": strategy_id,
        "total_pl": service.calculate_total_pl(strategy_id),
        "win_rate": service.calculate_win_rate(strategy_id),
        "profit_factor": service.calculate_profit_factor(strategy_id),
        "drawdown": service.calculate_drawdown(strategy_id),
        "sharpe_ratio": service.calculate_sharpe_ratio(strategy_id),
        "sortino_ratio": service.calculate_sortino_ratio(strategy_id),
        "avg_win": wl["avg_win"],
        "avg_loss": wl["avg_loss"],
        "win_loss_ratio": wl["win_loss_ratio"],
        "expectancy": service.calculate_expectancy(strategy_id),
    }

