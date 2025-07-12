from app.services.trade_service import TradeService
from app.services.order_executor import OrderExecutor


def test_bchusd_mapping():
    service = TradeService.__new__(TradeService)
    assert service.SYMBOL_MAP.get('BCHUSD') == 'BCH/USD'

    oe = OrderExecutor()
    mapped = oe.map_symbol('BCHUSD')
    assert mapped == 'BCH/USD'
