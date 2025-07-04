from datetime import datetime
from sqlalchemy.orm import Session
from ..models.trades import Trade
from ..integrations.alpaca.client import alpaca_client


class TradeService:
    SYMBOL_MAP = {
        'BTCUSD': 'BTC/USD',
        'ETHUSD': 'ETH/USD',
    }

    def __init__(self, db: Session):
        self.db = db
        self.alpaca = alpaca_client

    def _map_symbol(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol, symbol)

    def _get_current_price(self, symbol: str) -> float:
        try:
            if self.alpaca.is_crypto_symbol(symbol):
                quote = self.alpaca.get_latest_crypto_quote(symbol)
                return float(getattr(quote, 'ask_price', getattr(quote, 'ap', 0)))
            else:
                quote = self.alpaca.get_latest_quote(symbol)
                return float(quote.ask_price)
        except Exception:
            return 0.0

    def refresh_user_trades(self, user_id: int) -> None:
        open_trades = self.db.query(Trade).filter(Trade.user_id == user_id, Trade.status == 'open').all()
        for trade in open_trades:
            alpaca_symbol = self._map_symbol(trade.symbol)
            price = self._get_current_price(alpaca_symbol)
            position = self.alpaca.get_position(alpaca_symbol)
            if position is None:
                trade.exit_price = price
                trade.closed_at = datetime.utcnow()
                trade.status = 'closed'
            trade.pnl = (price - trade.entry_price) * trade.quantity
        self.db.commit()
