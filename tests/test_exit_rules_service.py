import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.exit_rules_service import ExitRulesService
from app.models.strategy_exit_rules import StrategyExitRules
from decimal import Decimal


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_default_rules(db_session):
    service = ExitRulesService(db_session)
    
    rules = service.create_default_rules("test_strategy")
    
    assert rules.id == "test_strategy"
    assert rules.stop_loss_pct == 0.02
    assert rules.take_profit_pct == 0.04
    assert rules.use_trailing == True


def test_calculate_exit_prices(db_session):
    service = ExitRulesService(db_session)
    
    # Crear reglas de prueba
    service.create_default_rules("test_strategy")
    
    # Calcular precios para entrada en $100
    result = service.calculate_exit_prices("test_strategy", Decimal("100"), "buy")

    assert result["entry_price"] == Decimal("100.00")
    assert result["stop_loss_price"] == Decimal("98.00")   # 100 * (1 - 0.02)
    assert result["take_profit_price"] == Decimal("104.00") # 100 * (1 + 0.04)
    assert result["strategy_id"] == "test_strategy"
