import asyncio
import json

try:  # alpaca-py may not be installed during testing
    from alpaca.data.live import StockDataStream, CryptoDataStream
    from alpaca.trading.stream import TradingStream
except Exception:  # pragma: no cover - fallback for tests

    class _Dummy:
        def __init__(self, *_, **__):
            pass

        def subscribe_trades(self, *_, **__):
            pass

        async def _run_forever(self):
            await asyncio.sleep(0)

    StockDataStream = CryptoDataStream = _Dummy

    class TradingStream(_Dummy):
        def subscribe_trade_updates(self, *_, **__):
            pass


from app.config import settings
from app.websockets import ws_manager
from app.integrations.alpaca.client import alpaca_client
from app.services.position_manager import position_manager


class AlpacaStream:
    """Manage Alpaca data streaming and forward events via internal WebSocket."""

    def __init__(self) -> None:
        self.stock_stream = None
        self.crypto_stream = None
        self.trading_stream = None
        if settings.alpaca_api_key and settings.alpaca_secret_key:
            self._init_streams()
        self._stock_task: asyncio.Task | None = None
        self._crypto_task: asyncio.Task | None = None
        self._trading_task: asyncio.Task | None = None

    def _init_streams(self) -> None:
        self.stock_stream = StockDataStream(
            settings.alpaca_api_key, settings.alpaca_secret_key
        )
        self.crypto_stream = CryptoDataStream(
            settings.alpaca_api_key, settings.alpaca_secret_key
        )
        self.trading_stream = TradingStream(
            settings.alpaca_api_key,
            settings.alpaca_secret_key,
            paper=True,
        )
        self.trading_stream.subscribe_trade_updates(self._handle_trade_update)
        if hasattr(self.trading_stream, "subscribe_account_updates"):
            self.trading_stream.subscribe_account_updates(self._handle_trade_update)

    def _cancel_tasks(self) -> None:
        for task in (self._stock_task, self._crypto_task, self._trading_task):
            if task is not None:
                task.cancel()
        self._stock_task = self._crypto_task = self._trading_task = None

    def stop(self) -> None:
        """Cancel any running stream tasks and clear stream objects."""
        self._cancel_tasks()
        self.stock_stream = None
        self.crypto_stream = None
        self.trading_stream = None

    def refresh(self) -> None:
        """Recreate stream clients based on current settings."""
        self.stop()
        if settings.alpaca_api_key and settings.alpaca_secret_key:
            self._init_streams()

    async def _handle_trade(self, trade) -> None:
        """Broadcast trade updates to all websocket clients."""
        await ws_manager.broadcast(
            json.dumps({"event": "quote_update", "payload": trade.__dict__})
        )

    async def _handle_trade_update(self, update) -> None:
        """Handle account or trade updates from TradingStream."""
        await self._broadcast_account_update()

    async def _broadcast_account_update(self) -> None:
        """Fetch account metrics and broadcast them."""
        account = alpaca_client.get_account()
        summary = position_manager.get_portfolio_summary()
        payload = {
            "portfolio_value": float(getattr(account, "portfolio_value", 0)),
            "cash": float(getattr(account, "cash", 0)),
            "buying_power": float(getattr(account, "buying_power", 0)),
            "total_positions": summary.get("total_positions", 0),
        }
        await ws_manager.broadcast(
            json.dumps({"event": "account_update", "payload": payload})
        )

    def _ensure_tasks(self) -> None:
        if not self.stock_stream or not self.crypto_stream or not self.trading_stream:
            return
        loop = asyncio.get_running_loop()
        if self._stock_task is None:
            self._stock_task = loop.create_task(self.stock_stream._run_forever())
        if self._crypto_task is None:
            self._crypto_task = loop.create_task(self.crypto_stream._run_forever())
        if self._trading_task is None:
            self._trading_task = loop.create_task(self.trading_stream._run_forever())

    def start(self) -> None:
        """Start background tasks without subscribing to any symbol."""
        self._ensure_tasks()

    def subscribe(self, symbol: str) -> None:
        """Subscribe to real time trades for a symbol."""
        if not self.crypto_stream or not self.stock_stream:
            return
        if "/" in symbol:
            self.crypto_stream.subscribe_trades(self._handle_trade, symbol)
        else:
            self.stock_stream.subscribe_trades(self._handle_trade, symbol)
        self._ensure_tasks()


alpaca_stream = AlpacaStream()
