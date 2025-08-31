import os
import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Ensure a lightweight SQLite database is used for the test
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test")

from app.execution.scheduler import ExecutionScheduler
import app.execution.trailing_stop_monitor as tsm


class DummyMonitor:
    def __init__(self, db):
        self.db = db

    def check_and_update_trailing_stops(self):
        return {"checked": 0, "updated": 0}


@pytest.mark.asyncio
async def test_run_trailing_stops_check_closes_db(monkeypatch):
    """Scheduler should close DB sessions to avoid pool growth."""
    engine = create_engine("sqlite://", poolclass=QueuePool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.execution.scheduler.get_db", override_get_db)
    monkeypatch.setattr(tsm, "TrailingStopMonitor", DummyMonitor)

    scheduler = ExecutionScheduler()
    scheduler.is_running = True

    initial_checkedout = engine.pool.checkedout()
    for _ in range(5):
        await scheduler.run_trailing_stops_check()
        assert engine.pool.checkedout() == initial_checkedout
