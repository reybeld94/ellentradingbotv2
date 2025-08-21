from datetime import datetime
import statistics
from sqlalchemy.orm import Session
from app.models.trades import Trade



class TradeService:
    SYMBOL_MAP = {
        'BTCUSD': 'BTC/USD',
        'ETHUSD': 'ETH/USD',
        'SOLUSD': 'SOL/USD',
        'BCHUSD': 'BCH/USD',
    }

    def __init__(self, db: Session):
        self.db = db
        from app.integrations import broker_client
        self.broker = broker_client

    def _map_symbol(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol, symbol)

    def _get_current_price(self, symbol: str) -> float:
        try:
            if self.broker.is_crypto_symbol(symbol):
                quote = self.broker.get_latest_crypto_quote(symbol)
                price = float(
                    getattr(quote, "ask_price", getattr(quote, "ap", 0)) or 0
                )
                if not price:
                    price = float(
                        getattr(quote, "bid_price", getattr(quote, "bp", 0)) or 0
                    )
            else:
                quote = self.broker.get_latest_quote(symbol)
                price = float(getattr(quote, "ask_price", 0) or 0)
                if not price:
                    price = float(getattr(quote, "bid_price", 0) or 0)
                if not price:
                    trade = self.broker.get_latest_trade(symbol)
                    price = float(getattr(trade, "price", getattr(trade, "p", 0)) or 0)
            return price
        except Exception:
            return 0.0

    def _fetch_position(self, symbol: str):
        """Get position for ``symbol`` trying both crypto formats."""
        position = self.broker.get_position(symbol)
        if position is None:
            if '/' in symbol:
                alt_symbol = symbol.replace('/', '')
            else:
                if len(symbol) > 3:
                    alt_symbol = f"{symbol[:-3]}/{symbol[-3:]}"
                else:
                    alt_symbol = None
            if alt_symbol:
                position = self.broker.get_position(alt_symbol)
        return position

    def refresh_user_trades(self, user_id: int, portfolio_id: int) -> None:
        open_trades = (
            self.db.query(Trade)
            .filter(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.status == "open",
            )
            .all()
        )

        # Ensure broker connectivity, ignore errors as trade status is managed
        # internally now
        try:
            self.broker.list_orders(status="open", limit=50)
        except Exception:
            pass

        for trade in open_trades:
            broker_symbol = self._map_symbol(trade.symbol)
            price = self._get_current_price(broker_symbol)
            # Calcular PnL total del trade desde el precio de entrada
            trade.pnl = (price - trade.entry_price) * trade.quantity

        self.db.commit()

    def get_equity_curve(
        self,
        user_id: int,
        portfolio_id: int,
        strategy_id: str | None = None,
    ):
        """Return equity curve data for the given user.

        If ``strategy_id`` is provided only trades for that strategy will be
        considered.
        """
        # Ensure trade information is up to date
        self.refresh_user_trades(user_id, portfolio_id)

        query = (
            self.db.query(Trade)
            .filter(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
            )
            .filter(Trade.status == "closed")
        )

        if strategy_id is not None:
            query = query.filter(Trade.strategy_id == strategy_id)

        trades = query.order_by(Trade.closed_at).all()

        equity_curve = []
        cumulative = 0.0
        for trade in trades:
            pnl = trade.pnl or 0.0
            cumulative += pnl
            timestamp = trade.closed_at or trade.opened_at
            equity_curve.append(
                {
                    "strategy_id": trade.strategy_id,
                    "timestamp": timestamp,
                    "equity": cumulative,
                }
            )
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

    def _trade_returns(self, trades):
        """Helper to compute fractional returns for trades."""
        returns = []
        for t in trades:
            if t.entry_price and t.quantity:
                capital = t.entry_price * t.quantity
                if capital != 0:
                    returns.append((t.pnl or 0.0) / capital)
        return returns

    def calculate_sharpe_ratio(self, strategy_id: str, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio using trade returns."""
        trades = self._get_strategy_trades(strategy_id)
        returns = self._trade_returns(trades)
        if not returns:
            return 0.0
        rf_per_trade = risk_free_rate / 252
        mean_ret = statistics.mean(returns)
        if len(returns) == 1:
            return 0.0
        std_dev = statistics.stdev(returns)
        if std_dev == 0:
            return 0.0
        return (mean_ret - rf_per_trade) / std_dev

    def calculate_sortino_ratio(self, strategy_id: str, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino Ratio using negative trade returns."""
        trades = self._get_strategy_trades(strategy_id)
        returns = self._trade_returns(trades)
        if not returns:
            return 0.0
        rf_per_trade = risk_free_rate / 252
        mean_ret = statistics.mean(returns)
        downside = [r for r in returns if r < 0]
        if len(downside) < 2:
            return 0.0
        downside_dev = statistics.stdev(downside)
        if downside_dev == 0:
            return 0.0
        return (mean_ret - rf_per_trade) / downside_dev

    def calculate_avg_win_loss(self, strategy_id: str) -> dict:
        """Return average win/loss and ratio."""
        trades = self._get_strategy_trades(strategy_id)
        wins = [t.pnl or 0.0 for t in trades if (t.pnl or 0.0) > 0]
        losses = [-(t.pnl or 0.0) for t in trades if (t.pnl or 0.0) < 0]
        avg_win = statistics.mean(wins) if wins else 0.0
        avg_loss = statistics.mean(losses) if losses else 0.0
        wl_ratio = (avg_win / avg_loss) if avg_loss != 0 else 0.0
        return {"avg_win": avg_win, "avg_loss": avg_loss, "win_loss_ratio": wl_ratio}

    def calculate_expectancy(self, strategy_id: str) -> float:
        """Expected value per trade."""
        trades = self._get_strategy_trades(strategy_id)
        if not trades:
            return 0.0
        metrics = self.calculate_avg_win_loss(strategy_id)
        win_rate = self.calculate_win_rate(strategy_id)
        loss_rate = 1 - win_rate
        return win_rate * metrics["avg_win"] - loss_rate * metrics["avg_loss"]
