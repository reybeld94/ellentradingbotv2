from __future__ import annotations

"""Kraken integration client used as the main broker interface."""

from types import SimpleNamespace
import asyncio
import json
from kraken.spot import SpotWSClient
from app.config import settings


class KrakenClient:
    def __init__(self) -> None:
        self.ws_client: SpotWSClient | None = None
        if settings.kraken_api_key and settings.kraken_secret_key:
            print("🔌 Kraken credentials detected, initializing websocket client...")
            self._init_client()
        else:
            print("⚠️ Kraken API credentials not provided; websocket client not initialized")

    def _init_client(self) -> None:
        print("🔗 Preparing Kraken websocket client...")
        self.ws_client = SpotWSClient(
            key=settings.kraken_api_key or "",
            secret=settings.kraken_secret_key or "",
        )

    def _ensure_client(self) -> None:
        if self.ws_client is None:
            print("🔒 Ensuring Kraken websocket client is initialized...")
            if not settings.kraken_api_key or not settings.kraken_secret_key:
                raise RuntimeError("Kraken API credentials not configured")
            self._init_client()

    async def _start_client(self):
        self._ensure_client()
        await self.ws_client.start()

    async def _stop_client(self):
        if self.ws_client:
            await self.ws_client.close()

    def refresh(self) -> None:
        """Recreate clients with current settings credentials."""
        print("🔄 Refreshing Kraken API clients...")
        if settings.kraken_api_key and settings.kraken_secret_key:
            self._init_client()
        else:
            print("❌ Credentials missing. Clearing Kraken clients")
            self.ws_client = None

    # --- Basic account helpers -------------------------------------------------
    def get_account(self):
        """Return a simplified account object with cash metrics via websocket."""
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "balances"})
            while True:
                msg = await self.ws_client._priv_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "balances":
                    bal = data.get("data", [{}])[0]
                    balance = bal.get("balance", {}) if isinstance(bal, dict) else {}
                    cash = float(balance.get("ZUSD", balance.get("USD", 0)))
                    await self._stop_client()
                    return SimpleNamespace(cash=cash, buying_power=cash, portfolio_value=cash)

        return asyncio.run(_fetch())

    def get_positions(self):
        """Return current asset balances as positions via websocket."""
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "balances"})
            while True:
                msg = await self.ws_client._priv_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "balances":
                    bal = data.get("data", [{}])[0]
                    balance = bal.get("balance", {}) if isinstance(bal, dict) else {}
                    await self._stop_client()
                    return [
                        SimpleNamespace(symbol=s, qty=float(q))
                        for s, q in balance.items()
                        if float(q) > 0
                    ]

        return asyncio.run(_fetch())

    def get_position(self, symbol: str):
        """Get balance for a single symbol via websocket."""
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "balances"})
            while True:
                msg = await self.ws_client._priv_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "balances":
                    bal = data.get("data", [{}])[0]
                    balance = bal.get("balance", {}) if isinstance(bal, dict) else {}
                    qty = float(balance.get(symbol, 0))
                    await self._stop_client()
                    if qty:
                        return SimpleNamespace(symbol=symbol, qty=qty)
                    return None

        return asyncio.run(_fetch())

    # --- Trading ---------------------------------------------------------------
    def is_crypto_symbol(self, symbol: str) -> bool:
        return True

    def submit_order(self, symbol, qty, side, order_type="market"):
        return self.submit_crypto_order(symbol, qty, side, order_type)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        """Create a crypto order on Kraken."""
        async def _send():
            await self._start_client()
            await self.ws_client.send_message(
                {
                    "method": "add_order",
                    "params": {
                        "symbol": symbol,
                        "side": side,
                        "order_qty": qty,
                        "order_type": order_type,
                    },
                }
            )
            await self._stop_client()
            return SimpleNamespace(id="", symbol=symbol, qty=qty, side=side)

        return asyncio.run(_send())

    # --- Market data -----------------------------------------------------------
    def get_latest_crypto_quote(self, symbol: str):
        """Fetch the latest ask and bid for ``symbol``."""
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "ticker", "symbol": [symbol]})
            while True:
                msg = await self.ws_client._pub_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "ticker" and data.get("symbol") == symbol:
                    ticker = data.get("data", [{}])[0]
                    ask = float(ticker.get("ask", ticker.get("a", 0)))
                    bid = float(ticker.get("bid", ticker.get("b", 0)))
                    await self._stop_client()
                    return SimpleNamespace(ask_price=ask, bid_price=bid)

        return asyncio.run(_fetch())

    def get_latest_quote(self, symbol: str):
        return self.get_latest_crypto_quote(symbol)

    # --- Misc -----------------------------------------------------------------
    def list_orders(self, status="all", limit=10):
        """List orders via websocket."""
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "executions"})
            collected = []
            while True:
                msg = await self.ws_client._priv_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "executions":
                    collected.extend(data.get("data", []))
                    if len(collected) >= limit:
                        await self._stop_client()
                        return collected[:limit]

        return asyncio.run(_fetch())

    def is_asset_fractionable(self, symbol):
        return True

    def check_crypto_status(self):
        return True

    def get_crypto_assets(self):
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "instrument"})
            while True:
                msg = await self.ws_client._pub_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "instrument":
                    await self._stop_client()
                    instruments = [d.get("symbol") for d in data.get("data", [])]
                    return instruments

        return asyncio.run(_fetch())

    def get_latest_trade(self, symbol):
        return self.get_latest_crypto_quote(symbol)

    def list_assets(self, status="active", asset_class="crypto"):
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "instrument"})
            while True:
                msg = await self.ws_client._pub_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "instrument":
                    await self._stop_client()
                    return [SimpleNamespace(symbol=d.get("symbol")) for d in data.get("data", [])]

        return asyncio.run(_fetch())

    def get_asset(self, symbol):
        async def _fetch():
            await self._start_client()
            await self.ws_client.subscribe({"channel": "instrument"})
            while True:
                msg = await self.ws_client._pub_conn.socket.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("channel") == "instrument":
                    for inst in data.get("data", []):
                        if inst.get("symbol") == symbol:
                            await self._stop_client()
                            return SimpleNamespace(symbol=symbol)
                    await self._stop_client()
                    return None

        return asyncio.run(_fetch())

    @property
    def api(self):
        return self.ws_client


# Global instance
kraken_client = KrakenClient()
