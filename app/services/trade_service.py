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
        open_trades = (
            self.db.query(Trade)
            .filter(Trade.user_id == user_id, Trade.status == "open")
            .all()
        )

        try:
            open_orders = self.alpaca.list_orders(status="open", limit=50)
            symbols_with_open_orders = {o.symbol for o in open_orders}
        except Exception:
            symbols_with_open_orders = set()

        for trade in open_trades:
            alpaca_symbol = self._map_symbol(trade.symbol)
            price = self._get_current_price(alpaca_symbol)
            position = self.alpaca.get_position(alpaca_symbol)

            if position is None and alpaca_symbol not in symbols_with_open_orders:
                trade.exit_price = price
                trade.closed_at = datetime.utcnow()
                trade.status = "closed"

            trade.pnl = (price - trade.entry_price) * trade.quantity

        self.db.commit()

    def get_equity_curve(self, user_id: int):
        """Return equity curve data for the given user."""
        # Ensure trade information is up to date
        self.refresh_user_trades(user_id)

        trades = (
            self.db.query(Trade)
            .filter(Trade.user_id == user_id)
            .filter(Trade.status == "closed")
            .order_by(Trade.closed_at)
            .all()
        )

        equity_curve = []
        cumulative = 0.0
        for trade in trades:
            pnl = trade.pnl or 0.0
            cumulative += pnl
            timestamp = trade.closed_at or trade.opened_at
            equity_curve.append({"timestamp": timestamp, "equity": cumulative})
        return equity_curve

    # New metrics calculation methods

    def _get_strategy_trades(self, strategy_id: str):
        """Return closed trades for a given strategy ordered by close time."""
        return (
            self.db.query(Trade)
            .filter(Trade.strategy_id == strategy_id)
            .filter(Trade.status == "closed")
            .order_by(Trade.closed_at)
            .all()
        )

    def calculate_total_pl(self, strategy_id: str) -> float:
        """Total profit or loss for the strategy."""
        trades = self._get_strategy_trades(strategy_id)
        return sum((t.pnl or 0.0) for t in trades)

    def calculate_win_rate(self, strategy_id: str) -> float:
        """Fraction of winning trades (0-1 scale)."""
        trades = self._get_strategy_trades(strategy_id)
        total = len(trades)
        if total == 0:
            return 0.0
        wins = sum(1 for t in trades if (t.pnl or 0.0) > 0)
        return wins / total

    def calculate_profit_factor(self, strategy_id: str) -> float:
        """Ratio of gross profit to gross loss."""
        trades = self._get_strategy_trades(strategy_id)
        total_profit = sum((t.pnl or 0.0) for t in trades if (t.pnl or 0.0) > 0)
        total_loss = sum(-(t.pnl or 0.0) for t in trades if (t.pnl or 0.0) < 0)
        if total_loss == 0:
            return 0.0
        return total_profit / total_loss

    def calculate_drawdown(self, strategy_id: str) -> float:
        """Maximum drawdown of the strategy's equity curve."""
        trades = self._get_strategy_trades(strategy_id)
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for trade in trades:
            cumulative += trade.pnl or 0.0
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown
        return -max_dd
