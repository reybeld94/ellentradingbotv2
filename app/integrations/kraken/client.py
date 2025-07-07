from __future__ import annotations

"""Kraken integration client used as the main broker interface."""

from types import SimpleNamespace
from kraken.spot import Market, Trade, User
from app.config import settings


class KrakenClient:
    def __init__(self) -> None:
        self.market_client: Market | None = None
        self.trade_client: Trade | None = None
        self.user_client: User | None = None
        if settings.kraken_api_key and settings.kraken_secret_key:
            print("🔌 Kraken credentials detected, initializing REST client...")
            self._init_client()
        else:
            print("⚠️ Kraken API credentials not provided; REST client not initialized")

    def _init_client(self) -> None:
        print("🔗 Preparing Kraken REST clients...")
        self.market_client = Market(
            key=settings.kraken_api_key or "",
            secret=settings.kraken_secret_key or "",
            url=settings.kraken_base_url,
        )
        self.trade_client = Trade(
            key=settings.kraken_api_key or "",
            secret=settings.kraken_secret_key or "",
            url=settings.kraken_base_url,
        )
        self.user_client = User(
            key=settings.kraken_api_key or "",
            secret=settings.kraken_secret_key or "",
            url=settings.kraken_base_url,
        )

    def _ensure_client(self) -> None:
        if self.market_client is None or self.trade_client is None or self.user_client is None:
            print("🔒 Ensuring Kraken REST client is initialized...")
            if not settings.kraken_api_key or not settings.kraken_secret_key:
                raise RuntimeError("Kraken API credentials not configured")
            self._init_client()

    def refresh(self) -> None:
        """Recreate clients with current settings credentials."""
        print("🔄 Refreshing Kraken API clients...")
        if settings.kraken_api_key and settings.kraken_secret_key:
            self._init_client()
        else:
            print("❌ Credentials missing. Clearing Kraken clients")
            self.market_client = None
            self.trade_client = None
            self.user_client = None

    # --- Basic account helpers -------------------------------------------------
    def get_account(self):
        """Return a simplified account object with cash metrics using REST."""
        self._ensure_client()
        balances = self.user_client.get_account_balance()
        cash = float(balances.get("ZUSD", balances.get("USD", 0)))
        return SimpleNamespace(cash=cash, buying_power=cash, portfolio_value=cash)

    def get_positions(self):
        """Return current asset balances as positions using REST."""
        self._ensure_client()
        balances = self.user_client.get_account_balance()
        return [
            SimpleNamespace(symbol=s, qty=float(q))
            for s, q in balances.items()
            if float(q) > 0
        ]

    def get_position(self, symbol: str):
        """Get balance for a single symbol using REST."""
        self._ensure_client()
        balances = self.user_client.get_account_balance()
        qty = float(balances.get(symbol, 0))
        if qty:
            return SimpleNamespace(symbol=symbol, qty=qty)
        return None

    # --- Trading ---------------------------------------------------------------
    def is_crypto_symbol(self, symbol: str) -> bool:
        return True

    def submit_order(self, symbol, qty, side, order_type="market"):
        return self.submit_crypto_order(symbol, qty, side, order_type)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        """Create a crypto order on Kraken via REST."""
        self._ensure_client()
        resp = self.trade_client.create_order(
            ordertype=order_type,
            side=side,
            pair=symbol,
            volume=str(qty),
        )
        txids = resp.get("txid", [""])
        order_id = txids[0] if txids else ""
        return SimpleNamespace(id=order_id, symbol=symbol, qty=qty, side=side)

    # --- Market data -----------------------------------------------------------
    def get_latest_crypto_quote(self, symbol: str):
        """Fetch the latest ask and bid for ``symbol`` using REST."""
        self._ensure_client()
        data = self.market_client.get_ticker(pair=symbol)
        ticker = next(iter(data.values())) if isinstance(data, dict) else {}
        ask = float(ticker.get("ask", ticker.get("a", [0])[0] if isinstance(ticker.get("a", []), list) else ticker.get("a", 0)))
        bid = float(ticker.get("bid", ticker.get("b", [0])[0] if isinstance(ticker.get("b", []), list) else ticker.get("b", 0)))
        return SimpleNamespace(ask_price=ask, bid_price=bid)

    def get_latest_quote(self, symbol: str):
        return self.get_latest_crypto_quote(symbol)

    # --- Misc -----------------------------------------------------------------
    def list_orders(self, status="all", limit=10):
        """List orders via REST."""
        self._ensure_client()
        orders = []
        if status in ("open", "all"):
            data = self.user_client.get_open_orders()
            for oid, info in data.get("open", {}).items():
                orders.append(
                    SimpleNamespace(
                        id=oid,
                        symbol=info.get("descr", {}).get("pair"),
                        qty=float(info.get("vol", 0)),
                        side=info.get("descr", {}).get("type"),
                        status="open",
                    )
                )
        if status in ("closed", "all"):
            data = self.user_client.get_closed_orders()
            for oid, info in data.get("closed", {}).items():
                orders.append(
                    SimpleNamespace(
                        id=oid,
                        symbol=info.get("descr", {}).get("pair"),
                        qty=float(info.get("vol", 0)),
                        side=info.get("descr", {}).get("type"),
                        status=info.get("status", "closed"),
                    )
                )
        return orders[:limit]

    def is_asset_fractionable(self, symbol):
        return True

    def check_crypto_status(self):
        return True

    def get_crypto_assets(self):
        self._ensure_client()
        data = self.market_client.get_asset_pairs()
        return list(data.keys())

    def get_latest_trade(self, symbol):
        return self.get_latest_crypto_quote(symbol)

    def list_assets(self, status="active", asset_class="crypto"):
        self._ensure_client()
        pairs = self.market_client.get_asset_pairs()
        return [SimpleNamespace(symbol=s) for s in pairs.keys()]

    def get_asset(self, symbol):
        self._ensure_client()
        pairs = self.market_client.get_asset_pairs()
        if symbol in pairs:
            return SimpleNamespace(symbol=symbol)
        return None

    @property
    def api(self):
        return self.market_client


# Global instance
kraken_client = KrakenClient()
