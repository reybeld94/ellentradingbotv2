from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services.risk_service import RiskService
from app.services import portfolio_service
from app.services.position_manager import position_manager
from app.services.risk_manager import risk_manager
from pydantic import BaseModel

router = APIRouter()

class RiskLimitUpdate(BaseModel):
    max_daily_drawdown: float = None
    max_weekly_drawdown: float = None
    max_position_size: float = None
    max_orders_per_hour: int = None
    max_orders_per_day: int = None
    max_open_positions: int = None
    trading_start_time: str = None
    trading_end_time: str = None
    allow_extended_hours: bool = None

@router.get("/risk/summary")
async def get_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener resumen del estado actual de riesgo"""
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    risk_service = RiskService(db)
    summary = risk_service.get_risk_summary(current_user.id, active_portfolio.id)
    
    return summary

@router.get("/risk/limits")
async def get_risk_limits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener límites de riesgo actuales"""
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    risk_service = RiskService(db)
    risk_limits = risk_service.get_or_create_risk_limits(current_user.id, active_portfolio.id)
    
    return {
        "id": risk_limits.id,
        "max_daily_drawdown": risk_limits.max_daily_drawdown,
        "max_weekly_drawdown": risk_limits.max_weekly_drawdown,
        "max_account_drawdown": risk_limits.max_account_drawdown,
        "max_position_size": risk_limits.max_position_size,
        "max_symbol_exposure": risk_limits.max_symbol_exposure,
        "max_sector_exposure": risk_limits.max_sector_exposure,
        "max_total_exposure": risk_limits.max_total_exposure,
        "max_orders_per_hour": risk_limits.max_orders_per_hour,
        "max_orders_per_day": risk_limits.max_orders_per_day,
        "max_open_positions": risk_limits.max_open_positions,
        "trading_start_time": risk_limits.trading_start_time,
        "trading_end_time": risk_limits.trading_end_time,
        "allow_extended_hours": risk_limits.allow_extended_hours,
        "min_price": risk_limits.min_price,
        "max_price": risk_limits.max_price,
        "min_volume": risk_limits.min_volume,
        "max_spread_percent": risk_limits.max_spread_percent,
        "block_earnings_days": risk_limits.block_earnings_days,
        "block_fomc_days": risk_limits.block_fomc_days,
        "created_at": risk_limits.created_at,
        "updated_at": risk_limits.updated_at
    }

@router.put("/risk/limits")
async def update_risk_limits(
    updates: RiskLimitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Actualizar límites de riesgo"""
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    # Filtrar solo campos no None
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    risk_service = RiskService(db)
    updated_limits = risk_service.update_risk_limits(
        current_user.id, 
        active_portfolio.id, 
        update_data
    )
    
    return {
        "message": "Risk limits updated successfully",
        "updated_fields": list(update_data.keys()),
        "limits": {
            "max_daily_drawdown": updated_limits.max_daily_drawdown,
            "max_orders_per_hour": updated_limits.max_orders_per_hour,
            "max_orders_per_day": updated_limits.max_orders_per_day,
            "max_open_positions": updated_limits.max_open_positions,
        }
    }

@router.get("/risk/status")
async def get_risk_status(current_user: User | None = Depends(get_current_verified_user)):
    """Obtener estado general de riesgo y posiciones actuales"""
    from app.integrations import broker_client

    account = broker_client.get_account()
    buying_power = float(getattr(account, "buying_power", 0))
    portfolio_value = float(getattr(account, "portfolio_value", 0))

    positions = position_manager.get_detailed_positions()
    allocation = risk_manager.get_allocation_info(buying_power)

    return {
        "account": {
            "buying_power": buying_power,
            "portfolio_value": portfolio_value,
        },
        "current_positions": positions,
        "allocation_info": allocation,
    }

@router.post("/risk/test-signal")
async def test_signal_risk(
    signal_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Probar si una señal pasaría el risk management sin ejecutarla"""
    from app.core.types import NormalizedSignal, SignalAction
    from app.risk.manager import RiskManager
    from datetime import datetime
    
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    try:
        # Crear señal de prueba
        test_signal = NormalizedSignal(
            symbol=signal_data.get("symbol", "AAPL"),
            action=SignalAction(signal_data.get("action", "buy")),
            strategy_id=signal_data.get("strategy_id", "test_strategy"),
            quantity=signal_data.get("quantity", 10),
            confidence=signal_data.get("confidence", 75),
            reason=signal_data.get("reason", "test"),
            source="test",
            raw_payload=signal_data,
            idempotency_key="test_" + str(datetime.now().timestamp()),
            fired_at=datetime.now()
        )
        
        # Evaluar con risk manager
        risk_manager = RiskManager(db)
        result = risk_manager.evaluate_signal(test_signal, current_user, active_portfolio)
        
        return {
            "test_signal": {
                "symbol": test_signal.symbol,
                "action": test_signal.action,
                "strategy_id": test_signal.strategy_id,
                "quantity": test_signal.quantity
            },
            "risk_evaluation": result,
            "note": "This was a test - no actual signal was saved or executed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Test failed: {str(e)}")
