# backend/app/models/signal.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.time import now_eastern


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # buy, sell
    strategy_id = Column(String(50), nullable=False, index=True)
    quantity = Column(Float, nullable=True)  # ✅ CHANGED: Float instead of Integer to support decimals
    price = Column(Float, nullable=True)
    source = Column(String(50), default="tradingview")
    timestamp = Column(DateTime(timezone=True), default=now_eastern)
    processed = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, processed, error
    error_message = Column(Text, nullable=True)

    # Campos para análisis avanzado
    reason = Column(String(50), nullable=True)  # fibonacci_entry, fibonacci_exit, trailing_stop
    confidence = Column(Integer, nullable=True)  # Score 0-100
    tv_timestamp = Column(String(50), nullable=True)  # Timestamp original de TradingView

    # NUEVO: Relación con usuario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", back_populates="signals")

    # Portfolio association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)
    portfolio = relationship("Portfolio", back_populates="signals")

    def __repr__(self):
        return f"<Signal({self.strategy_id}:{self.symbol}, {self.action}, {self.status}, user:{self.user_id})>"
