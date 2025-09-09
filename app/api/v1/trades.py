# backend/app/api/v1/trades.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.trades import Trade
from app.models.user import User
from app.models.signal import Signal
from app.schemas.trades import TradeSchema, EquityPointSchema
from app.core.auth import get_current_verified_user, get_admin_user
from app.services.trade_service import TradeService
from app.services import portfolio_service
from app.services.trade_validation import TradeValidator
from app.core.types import TradeStatus
from app.utils.time import now_eastern
from app.services.order_executor import OrderExecutor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/trades", response_model=List[TradeSchema])
async def get_user_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Ver todos los trades del usuario actual y refrescar su información"""
    service = TradeService(db)
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        return []
    service.refresh_user_trades(current_user.id, active_portfolio.id)

    trades = (
        db.query(Trade)
        .filter(
            Trade.user_id == current_user.id,
            Trade.portfolio_id == active_portfolio.id,
        )
        .order_by(Trade.opened_at.desc())
        .all()
    )
    return trades


@router.get("/trades/by-strategy/{strategy_id}", response_model=List[TradeSchema])
async def get_trades_by_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Return trades for the current user filtered by strategy."""
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        return []

    service = TradeService(db)
    service.refresh_user_trades(current_user.id, active_portfolio.id)

    trades = (
        db.query(Trade)
        .filter(
            Trade.user_id == current_user.id,
            Trade.portfolio_id == active_portfolio.id,
            Trade.strategy_id == str(strategy_id),
        )
        .order_by(Trade.opened_at.desc())
        .all()
    )
    return trades


@router.get("/trades/equity-curve", response_model=List[EquityPointSchema])
async def get_equity_curve(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    strategy_id: str | None = None,
):
    """Return equity curve points for the current user."""
    service = TradeService(db)
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        return []
    data = service.get_equity_curve(
        current_user.id, active_portfolio.id, strategy_id=strategy_id
    )
    return data


@router.get("/admin/all-trades", response_model=List[TradeSchema])
async def get_all_trades(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Ver todos los trades de todos los usuarios (solo admin)"""
    service = TradeService(db)
    # Actualizar PnL y estado de todos los trades abiertos agrupados por usuario y portafolio
    key_pairs = {
        (t.user_id, t.portfolio_id)
        for t in db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
    }
    for uid, pid in key_pairs:
        if pid is not None:
            service.refresh_user_trades(uid, pid)

    trades = db.query(Trade).order_by(Trade.opened_at.desc()).all()
    return trades


@router.post("/trades/validate")
async def validate_trades_with_alpaca(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Validar trades en BD contra posiciones reales en Alpaca"""
    validator = TradeValidator(db)
    validation_result = validator.validate_user_trades(current_user.id)
    return validation_result


@router.post("/trades/cleanup-orphaned")
async def cleanup_orphaned_trades(
    dry_run: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Limpiar trades huérfanos que no existen en Alpaca"""
    validator = TradeValidator(db)
    cleanup_result = validator.cleanup_orphaned_trades(current_user.id, dry_run=dry_run)
    return cleanup_result


@router.post("/trades/{trade_id}/close", response_model=TradeSchema)
async def close_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Create a sell signal and mark the trade as closed."""
    trade = (
        db.query(Trade)
        .filter(Trade.id == trade_id, Trade.user_id == current_user.id)
        .first()
    )
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.status != TradeStatus.OPEN:
        raise HTTPException(status_code=400, detail="Trade is not open")

    # Create sell signal to close the position
    action = "sell" if trade.action.lower() == "buy" else "buy"
    signal = Signal(
        symbol=trade.symbol,
        action=action,
        strategy_id=trade.strategy_id,
        quantity=trade.quantity,
        user_id=current_user.id,
        portfolio_id=trade.portfolio_id,
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    executor = OrderExecutor()
    try:
        executor.execute_signal(signal, current_user)
        trade.status = TradeStatus.CLOSED
        trade.closed_at = now_eastern()
        db.commit()
        db.refresh(trade)
    except Exception:
        logger.exception("Failed to execute close signal for trade %s", trade_id)
        db.rollback()
        db.refresh(trade)

    return trade
