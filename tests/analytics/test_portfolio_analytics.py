import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trades import Trade
from app.models.strategy import Strategy
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


def test_get_performance_metrics_counts(db_session, test_user, test_portfolio):
    analytics = PortfolioAnalytics(db_session)

    # Create trades with different outcomes
    create_test_trade(db_session, user_id=test_user.id, portfolio_id=test_portfolio.id, pnl=10.0)
    create_test_trade(db_session, user_id=test_user.id, portfolio_id=test_portfolio.id, pnl=-5.0)
    create_test_trade(db_session, user_id=test_user.id, portfolio_id=test_portfolio.id, pnl=0.0)

    metrics = analytics.get_performance_metrics(test_user.id, test_portfolio.id, "1M")

    assert metrics["total_trades"] == 3
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate"] == pytest.approx(33.33, rel=1e-2)


def test_strategy_performance_single_query(db_session, test_user, test_portfolio):
    strat_a = Strategy(
        name="s1",
        entry_rules={},
        exit_rules={},
        risk_parameters={},
        position_sizing={},
        user_id=test_user.id,
    )
    strat_b = Strategy(
        name="s2",
        entry_rules={},
        exit_rules={},
        risk_parameters={},
        position_sizing={},
        user_id=test_user.id,
    )
    db_session.add_all([strat_a, strat_b])
    db_session.commit()

    for i in range(1000):
        create_test_trade(
            db_session,
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            strategy_id=str(strat_a.id if i % 2 == 0 else strat_b.id),
            pnl=1.0 if i % 2 == 0 else -1.0,
        )

    analytics = PortfolioAnalytics(db_session)
    base_query = db_session.query(Trade).filter(
        Trade.user_id == test_user.id,
        Trade.portfolio_id == test_portfolio.id,
    )

    executed = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.lower().startswith("select"):
            executed.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", before_cursor_execute)
    analytics._get_strategy_performance(base_query)
    event.remove(db_session.bind, "before_cursor_execute", before_cursor_execute)

    assert len(executed) == 1
