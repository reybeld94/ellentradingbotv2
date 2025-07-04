import asyncio
import json

try:  # alpaca-py may not be installed during testing
    from alpaca.data.live import StockDataStream, CryptoDataStream
except Exception:  # pragma: no cover - fallback for tests
    class _Dummy:
        def __init__(self, *_, **__):
            pass

        def subscribe_trades(self, *_, **__):
            pass

        async def _run_forever(self):
            await asyncio.sleep(0)

    StockDataStream = CryptoDataStream = _Dummy

from ...config import settings
from ...websockets import ws_manager


class AlpacaStream:
    """Manage Alpaca data streaming and forward events via internal WebSocket."""

    def __init__(self) -> None:
        self.stock_stream = StockDataStream(
            settings.alpaca_api_key, settings.alpaca_secret_key
        )
        self.crypto_stream = CryptoDataStream(
            settings.alpaca_api_key, settings.alpaca_secret_key
        )
        self._stock_task: asyncio.Task | None = None
        self._crypto_task: asyncio.Task | None = None

    async def _handle_trade(self, trade) -> None:
        """Broadcast trade updates to all websocket clients."""
        await ws_manager.broadcast(
            json.dumps({"event": "quote_update", "payload": trade.__dict__})
        )

    def _ensure_tasks(self) -> None:
        loop = asyncio.get_running_loop()
        if self._stock_task is None:
            self._stock_task = loop.create_task(self.stock_stream._run_forever())
        if self._crypto_task is None:
            self._crypto_task = loop.create_task(self.crypto_stream._run_forever())

    def start(self) -> None:
        """Start background tasks without subscribing to any symbol."""
        self._ensure_tasks()

    def subscribe(self, symbol: str) -> None:
        """Subscribe to real time trades for a symbol."""
        if "/" in symbol:
            self.crypto_stream.subscribe_trades(self._handle_trade, symbol)
        else:
            self.stock_stream.subscribe_trades(self._handle_trade, symbol)
        self._ensure_tasks()


alpaca_stream = AlpacaStream()

