from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.risk_limit import RiskLimit
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trades import Trade
from app.models.signal import Signal
from datetime import datetime, timedelta
from app.utils.time import now_eastern
from app.integrations import broker_client

class RiskService:
    """Servicio para gestión y consulta de límites de riesgo"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_or_create_risk_limits(self, user_id: int, portfolio_id: int) -> RiskLimit:
        """Obtener o crear límites de riesgo para usuario/portfolio"""
        risk_limit = self.db.query(RiskLimit).filter(
            and_(
                RiskLimit.user_id == user_id,
                RiskLimit.portfolio_id == portfolio_id
            )
        ).first()
        
        if not risk_limit:
            risk_limit = RiskLimit(
                user_id=user_id,
                portfolio_id=portfolio_id
            )
            self.db.add(risk_limit)
            self.db.commit()
            self.db.refresh(risk_limit)
            
        return risk_limit
    
    def update_risk_limits(
        self, 
        user_id: int, 
        portfolio_id: int, 
        updates: Dict[str, Any]
    ) -> RiskLimit:
        """Actualizar límites de riesgo"""
        risk_limit = self.get_or_create_risk_limits(user_id, portfolio_id)
        
        # Actualizar solo campos válidos
        valid_fields = {
            'max_daily_drawdown', 'max_weekly_drawdown', 'max_account_drawdown',
            'max_position_size', 'max_symbol_exposure', 'max_sector_exposure',
            'max_total_exposure', 'max_orders_per_hour', 'max_orders_per_day',
            'max_open_positions', 'trading_start_time', 'trading_end_time',
            'allow_extended_hours', 'min_price', 'max_price', 'min_volume',
            'max_spread_percent', 'block_earnings_days', 'block_fomc_days',
            'block_news_sentiment_negative'
        }
        
        for field, value in updates.items():
            if field in valid_fields and hasattr(risk_limit, field):
                setattr(risk_limit, field, value)
        
        risk_limit.updated_at = now_eastern()
        self.db.commit()
        self.db.refresh(risk_limit)
        
        return risk_limit
    
    def get_risk_summary(self, user_id: int, portfolio_id: int) -> Dict[str, Any]:
        """Obtener resumen del estado actual de riesgo"""
        risk_limits = self.get_or_create_risk_limits(user_id, portfolio_id)
        now = now_eastern()
        
        # Calcular métricas actuales
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # PnL diario
        daily_pnl = self.db.query(func.sum(Trade.pnl)).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.closed_at >= today_start,
                Trade.status == "closed"
            )
        ).scalar() or 0.0
        
        # Órdenes hoy
        orders_today = self.db.query(Signal).filter(
            and_(
                Signal.user_id == user_id,
                Signal.portfolio_id == portfolio_id,
                Signal.timestamp >= today_start,
                Signal.status.in_(["executed", "processing", "validated"])
            )
        ).count()
        
        # Posiciones abiertas
        open_positions = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.status == "open"
            )
        ).count()
        
        # Órdenes en la última hora
        one_hour_ago = now - timedelta(hours=1)
            
        orders_last_hour = self.db.query(Signal).filter(
            and_(
                Signal.user_id == user_id,
                Signal.portfolio_id == portfolio_id,
                Signal.timestamp >= one_hour_ago,
                Signal.status.in_(["executed", "processing", "validated"])
            )
        ).count()
        
        return {
            "risk_limits": {
                "max_daily_drawdown": risk_limits.max_daily_drawdown,
                "max_orders_per_hour": risk_limits.max_orders_per_hour,
                "max_orders_per_day": risk_limits.max_orders_per_day,
                "max_open_positions": risk_limits.max_open_positions,
                "trading_hours": f"{risk_limits.trading_start_time} - {risk_limits.trading_end_time}",
                "allow_extended_hours": risk_limits.allow_extended_hours
            },
            "current_status": {
                "daily_pnl": round(daily_pnl, 2),
                "orders_today": orders_today,
                "orders_last_hour": orders_last_hour,
                "open_positions": open_positions,
            },
            "limits_usage": {
                "orders_per_hour": f"{orders_last_hour}/{risk_limits.max_orders_per_hour}",
                "orders_per_day": f"{orders_today}/{risk_limits.max_orders_per_day}",
                "open_positions": f"{open_positions}/{risk_limits.max_open_positions}",
            },
            "warnings": self._get_risk_warnings(risk_limits, daily_pnl, orders_today, orders_last_hour, open_positions)
        }
    
    def _get_risk_warnings(
        self, 
        limits: RiskLimit, 
        daily_pnl: float, 
        orders_today: int, 
        orders_last_hour: int, 
        open_positions: int
    ) -> List[str]:
        """Generar advertencias basadas en el uso actual"""
        warnings = []
        
        # Advertencias por uso alto
        if orders_last_hour >= limits.max_orders_per_hour * 0.8:
            warnings.append(f"High order frequency: {orders_last_hour}/{limits.max_orders_per_hour} orders in last hour")
        
        if orders_today >= limits.max_orders_per_day * 0.8:
            warnings.append(f"High daily activity: {orders_today}/{limits.max_orders_per_day} orders today")
        
        if open_positions >= limits.max_open_positions * 0.8:
            warnings.append(f"High position count: {open_positions}/{limits.max_open_positions} open positions")
        
        if daily_pnl < 0:
            try:
                account = broker_client.get_account()
                reference_capital = float(getattr(account, "portfolio_value", 10000.0))
            except Exception:
                reference_capital = 10000.0

            daily_dd_percent = abs(daily_pnl) / reference_capital
            if daily_dd_percent >= limits.max_daily_drawdown * 0.8:
                warnings.append(
                    f"High daily drawdown: {daily_dd_percent:.2%} (limit: {limits.max_daily_drawdown:.2%})"
                )
        
        return warnings
