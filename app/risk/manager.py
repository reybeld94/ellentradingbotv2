from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, time, timedelta
from app.core.types import NormalizedSignal, OrderIntent, TradeStatus
from app.models.risk_limit import RiskLimit
from app.models.trades import Trade
from app.models.signal import Signal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.utils.time import now_eastern
from app.integrations import broker_client
import logging

logger = logging.getLogger(__name__)

class RiskViolation(Exception):
    """Excepción cuando se viola una regla de riesgo"""
    pass

class RiskManager:
    """Gestor principal de riesgo - punto único de verdad para todas las validaciones"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def evaluate_signal(
        self, 
        signal: NormalizedSignal, 
        user: User, 
        portfolio: Portfolio
    ) -> Dict[str, Any]:
        """
        Evaluar si una señal pasa todos los checks de riesgo
        Retorna: {"approved": bool, "reason": str, "suggested_quantity": float}
        """
        
        try:
            # 1. Obtener límites de riesgo para este usuario/portfolio
            risk_limits = self._get_risk_limits(user.id, portfolio.id)
            
            # 2. Verificar horarios de trading
            if not self._check_trading_hours(risk_limits):
                return self._reject("Outside trading hours")
            
            # 3. Verificar límites operacionales
            operation_check = self._check_operational_limits(signal, user.id, portfolio.id, risk_limits)
            if not operation_check["approved"]:
                return operation_check
            
            # 4. Verificar drawdown actual
            drawdown_check = self._check_drawdown_limits(user.id, portfolio.id, risk_limits)
            if not drawdown_check["approved"]:
                return drawdown_check
            
            # 5. Verificar exposición por símbolo
            exposure_check = self._check_symbol_exposure(signal.symbol, user.id, portfolio.id, risk_limits)
            if not exposure_check["approved"]:
                return exposure_check

            # 6. Calcular cantidad sugerida (position sizing básico)
            suggested_quantity = self._calculate_position_size(signal, user.id, portfolio.id, risk_limits)

            logger.info(f"Signal {signal.symbol} {signal.action} APPROVED by risk manager")
            
            return {
                "approved": True,
                "reason": "All risk checks passed",
                "suggested_quantity": suggested_quantity,
                "checks_passed": [
                    "trading_hours", "operational_limits", 
                    "drawdown_limits", "symbol_exposure"
                ]
            }
            
        except RiskViolation as e:
            return self._reject(str(e))
        except Exception as e:
            logger.error(f"Error in risk evaluation: {e}")
            return self._reject(f"Risk evaluation error: {str(e)}")
    
    def _get_risk_limits(self, user_id: int, portfolio_id: int) -> RiskLimit:
        """Obtener límites de riesgo, crear defaults si no existen"""
        risk_limit = self.db.query(RiskLimit).filter(
            and_(
                RiskLimit.user_id == user_id,
                RiskLimit.portfolio_id == portfolio_id
            )
        ).first()
        
        if not risk_limit:
            # Crear límites por defecto
            risk_limit = RiskLimit(
                user_id=user_id,
                portfolio_id=portfolio_id
            )
            self.db.add(risk_limit)
            self.db.commit()
            self.db.refresh(risk_limit)
            
        return risk_limit
    
    def _check_trading_hours(self, risk_limits: RiskLimit) -> bool:
        """Verificar si estamos en horario de trading"""
        now = now_eastern()
        current_time = now.time()
        
        # Convertir strings a time objects
        start_time = time.fromisoformat(risk_limits.trading_start_time)
        end_time = time.fromisoformat(risk_limits.trading_end_time)
        
        # Verificar que sea día de semana (lunes-viernes)
        if now.weekday() >= 5:  # 5=sábado, 6=domingo
            return False
        
        # Verificar horario
        if start_time <= current_time <= end_time:
            return True
        
        # Si permite extended hours, más flexible
        if risk_limits.allow_extended_hours:
            # Pre-market: 04:00-09:30, After-hours: 16:00-20:00
            pre_market = time(4, 0) <= current_time <= time(9, 30)
            after_hours = time(16, 0) <= current_time <= time(20, 0)
            return pre_market or after_hours
        
        return False
    
    def _check_operational_limits(
        self, 
        signal: NormalizedSignal, 
        user_id: int, 
        portfolio_id: int, 
        risk_limits: RiskLimit
    ) -> Dict[str, Any]:
        """Verificar límites operacionales (órdenes por hora/día, posiciones abiertas)"""
        
        now = now_eastern()
        
        # Contar órdenes en la última hora
        one_hour_ago = now - timedelta(hours=1)
        orders_last_hour = self.db.query(Signal).filter(
            and_(
                Signal.user_id == user_id,
                Signal.portfolio_id == portfolio_id,
                Signal.timestamp >= one_hour_ago,
                Signal.status.in_(["executed", "processing"])
            )
        ).count()
        
        if orders_last_hour >= risk_limits.max_orders_per_hour:
            return self._reject(f"Max orders per hour exceeded: {orders_last_hour}/{risk_limits.max_orders_per_hour}")
        
        # Contar órdenes hoy
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        orders_today = self.db.query(Signal).filter(
            and_(
                Signal.user_id == user_id,
                Signal.portfolio_id == portfolio_id,
                Signal.timestamp >= today_start,
                Signal.status.in_(["executed", "processing"])
            )
        ).count()
        
        if orders_today >= risk_limits.max_orders_per_day:
            return self._reject(f"Max orders per day exceeded: {orders_today}/{risk_limits.max_orders_per_day}")
        
        # Contar posiciones abiertas
        open_trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.status == TradeStatus.OPEN,
            )
        ).count()
        
        if open_trades >= risk_limits.max_open_positions:
            return self._reject(f"Max open positions exceeded: {open_trades}/{risk_limits.max_open_positions}")
        
        return {"approved": True}
    
    def _check_drawdown_limits(
        self, 
        user_id: int, 
        portfolio_id: int, 
        risk_limits: RiskLimit
    ) -> Dict[str, Any]:
        """Verificar límites de drawdown"""
        
        now = now_eastern()
        
        # Calcular drawdown diario
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_pnl = self.db.query(func.sum(Trade.pnl)).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.closed_at >= today_start,
                Trade.status == TradeStatus.CLOSED,
            )
        ).scalar() or 0.0
        
        # Obtener capital real del broker/portfolio
        try:
            account = broker_client.get_account()
            capital = float(getattr(account, "portfolio_value", 0.0))
        except Exception as e:
            logger.error(f"Error getting account info for drawdown: {e}")
            capital = 0.0

        daily_dd_percent = abs(daily_pnl) / capital if daily_pnl < 0 and capital > 0 else 0.0
        
        if daily_dd_percent > risk_limits.max_daily_drawdown:
            return self._reject(f"Daily drawdown limit exceeded: {daily_dd_percent:.2%} > {risk_limits.max_daily_drawdown:.2%}")
        
        return {"approved": True}
    
    def _check_symbol_exposure(
        self, 
        symbol: str, 
        user_id: int, 
        portfolio_id: int, 
        risk_limits: RiskLimit
    ) -> Dict[str, Any]:
        """Verificar exposición por símbolo"""

        # Calcular exposición actual en este símbolo
        current_position = self.db.query(func.sum(Trade.quantity)).filter(
            and_(
                Trade.symbol == symbol,
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.status == TradeStatus.OPEN,
            )
        ).scalar() or 0.0

        if current_position == 0:
            return {"approved": True}

        try:
            trade = broker_client.get_latest_trade(symbol)
            current_price = float(getattr(trade, "price", 0.0))
            account = broker_client.get_account()
            total_capital = float(getattr(account, "portfolio_value", 0.0))
        except Exception as e:
            logger.error(f"Error getting data for exposure check: {e}")
            return {"approved": True}

        if current_price <= 0 or total_capital <= 0:
            return {"approved": True}

        position_value = current_position * current_price
        max_allowed = total_capital * risk_limits.max_symbol_exposure

        if position_value > max_allowed:
            return self._reject(
                f"Symbol exposure limit exceeded: ${position_value:.2f} > ${max_allowed:.2f}"
            )

        return {"approved": True}
    
    def _calculate_position_size(
        self, 
        signal: NormalizedSignal, 
        user_id: int, 
        portfolio_id: int, 
        risk_limits: RiskLimit
    ) -> float:
        """Calcular tamaño de posición sugerido"""
        
        # Obtener capital disponible y precio actual del símbolo
        try:
            account = broker_client.get_account()
            available_capital = float(getattr(account, "buying_power", 0.0))
            total_capital = float(getattr(account, "portfolio_value", 0.0))
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise RiskViolation("Unable to retrieve account information")

        try:
            trade = broker_client.get_latest_trade(signal.symbol)
            current_price = float(getattr(trade, "price", 0.0))
        except Exception as e:
            logger.error(f"Error getting price for {signal.symbol}: {e}")
            raise RiskViolation(f"Unable to retrieve price for {signal.symbol}")

        if current_price <= 0 or total_capital <= 0:
            raise RiskViolation("Invalid account or price data")

        max_position_value = total_capital * risk_limits.max_position_size
        allowed_capital = min(max_position_value, available_capital)

        if signal.quantity:
            requested_value = signal.quantity * current_price
            if requested_value > allowed_capital:
                raise RiskViolation(
                    f"Requested position value ${requested_value:.2f} exceeds max allowed ${allowed_capital:.2f}"
                )
            return signal.quantity

        suggested_shares = allowed_capital / current_price
        return round(suggested_shares, 2)
    
    def _reject(self, reason: str) -> Dict[str, Any]:
        """Helper para rechazar señales"""
        return {
            "approved": False,
            "reason": reason,
            "suggested_quantity": 0.0
        }
