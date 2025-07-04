# backend/app/api/v1/trades.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...models.trades import Trade
from ...models.user import User
from ...schemas.trades import TradeSchema
from ...core.auth import get_current_verified_user, get_admin_user
from ...services.trade_service import TradeService

router = APIRouter()


@router.get("/trades", response_model=List[TradeSchema])
async def get_user_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Ver todos los trades del usuario actual y refrescar su información"""
    service = TradeService(db)
    service.refresh_user_trades(current_user.id)

    trades = (
        db.query(Trade)
        .filter(Trade.user_id == current_user.id)
        .order_by(Trade.opened_at.desc())
        .all()
    )
    return trades


@router.get("/admin/all-trades", response_model=List[TradeSchema])
async def get_all_trades(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Ver todos los trades de todos los usuarios (solo admin)"""
    service = TradeService(db)
    # Actualizar PnL y estado de todos los trades abiertos agrupados por usuario
    user_ids = {t.user_id for t in db.query(Trade).filter(Trade.status == 'open').all()}
    for uid in user_ids:
        service.refresh_user_trades(uid)

    trades = db.query(Trade).order_by(Trade.opened_at.desc()).all()
    return trades
