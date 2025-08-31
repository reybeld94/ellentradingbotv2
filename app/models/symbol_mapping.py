from sqlalchemy import Column, Integer, String
from app.database import Base


class SymbolMapping(Base):
    """Represents mapping from external symbols to broker symbols."""

    __tablename__ = "symbol_mappings"

    id = Column(Integer, primary_key=True, index=True)
    raw_symbol = Column(String(50), unique=True, nullable=False, index=True)
    broker_symbol = Column(String(50), nullable=False)
