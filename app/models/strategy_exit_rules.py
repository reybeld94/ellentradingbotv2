from sqlalchemy import Column, String, Float, Boolean, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from app.database import Base
from app.utils.time import now_eastern
from datetime import datetime


class StrategyExitRules(Base):
    __tablename__ = "strategy_exit_rules"

    id = Column(String(50), primary_key=True, index=True)  # strategy_id
    
    # Porcentajes para Stop Loss y Take Profit
    stop_loss_pct = Column(Float, nullable=False, default=0.02)  # 2%
    take_profit_pct = Column(Float, nullable=False, default=0.04)  # 4%
    
    # Trailing Stop configuration
    trailing_stop_pct = Column(Float, nullable=False, default=0.015)  # 1.5%
    use_trailing = Column(Boolean, nullable=False, default=True)
    
    # Risk management
    risk_reward_ratio = Column(Float, nullable=False, default=2.0)  # 1:2
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=now_eastern)
    updated_at = Column(DateTime(timezone=True), default=now_eastern, onupdate=now_eastern)

    def __repr__(self):
        return f"<StrategyExitRules({self.id}: SL={self.stop_loss_pct*100}%, TP={self.take_profit_pct*100}%)>"

    def calculate_exit_prices(self, entry_price: float, side: str = "buy") -> dict:
        """Calcular precios de salida basados en precio de entrada"""
        if side.lower() == "buy":
            stop_loss_price = entry_price * (1 - self.stop_loss_pct)
            take_profit_price = entry_price * (1 + self.take_profit_pct)
        else:  # sell/short
            stop_loss_price = entry_price * (1 + self.stop_loss_pct)
            take_profit_price = entry_price * (1 - self.take_profit_pct)
            
        return {
            "stop_loss_price": round(stop_loss_price, 2),
            "take_profit_price": round(take_profit_price, 2),
            "entry_price": entry_price
        }
