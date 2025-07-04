
# backend/app/api/v1/strategies.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.user import User
from ...models.strategy import Strategy
from ...services.trade_service import TradeService
from ...core.auth import get_current_verified_user
from ...schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut

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

