import pytest

from app.services.risk_manager import RiskManager


def test_smart_allocation_no_positions(monkeypatch):
    rm = RiskManager()
    monkeypatch.setattr(rm, "_get_open_positions_count", lambda: 0)
    qty = rm.calculate_optimal_position_size(price=100, buying_power=900, symbol="AAPL")
    assert qty == pytest.approx(3.0)


def test_smart_allocation_with_positions(monkeypatch):
    rm = RiskManager()
    monkeypatch.setattr(rm, "_get_open_positions_count", lambda: 2)
    qty = rm.calculate_optimal_position_size(price=100, buying_power=1000, symbol="MSFT")
    assert qty == pytest.approx(2.0)


def test_minimum_validation(monkeypatch):
    rm = RiskManager()
    monkeypatch.setattr(rm, "_get_open_positions_count", lambda: 0)
    # price so high that calculated quantity is below minimum
    qty = rm.calculate_optimal_position_size(price=1_000_000, buying_power=100, symbol="AAPL")
    assert qty == 0.0
    # price such that quantity exceeds minimum
    qty2 = rm.calculate_optimal_position_size(price=20, buying_power=100, symbol="AAPL")
    assert qty2 > 0.0


def test_reserved_slots_configuration():
    rm = RiskManager()
    rm.set_reserved_slots(5)
    assert rm.reserved_slots == 5
    with pytest.raises(ValueError):
        rm.set_reserved_slots(0)
    with pytest.raises(ValueError):
        rm.set_reserved_slots(11)

