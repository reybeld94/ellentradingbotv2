# backend/app/models/strategy_position.py

from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from app.utils.time import now_eastern
from app.database import Base


class StrategyPosition(Base):
    __tablename__ = "strategy_positions"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)  # Puede ser decimal para crypto
    avg_price = Column(Float, nullable=True)  # Precio promedio de compra
    total_invested = Column(Float, nullable=False, default=0.0)  # Total invertido
    created_at = Column(DateTime(timezone=True), default=now_eastern)
    updated_at = Column(DateTime(timezone=True), default=now_eastern, onupdate=now_eastern)

    # Constraint para evitar duplicados: una estrategia solo puede tener una posición por símbolo
    __table_args__ = (
        UniqueConstraint('strategy_id', 'symbol', name='uq_strategy_symbol'),
    )

    def __repr__(self):
        return f"<StrategyPosition({self.strategy_id}:{self.symbol}, qty:{self.quantity}, avg:{self.avg_price})>"
