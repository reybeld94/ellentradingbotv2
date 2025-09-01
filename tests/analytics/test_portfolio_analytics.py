import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.analytics.portfolio_analytics import PortfolioAnalytics
from tests.conftest import create_test_trade  # noqa: F401


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
    return portfolio


def test_portfolio_analytics_creation(db_session):
    analytics = PortfolioAnalytics(db_session)
    assert analytics.db == db_session


def test_get_performance_metrics_empty(db_session, test_user, test_portfolio):
    analytics = PortfolioAnalytics(db_session)
    metrics = analytics.get_performance_metrics(test_user.id, test_portfolio.id, "1M")

    assert metrics["total_pnl"] == 0.0
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["timeframe"] == "1M"
