from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.services.trade_service import TradeService
from app.services.order_executor import OrderExecutor
from app.services import symbol_mapper
from app.models.symbol_mapping import SymbolMapping


# Set up in-memory database shared across sessions
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Insert mapping using service function
with SessionLocal() as db:
    symbol_mapper.upsert_symbol_mapping("BCHUSD", "BCH/USD", db)

# Patch symbol mapper's SessionLocal to use testing session
symbol_mapper.SessionLocal = SessionLocal


def test_bchusd_mapping():
    service = TradeService.__new__(TradeService)
    with SessionLocal() as db:
        service.db = db
        assert service._map_symbol("BCHUSD") == "BCH/USD"

    oe = OrderExecutor()
    mapped = oe.map_symbol("BCHUSD")
    assert mapped == "BCH/USD"
