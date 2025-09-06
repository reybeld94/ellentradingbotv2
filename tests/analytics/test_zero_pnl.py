import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.core.types import TradeStatus
from app.models.trades import Trade
from app.analytics.portfolio_analytics import PortfolioAnalytics


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
    user = User(email="zero@example.com", username="zerouser", password_hash="test", is_verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name="zero_portfolio",
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
    return portfolio


def test_monthly_returns_includes_zero_pnl(db_session, test_user, test_portfolio):
    analytics = PortfolioAnalytics(db_session)
    trade = Trade(
        user_id=test_user.id,
        portfolio_id=test_portfolio.id,
        symbol="AAPL",
        pnl=0.0,
        quantity=1,
        entry_price=100.0,
        status=TradeStatus.CLOSED,
        opened_at=datetime(2024, 1, 15),
    )
    db_session.add(trade)
    db_session.commit()

    query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    monthly_returns = analytics._get_monthly_returns(query)

    assert len(monthly_returns) == 1
    assert monthly_returns[0]["trades"] == 1
    assert monthly_returns[0]["pnl"] == 0.0


def test_risk_metrics_with_zero_pnl(db_session, test_user, test_portfolio):
    analytics = PortfolioAnalytics(db_session)
    trade1 = Trade(
        user_id=test_user.id,
        portfolio_id=test_portfolio.id,
        symbol="AAPL",
        pnl=0.0,
        quantity=1,
        entry_price=100.0,
        status=TradeStatus.CLOSED,
        opened_at=datetime.utcnow(),
    )
    trade2 = Trade(
        user_id=test_user.id,
        portfolio_id=test_portfolio.id,
        symbol="AAPL",
        pnl=50.0,
        quantity=1,
        entry_price=100.0,
        status=TradeStatus.CLOSED,
        opened_at=datetime.utcnow(),
    )
    db_session.add_all([trade1, trade2])
    db_session.commit()

    query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    risk_metrics = analytics._get_risk_metrics(query)

    assert risk_metrics
    assert "volatility" in risk_metrics


def test_risk_adjusted_returns_with_zero_pnl(db_session, test_user, test_portfolio):
    analytics = PortfolioAnalytics(db_session)
    for pnl in [0.0, 0.0]:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            pnl=pnl,
            quantity=1,
            entry_price=100.0,
            status=TradeStatus.CLOSED,
            opened_at=datetime.utcnow(),
        )
        db_session.add(trade)
    db_session.commit()

    query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    result = analytics._calculate_risk_adjusted_returns(query)

    assert "error" not in result
    assert "sharpe_ratio" in result
