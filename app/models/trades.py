# backend/app/models/trade.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(50), index=True)
    symbol = Column(String(10), index=True)
    action = Column(String(10))  # buy or sell
    quantity = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    status = Column(String(10), default="open")  # open, closed
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="trades")  # si quieres enlazarlo

    # Portfolio association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)
    portfolio = relationship("Portfolio", back_populates="trades")

    def __repr__(self):
        return f"<Trade({self.strategy_id}:{self.symbol} - {self.action}, {self.quantity}, {self.status})>"
