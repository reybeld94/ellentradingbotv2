import os
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.order import Order
from app.core.types import OrderStatus
from app.execution import order_processor as op_module


def _setup_db():
    if os.path.exists("test.db"):
        os.remove("test.db")
    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    order = Order(
        client_order_id="o1",
        symbol="AAPL",
        side="buy",
        quantity=1,
        order_type="market",
        status=OrderStatus.NEW,
        signal_id=1,
        user_id=1,
    )
    session.add(order)
    session.commit()
    session.close()
    return TestingSession


class DummyBrokerExecutor:
    def __init__(self, db):
        self.db = db

    def execute_order(self, order):
        order.status = OrderStatus.ACCEPTED
        order.broker_order_id = f"B{order.id}"
        self.db.flush()
        time.sleep(0.2)
        return {"success": True, "broker_order_id": order.broker_order_id}


def test_process_single_order_concurrency(monkeypatch):
    TestingSession = _setup_db()

    monkeypatch.setattr(op_module, "BrokerExecutor", DummyBrokerExecutor)
    monkeypatch.setattr(op_module, "OrderManager", lambda db: None)

    def worker():
        session = TestingSession()
        processor = op_module.OrderProcessor(session)
        start = time.time()
        result = processor.process_single_order(1)
        duration = time.time() - start
        session.close()
        return result, duration

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker) for _ in range(2)]
        results = [f.result() for f in futures]

    durations = [d for _, d in results]
    # Ensure one thread waited for the other by checking duration spread
    assert max(durations) - min(durations) >= 0.15

    success_count = sum(1 for r, _ in results if r["success"])
    assert success_count == 2

    session = TestingSession()
    final_status = session.query(Order.status).filter(Order.id == 1).scalar()
    session.close()
    assert final_status == OrderStatus.ACCEPTED
