from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.signals.processor import WebhookProcessor
from app.schemas.webhook import TradingViewWebhook
from app.services.exit_rules_service import ExitRulesService
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.risk_limit import RiskLimit
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest


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


@pytest.fixture
def test_user(db_session):
    user = User(email="test@example.com", username="testuser", password_hash="test", is_verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name="test_portfolio",
        api_key_encrypted="key",
        secret_key_encrypted="secret",
        base_url="http://example.com",
        broker="alpaca",
        is_active=True,
        user_id=test_user.id,
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # Crear límites de riesgo amplios para que pase el risk manager
    risk_limit = RiskLimit(
        user_id=test_user.id,
        portfolio_id=portfolio.id,
        trading_start_time="00:00:00",
        trading_end_time="23:59:59",
        allow_extended_hours=True,
    )
    db_session.add(risk_limit)
    db_session.commit()
    return portfolio


@pytest.mark.asyncio
async def test_full_bracket_order_flow(db_session, test_user, test_portfolio, monkeypatch):
    """Test completo: Webhook -> Signal -> Risk -> Bracket Orders"""

    # 1. Crear reglas de salida para la estrategia
    exit_service = ExitRulesService(db_session)
    from app.models.strategy import Strategy
    strategy = Strategy(id=1, name="momentum_test")
    db_session.add(strategy)
    db_session.commit()
    exit_service.create_default_rules("1")

    # Asegurar que estamos dentro del horario de trading
    monkeypatch.setattr(
        "app.risk.manager.now_eastern",
        lambda: datetime(2024, 1, 2, 10, 0, tzinfo=ZoneInfo("America/New_York")),
    )

    # 2. Crear webhook de TradingView
    webhook_data = TradingViewWebhook(
        symbol="AAPL",
        action="buy",
        strategy_id="1",
        quantity=10,
        confidence=85,
        reason="breakout_signal",
    )

    # 3. Procesar con WebhookProcessor
    processor = WebhookProcessor(db_session)
    result = await processor.process_tradingview_webhook(webhook_data, test_user)

    # 4. Verificar resultados
    assert result["status"] == "success"
    assert result["signal_id"] is not None
    assert "bracket_orders" in result

    bracket_result = result["bracket_orders"]
    assert bracket_result["status"] == "success"
    assert bracket_result["orders_created"] == 3  # 1 entry + 1 SL + 1 TP

    # 5. Verificar que las órdenes se crearon en la base de datos
    from app.models.order import Order

    orders = db_session.query(Order).filter(Order.signal_id == result["signal_id"]).all()
    assert len(orders) == 3

    # Verificar tipos de órdenes
    order_types = [order.order_type for order in orders]
    assert "market" in order_types  # Entry order
    assert "stop" in order_types  # Stop loss
    assert "limit" in order_types  # Take profit

    print(f"✅ Full E2E test passed: {len(orders)} orders created")


def test_bracket_order_price_calculation():
    """Test de cálculo de precios de bracket orders"""
    from app.services.exit_rules_service import ExitRulesService

    # Simular reglas: SL=2%, TP=4%
    # Entrada=$100 -> SL=$98, TP=$104
    # (Se testea en isolation)
    pass
