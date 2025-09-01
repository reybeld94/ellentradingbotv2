import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.analytics.portfolio_analytics import PortfolioAnalytics
from app.models.trades import Trade
from app.models.risk_limit import RiskLimit


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


def test_get_risk_dashboard_data(db_session, test_user, test_portfolio):
  analytics = PortfolioAnalytics(db_session)

  trades_data = [
      {"pnl": 100.0, "symbol": "AAPL", "quantity": 10, "entry_price": 50.0, "opened_at": datetime.utcnow() - timedelta(days=5)},
      {"pnl": -50.0, "symbol": "TSLA", "quantity": 5, "entry_price": 200.0, "opened_at": datetime.utcnow() - timedelta(days=4)},
      {"pnl": 75.0, "symbol": "AAPL", "quantity": 8, "entry_price": 60.0, "opened_at": datetime.utcnow() - timedelta(days=3)},
      {"pnl": -25.0, "symbol": "MSFT", "quantity": 15, "entry_price": 80.0, "opened_at": datetime.utcnow() - timedelta(days=2)},
      {"pnl": 150.0, "symbol": "NVDA", "quantity": 3, "entry_price": 300.0, "opened_at": datetime.utcnow() - timedelta(days=1)}
  ]

  for trade_data in trades_data:
      trade = Trade(user_id=test_user.id, portfolio_id=test_portfolio.id, status="filled", **trade_data)
      db_session.add(trade)

  db_session.commit()

  risk_data = analytics.get_risk_dashboard_data(test_user.id, test_portfolio.id, "1M")

  expected_keys = [
      "risk_metrics", "var_analysis", "position_sizing", "symbol_exposure",
      "time_based_risk", "risk_adjusted_returns", "correlation_analysis", "timeframe"
  ]

  for key in expected_keys:
      assert key in risk_data

  assert "risk_score" in risk_data["risk_metrics"]
  assert "total_return" in risk_data["risk_metrics"]
  assert "volatility" in risk_data["risk_metrics"]


def test_advanced_risk_metrics_calculation(db_session, test_user, test_portfolio):
  analytics = PortfolioAnalytics(db_session)

  pnl_values = [100, -50, 75, -25, 150, -75, 200, -100, 80, -40]

  for i, pnl in enumerate(pnl_values):
      trade = Trade(
          user_id=test_user.id,
          portfolio_id=test_portfolio.id,
          symbol="TEST",
          pnl=pnl,
          quantity=10,
          entry_price=100.0,
          status="filled",
          opened_at=datetime.utcnow() - timedelta(days=10 - i)
      )
      db_session.add(trade)

  db_session.commit()

  base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
  risk_metrics = analytics._get_advanced_risk_metrics(base_query)

  assert risk_metrics["total_return"] == sum(pnl_values)
  assert risk_metrics["volatility"] > 0
  assert "sharpe_ratio" in risk_metrics
  assert "var_95" in risk_metrics
  assert "expected_shortfall_95" in risk_metrics
  assert "risk_score" in risk_metrics
  assert 0 <= risk_metrics["risk_score"]["score"] <= 100
  assert risk_metrics["risk_score"]["level"] in ["Low", "Moderate", "High", "Very High"]


def test_position_sizing_analysis(db_session, test_user, test_portfolio):
  analytics = PortfolioAnalytics(db_session)

  position_data = [
      {"quantity": 10, "entry_price": 50},
      {"quantity": 20, "entry_price": 150},
      {"quantity": 50, "entry_price": 200},
      {"quantity": 5, "entry_price": 100},
  ]

  for i, data in enumerate(position_data):
      trade = Trade(
          user_id=test_user.id,
          portfolio_id=test_portfolio.id,
          symbol=f"STOCK{i}",
          pnl=50.0,
          status="filled",
          **data
      )
      db_session.add(trade)

  db_session.commit()

  base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
  position_analysis = analytics._analyze_position_sizing(base_query)

  assert "position_analysis" in position_analysis
  assert "concentration_metrics" in position_analysis
  categories = [item["category"] for item in position_analysis["position_analysis"]]
  assert "Small (<$1K)" in categories
  assert "Medium ($1K-$5K)" in categories or "Very Large (>$10K)" in categories
  concentration = position_analysis["concentration_metrics"]
  assert concentration["max_position_size"] >= concentration["avg_position_size"]
  assert concentration["concentration_ratio"] >= 1.0


def test_symbol_exposure_analysis(db_session, test_user, test_portfolio):
  analytics = PortfolioAnalytics(db_session)

  symbol_data = [
      ("AAPL", [100, 50, -25]),
      ("TSLA", [-50, -30]),
      ("MSFT", [200]),
  ]

  for symbol, pnl_list in symbol_data:
      for pnl in pnl_list:
          trade = Trade(
              user_id=test_user.id,
              portfolio_id=test_portfolio.id,
              symbol=symbol,
              pnl=pnl,
              quantity=10,
              entry_price=100.0,
              status="filled"
          )
          db_session.add(trade)

  db_session.commit()

  base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
  exposure_analysis = analytics._analyze_symbol_exposure(base_query)

  symbols = [item["symbol"] for item in exposure_analysis]
  assert "AAPL" in symbols
  assert "TSLA" in symbols
  assert "MSFT" in symbols

  assert exposure_analysis[0]["pnl_contribution"] >= exposure_analysis[-1]["pnl_contribution"]

  aapl_data = next(item for item in exposure_analysis if item["symbol"] == "AAPL")
  assert aapl_data["trades"] == 3
  assert aapl_data["total_pnl"] == 125.0

