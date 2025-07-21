import asyncio
import json

from alpaca.trading.stream import TradingStream

from app.config import settings
from app.websockets import ws_manager
from app.integrations.alpaca.client import alpaca_client
from app.services.position_manager import position_manager


class AlpacaStream:
    """Simplified stream manager for Alpaca."""

    def __init__(self) -> None:
        self._running_task: asyncio.Task | None = None
        self._stream: TradingStream | None = None

    def refresh(self) -> None:
        if self._stream:
            self.stop()
        key = getattr(settings, "alpaca_api_key", None)
        secret = getattr(settings, "alpaca_secret_key", None)
        if key and secret:
            base_url = getattr(settings, "alpaca_base_url", None) or ""
            paper_mode = getattr(settings, "alpaca_paper", None)
            if paper_mode is None:
                paper_mode = "paper" in base_url.lower()
            self._stream = TradingStream(key, secret, paper=paper_mode)
        else:
            self._stream = None

    def stop(self) -> None:
        if self._running_task is not None:
            self._running_task.cancel()
            self._running_task = None

    def start(self) -> None:
        if self._running_task is None:
            loop = asyncio.get_event_loop()
            self._running_task = loop.create_task(self._run())

    async def _run(self) -> None:
        if self._stream is not None:
            self._stream.subscribe_trade_updates(self._on_trade_update)
            await self._stream._run_forever()
        else:
            while True:
                await self._broadcast_account_update()
                await asyncio.sleep(5)

    def subscribe(self, symbol: str) -> None:
        self.start()

    async def _broadcast_account_update(self) -> None:
        account = alpaca_client.get_account()
        summary = position_manager.get_portfolio_summary()
        payload = {
            "portfolio_value": float(getattr(account, "portfolio_value", 0)),
            "cash": float(getattr(account, "cash", 0)),
            "buying_power": float(getattr(account, "buying_power", 0)),
            "total_positions": summary.get("total_positions", 0),
        }
        await ws_manager.broadcast(json.dumps({"event": "account_update", "payload": payload}))

    async def _handle_trade_update(self, update) -> None:
        await self._broadcast_account_update()

    async def _on_trade_update(self, data) -> None:
        await self._handle_trade_update(data)


alpaca_stream = AlpacaStream()
