import sys
import os
import types
import importlib.util
from pathlib import Path

# Ensure project root is in sys.path for tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use in-memory SQLite database for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Create lightweight app.execution package to avoid heavy dependencies
execution_pkg = types.ModuleType("app.execution")
execution_pkg.__path__ = []
sys.modules.setdefault("app.execution", execution_pkg)


def _load_module(fullname: str, path: str) -> None:
    spec = importlib.util.spec_from_file_location(fullname, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    sys.modules[fullname] = module


_load_module("app.execution.order_executor", str(ROOT / "app/execution/order_executor.py"))
_load_module(
    "app.execution.bracket_order_processor", str(ROOT / "app/execution/bracket_order_processor.py")
)
_load_module("app.execution.order_manager", str(ROOT / "app/execution/order_manager.py"))
from datetime import datetime
from app.models.trades import Trade


def create_test_trade(db_session, user_id, portfolio_id, **kwargs):
    trade = Trade(
        user_id=user_id,
        portfolio_id=portfolio_id,
        symbol=kwargs.get("symbol", "AAPL"),
        action=kwargs.get("action", "buy"),
        quantity=kwargs.get("quantity", 1),
        entry_price=kwargs.get("entry_price", 100.0),
        exit_price=kwargs.get("exit_price"),
        status=kwargs.get("status", "closed"),
        opened_at=kwargs.get("opened_at", datetime.utcnow()),
        closed_at=kwargs.get("closed_at"),
        pnl=kwargs.get("pnl", 0.0),
    )
    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)
    return trade
