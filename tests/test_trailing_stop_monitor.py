import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.execution.trailing_stop_monitor import TrailingStopMonitor


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


def test_trailing_stop_monitor_creation(db_session):
    monitor = TrailingStopMonitor(db_session)
    assert monitor.db == db_session


def test_get_trailing_stops_summary(db_session):
    monitor = TrailingStopMonitor(db_session)
    summary = monitor.get_trailing_stops_summary()
    
    assert "total_active" in summary
    assert "by_symbol" in summary
    assert "by_strategy" in summary
