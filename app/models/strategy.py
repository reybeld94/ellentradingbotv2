from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship, foreign

from app.database import Base
from app.utils.time import now_eastern


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)

    # Configuración de reglas
    entry_rules = Column(JSON, nullable=False)  # {"indicators": [], "conditions": []}
    exit_rules = Column(JSON, nullable=False)  # {"stop_loss": 0.02, "take_profit": 0.04}
    risk_parameters = Column(JSON, nullable=False)  # {"max_position_size": 0.05}
    position_sizing = Column(JSON, nullable=False)  # {"type": "fixed", "amount": 1000}

    # Estado y configuración
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_eastern)
    updated_at = Column(DateTime(timezone=True), default=now_eastern, onupdate=now_eastern)

    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="strategies")

    # Relación con señales y trades
    signals = relationship(
        "Signal",
        back_populates="strategy",
        cascade="all, delete-orphan",
        primaryjoin="Strategy.name==foreign(Signal.strategy_id)",
    )

    def __repr__(self) -> str:  # pragma: no cover - representación simple
        return f"<Strategy({self.name}, user:{self.user_id}, active:{self.is_active})>"

