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
    try:
        updated_limits = risk_service.update_risk_limits(
            current_user.id,
            active_portfolio.id,
            update_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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

@router.get("/risk/metrics")
async def get_risk_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener métricas completas de riesgo para el dashboard"""
    from app.integrations import broker_client
    from app.risk.manager import RiskManager
    from sqlalchemy import func, and_
    from app.models.trades import Trade
    from app.models.signal import Signal
    from app.utils.time import now_eastern
    from datetime import timedelta
    
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    try:
        # Obtener datos del broker
        account = broker_client.get_account()
        portfolio_value = float(getattr(account, "portfolio_value", 100000))
        buying_power = float(getattr(account, "buying_power", 50000))
        
        # Obtener risk limits
        risk_service = RiskService(db)
        risk_limits = risk_service.get_or_create_risk_limits(current_user.id, active_portfolio.id)
        
        now = now_eastern()
        
        # Calcular métricas básicas
        open_positions = db.query(Trade).filter(
            and_(
                Trade.user_id == current_user.id,
                Trade.portfolio_id == active_portfolio.id,
                Trade.status == "open"
            )
        ).count()
        
        # PnL diario
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_pnl = db.query(func.sum(Trade.pnl)).filter(
            and_(
                Trade.user_id == current_user.id,
                Trade.portfolio_id == active_portfolio.id,
                Trade.closed_at >= today_start,
                Trade.status == "closed"
            )
        ).scalar() or 0.0
        
        # Utilización de margen
        margin_utilization = max(0, (portfolio_value - buying_power) / portfolio_value * 100) if portfolio_value > 0 else 0
        
        # Leverage ratio estimado
        leverage_ratio = portfolio_value / buying_power if buying_power > 0 else 1.0
        
        # Risk score calculado
        risk_factors = []
        risk_factors.append(min(open_positions / risk_limits.max_open_positions * 30, 30))  # Factor posiciones
        risk_factors.append(min(margin_utilization, 25))  # Factor margen
        risk_factors.append(min(abs(daily_pnl) / portfolio_value * 1000, 15) if portfolio_value > 0 else 0)  # Factor PnL
        risk_factors.append(min((leverage_ratio - 1) * 20, 20))  # Factor leverage
        
        risk_score = min(sum(risk_factors), 100)
        
        # Determinar nivel de riesgo
        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"  
        elif risk_score < 80:
            risk_level = "high"
        else:
            risk_level = "critical"
            
        # VaR simple (estimación básica)
        portfolio_var = min(risk_score / 100 * 5, 10)  # Entre 0-10%
        portfolio_cvar = portfolio_var * 1.5
        
        return {
            "metrics": {
                "portfolioVaR": round(portfolio_var, 2),
                "portfolioCVaR": round(portfolio_cvar, 2),
                "positionLimit": risk_limits.max_open_positions,
                "usedPositions": open_positions,
                "marginUtilization": round(margin_utilization, 1),
                "leverageRatio": round(leverage_ratio, 2),
                "correlationRisk": 35.7,  # Dummy por ahora
                "concentrationRisk": 28.4,  # Dummy por ahora
                "liquidityRisk": 12.1,  # Dummy por ahora
                "marketRisk": 18.9,  # Dummy por ahora
                "riskScore": int(risk_score),
                "riskLevel": risk_level
            },
            "account": {
                "portfolioValue": portfolio_value,
                "buyingPower": buying_power,
                "dailyPnL": daily_pnl
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating risk metrics: {str(e)}")

@router.get("/risk/exposure")
async def get_risk_exposure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener exposición real por símbolos y sectores"""
    from app.integrations import broker_client
    
    active_portfolio = portfolio_service.get_active(db, current_user)
    if not active_portfolio:
        raise HTTPException(status_code=400, detail="No active portfolio found")
    
    try:
        # Obtener posiciones reales del broker
        positions = position_manager.get_detailed_positions()
        
        # Obtener valor total del portfolio
        account = broker_client.get_account()
        portfolio_value = float(getattr(account, "portfolio_value", 100000))
        
        # Mapeo simple de sectores (extender según necesites)
        sector_mapping = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'NVDA': 'Technology',
            'JPM': 'Financial', 'BAC': 'Financial', 'GS': 'Financial', 'WFC': 'Financial',
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 'ABBV': 'Healthcare',
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
            'AMZN': 'Consumer Discretionary', 'TSLA': 'Consumer Discretionary',
            'WMT': 'Consumer Staples', 'PG': 'Consumer Staples'
        }
        
        # Agrupar por sectores
        sectors = {}
        total_exposure = 0
        
        for pos in positions:
            symbol = pos['symbol']
            market_value = abs(pos['market_value'])
            sector = sector_mapping.get(symbol, 'Other')
            
            if sector not in sectors:
                sectors[sector] = {
                    'category': sector,
                    'exposure': 0,
                    'limit': portfolio_value * 0.3,  # 30% max por sector
                    'utilizationPercent': 0,
                    'riskLevel': 'low',
                    'positions': []
                }
            
            # Agregar posición al sector
            sectors[sector]['exposure'] += market_value
            total_exposure += market_value
            
            sectors[sector]['positions'].append({
                'symbol': symbol,
                'value': market_value,
                'percentage': 0,  # Calculamos después
                'riskContribution': market_value / portfolio_value * 100 if portfolio_value > 0 else 0
            })
        
        # Calcular porcentajes y niveles de riesgo
        exposure_list = []
        for sector_data in sectors.values():
            sector_total = sector_data['exposure']
            utilization = (sector_total / sector_data['limit'] * 100) if sector_data['limit'] > 0 else 0
            
            # Actualizar porcentajes de posiciones
            for position in sector_data['positions']:
                position['percentage'] = (position['value'] / sector_total * 100) if sector_total > 0 else 0
            
            # Determinar nivel de riesgo
            if utilization > 80:
                risk_level = 'high'
            elif utilization > 60:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            exposure_list.append({
                'category': sector_data['category'],
                'exposure': sector_total,
                'limit': sector_data['limit'],
                'utilizationPercent': round(utilization, 1),
                'riskLevel': risk_level,
                'positions': sector_data['positions']
            })
        
        # Ordenar por exposición descendente
        exposure_list.sort(key=lambda x: x['exposure'], reverse=True)
        
        return {"exposure": exposure_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating exposure: {str(e)}")

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
