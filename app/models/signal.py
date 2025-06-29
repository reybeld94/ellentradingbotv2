# backend/app/models/signal.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # buy, sell
    strategy_id = Column(String(50), nullable=False, index=True)  # NUEVO: identificador de estrategia
    quantity = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    source = Column(String(50), default="tradingview")
    timestamp = Column(DateTime, server_default=func.now())
    processed = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, processed, error
    error_message = Column(Text, nullable=True)

    # Campos para análisis avanzado
    reason = Column(String(50), nullable=True)  # fibonacci_entry, fibonacci_exit, trailing_stop
    confidence = Column(Integer, nullable=True)  # Score 0-100
    tv_timestamp = Column(String(50), nullable=True)  # Timestamp original de TradingView

    def __repr__(self):
        return f"<Signal({self.strategy_id}:{self.symbol}, {self.action}, {self.status}, conf:{self.confidence})>"