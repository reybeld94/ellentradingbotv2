import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.analytics.portfolio_analytics import PortfolioAnalytics
from app.models.trades import Trade
from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio


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


def test_build_equity_curve(db_session, test_user, test_portfolio):
    """Test construcción de equity curve"""
    analytics = PortfolioAnalytics(db_session)

    trades_data = [
        {"pnl": 100.0, "opened_at": datetime.utcnow() - timedelta(days=5)},
        {"pnl": -50.0, "opened_at": datetime.utcnow() - timedelta(days=4)},
        {"pnl": 75.0, "opened_at": datetime.utcnow() - timedelta(days=3)},
        {"pnl": -25.0, "opened_at": datetime.utcnow() - timedelta(days=2)},
    ]

    for trade_data in trades_data:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            quantity=10,
            entry_price=100.0,
            status="filled",
            **trade_data,
        )
        db_session.add(trade)

    db_session.commit()

    base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    equity_curve = analytics._build_equity_curve(base_query)

    assert len(equity_curve) == 4
    assert equity_curve[0]["equity"] == 100.0
    assert equity_curve[1]["equity"] == 50.0
    assert equity_curve[2]["equity"] == 125.0
    assert equity_curve[3]["equity"] == 100.0

    assert "date" in equity_curve[0]
    assert "drawdown" in equity_curve[0]
    assert "symbol" in equity_curve[0]


def test_trade_distribution_analysis(db_session, test_user, test_portfolio):
    """Test análisis de distribución de trades"""
    analytics = PortfolioAnalytics(db_session)

    returns = [1.0, 1.5, 0.75, 2.0, -0.5, -0.25, -1.0, -0.75, 3.0, -1.5]

    for r in returns:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            quantity=1,
            entry_price=100.0,
            pnl=r * 100.0,
            status="filled",
        )
        db_session.add(trade)

    db_session.commit()

    base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    distribution = analytics._analyze_trade_distribution(base_query)

    assert distribution["total_winners"] == 5
    assert distribution["total_losers"] == 5
    assert len(distribution["win_distribution"]) > 0
    assert len(distribution["loss_distribution"]) > 0
    assert distribution["avg_winner"] > 0
    assert distribution["avg_loser"] < 0
