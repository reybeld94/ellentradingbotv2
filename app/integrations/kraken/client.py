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
            self._init_clients()

    def _init_clients(self) -> None:
        self.market_client = Market()
        self.trade_client = Trade(
            key=settings.kraken_api_key,
            secret=settings.kraken_secret_key,
            url=settings.kraken_base_url,
        )
        self.user_client = User(
            key=settings.kraken_api_key,
            secret=settings.kraken_secret_key,
            url=settings.kraken_base_url,
        )

    def _ensure_clients(self) -> None:
        if self.trade_client is None:
            if not settings.kraken_api_key or not settings.kraken_secret_key:
                raise RuntimeError("Kraken API credentials not configured")
            self._init_clients()

    def refresh(self) -> None:
        """Recreate clients with current settings credentials."""
        if settings.kraken_api_key and settings.kraken_secret_key:
            self._init_clients()
        else:
            self.market_client = None
            self.trade_client = None
            self.user_client = None

    # --- Basic account helpers -------------------------------------------------
    def get_account(self):
        """Return a simplified account object with cash metrics."""
        self._ensure_clients()
        balances = self.user_client.get_account_balance()
        cash = float(balances.get("ZUSD", balances.get("USD", 0)))
        return SimpleNamespace(cash=cash, buying_power=cash, portfolio_value=cash)

    def get_positions(self):
        """Return current asset balances as positions."""
        self._ensure_clients()
        balances = self.user_client.get_account_balance()
        return [
            SimpleNamespace(symbol=s, qty=float(q))
            for s, q in balances.items()
            if float(q) > 0
        ]

    def get_position(self, symbol: str):
        """Get balance for a single symbol."""
        self._ensure_clients()
        qty = float(self.user_client.get_account_balance().get(symbol, 0))
        if qty:
            return SimpleNamespace(symbol=symbol, qty=qty)
        return None

    # --- Trading ---------------------------------------------------------------
    def is_crypto_symbol(self, symbol: str) -> bool:
        return True

    def submit_order(self, symbol, qty, side, order_type="market"):
        return self.submit_crypto_order(symbol, qty, side, order_type)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        """Create a crypto order on Kraken."""
        self._ensure_clients()
        resp = self.trade_client.create_order(
            pair=symbol,
            type=side,
            ordertype=order_type,
            volume=str(qty),
        )
        txid = ""
        if isinstance(resp, dict):
            txid = resp.get("result", {}).get("txid", "")
            if isinstance(txid, list):
                txid = txid[0]
        return SimpleNamespace(id=txid, symbol=symbol, qty=qty, side=side)

    # --- Market data -----------------------------------------------------------
    def get_latest_crypto_quote(self, symbol: str):
        """Fetch the latest ask and bid for ``symbol``."""
        self._ensure_clients()
        info = self.market_client.get_ticker(pair=symbol)
        data = next(iter(info.values()))
        ask = float(data["a"][0])
        bid = float(data["b"][0])
        return SimpleNamespace(ask_price=ask, bid_price=bid)

    def get_latest_quote(self, symbol: str):
        return self.get_latest_crypto_quote(symbol)

    # --- Misc -----------------------------------------------------------------
    def list_orders(self, status="all", limit=10):
        self._ensure_clients()
        orders = []
        if status in ("all", "open"):
            res = self.user_client.get_open_orders()
            orders.extend(res.get("open", {}).values())
        if status in ("all", "closed"):
            res = self.user_client.get_closed_orders()
            orders.extend(res.get("closed", {}).values())
        return orders[:limit]

    def is_asset_fractionable(self, symbol):
        return True

    def check_crypto_status(self):
        return True

    def get_crypto_assets(self):
        self._ensure_clients()
        assets = self.market_client.get_assets()
        return list(assets.keys())

    def get_latest_trade(self, symbol):
        return self.get_latest_crypto_quote(symbol)

    def list_assets(self, status="active", asset_class="crypto"):
        self._ensure_clients()
        assets = self.market_client.get_assets()
        return [SimpleNamespace(symbol=s) for s in assets.keys()]

    def get_asset(self, symbol):
        self._ensure_clients()
        assets = self.market_client.get_assets()
        if symbol in assets:
            return SimpleNamespace(symbol=symbol)
        return None

    @property
    def api(self):
        return self.trade_client


# Global instance
kraken_client = KrakenClient()
