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
