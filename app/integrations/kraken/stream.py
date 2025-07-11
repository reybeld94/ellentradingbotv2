import asyncio
import json
from app.config import settings
from app.websockets import ws_manager
from app.integrations.kraken.client import kraken_client
from app.services.position_manager import position_manager
try:
    # Newer versions of python-kraken-sdk (>=3.x)
    from kraken.spot import SpotWSClient
except (ImportError, AttributeError):  # pragma: no cover - fallback for older versions
    try:  # Older (<3.x) versions expose the client in the client module
        from kraken.spot.client import KrakenSpotWSClient as SpotWSClient
    except (ImportError, AttributeError):
        try:
            # Very old versions (<1.x) provide the class in the ws_client package
            from kraken.spot.ws_client.ws_client import SpotWsClientCl as SpotWSClient
        except (ImportError, AttributeError):  # pragma: no cover - optional dep missing
            SpotWSClient = None  # type: ignore[misc]


class KrakenStream:
    """Simplified stream manager for Kraken."""

    def __init__(self) -> None:
        self._running_task: asyncio.Task | None = None
        self._ws: object | None = None

    def refresh(self) -> None:
        """No-op refresh to keep API parity."""
        pass

    def stop(self) -> None:
        if self._running_task is not None:
            self._running_task.cancel()
            self._running_task = None

    def start(self) -> None:
        if self._running_task is None:
            loop = asyncio.get_event_loop()
            self._running_task = loop.create_task(self._run())

    async def _run(self) -> None:
        if (
            SpotWSClient is not None
            and settings.kraken_api_key
            and settings.kraken_secret_key
        ):
            self._ws = SpotWSClient(
                key=settings.kraken_api_key,
                secret=settings.kraken_secret_key,
                callback=self._on_ws_message,
            )
            await self._ws.subscribe({"name": "ownTrades"})
            await self._ws.subscribe({"name": "balances"})
            # keep connection running
            while True:
                await asyncio.sleep(0.1)
        else:
            # fallback: periodically poll account to simulate real time
            while True:
                await self._broadcast_account_update()
                await asyncio.sleep(5)

    def subscribe(self, symbol: str) -> None:
        self.start()

    async def _broadcast_account_update(self) -> None:
        account = kraken_client.get_account()
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

    async def _on_ws_message(self, message: dict) -> None:
        if isinstance(message, dict):
            channel = message.get("channel")
            if channel == "ownTrades":
                await self._handle_trade_update(message)
            elif channel == "balances":
                await self._broadcast_account_update()


kraken_stream = KrakenStream()
