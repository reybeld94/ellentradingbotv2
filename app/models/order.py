# backend/app/models/order.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    DECIMAL,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.types import OrderStatus, OrderType
from datetime import datetime
from typing import Optional


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # IDs únicos
    client_order_id = Column(String(50), unique=True, nullable=False, index=True)
    broker_order_id = Column(String(50), unique=True, nullable=True, index=True)
    parent_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Básicos
    symbol = Column(String(10), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy/sell
    quantity = Column(DECIMAL(12, 4), nullable=False)
    order_type = Column(String(20), nullable=False, default=OrderType.MARKET)
    
    # Precios
    limit_price = Column(DECIMAL(12, 4), nullable=True)
    stop_price = Column(DECIMAL(12, 4), nullable=True)
    
    # Estado y timestamps
    status = Column(String(20), nullable=False, default=OrderStatus.NEW, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ejecución
    filled_quantity = Column(DECIMAL(12, 4), default=0, nullable=False)
    avg_fill_price = Column(DECIMAL(12, 4), nullable=True)
    total_fees = Column(DECIMAL(12, 4), default=0, nullable=False)
    
    # Retry y error handling
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    # Time in force
    time_in_force = Column(String(10), default="day", nullable=False)
    
    # Bracket order fields
    stop_loss_price = Column(DECIMAL(12, 4), nullable=True)
    take_profit_price = Column(DECIMAL(12, 4), nullable=True)
    
    # Relaciones
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)
    
    # Relationships
    signal = relationship("Signal", back_populates="orders")
    user = relationship("User")
    portfolio = relationship("Portfolio")
    child_orders = relationship("Order", backref="parent_order", remote_side=[id])
    
    def __repr__(self):
        return f"<Order(id={self.id}, client_order_id='{self.client_order_id}', symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"
    
    @property
    def is_buy(self) -> bool:
        return self.side.lower() == "buy"
    
    @property
    def is_sell(self) -> bool:
        return self.side.lower() == "sell"
    
    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED
    
    @property
    def is_partial_fill(self) -> bool:
        return self.status == OrderStatus.PARTIALLY_FILLED
    
    @property
    def is_active(self) -> bool:
        active_statuses = [OrderStatus.NEW, OrderStatus.SENT, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED]
        return self.status in active_statuses
    
    @property
    def fill_percentage(self) -> float:
        if not self.quantity or self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity * 100)
    
    @property
    def remaining_quantity(self) -> float:
        return float(self.quantity - (self.filled_quantity or 0))
