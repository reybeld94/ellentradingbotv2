from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.strategy import Strategy
from ..models.user import User
from ..schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut
from ..core.auth import get_current_verified_user

router = APIRouter()


@router.get("/strategies", response_model=List[StrategyOut])
async def list_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    return db.query(Strategy).order_by(Strategy.created_at.desc()).all()


@router.post("/strategies", response_model=StrategyOut)
async def create_strategy(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    strategy = Strategy(name=strategy_in.name, description=strategy_in.description)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/strategies/{strategy_id}", response_model=StrategyOut)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.put("/strategies/{strategy_id}", response_model=StrategyOut)
async def update_strategy(
    strategy_id: int,
    strategy_in: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy_in.name is not None:
        strategy.name = strategy_in.name
    if strategy_in.description is not None:
        strategy.description = strategy_in.description
    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.delete(strategy)
    db.commit()
    return {"detail": "Strategy deleted"}
