from __future__ import annotations

"""Kraken integration client used as the main broker interface."""

from types import SimpleNamespace
from urllib.parse import urlencode
import time
import hmac
import hashlib
import base64
import requests

from app.config import settings

# Kraken REST API base URL
DEFAULT_KRAKEN_BASE_URL = "https://api.kraken.com"

class KrakenClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.base_url = settings.kraken_base_url or DEFAULT_KRAKEN_BASE_URL
        self.api_key = settings.kraken_api_key or ""
        self.api_secret = settings.kraken_secret_key or ""
        if self.api_key and self.api_secret:
            print("🔌 Kraken credentials detected, REST client ready")
        else:
            print("⚠️ Kraken API credentials not provided; REST client not initialized")

    def _sign(self, urlpath: str, data: dict) -> str:
        nonce = data["nonce"]
        postdata = urlencode(data)
        message = (str(nonce) + postdata).encode()
        sha = hashlib.sha256(message).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), urlpath.encode() + sha, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()

    def _private_post(self, endpoint: str, data: dict | None = None) -> dict:
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Kraken API credentials not configured")
        data = data or {}
        data["nonce"] = str(int(time.time() * 1000))
        urlpath = f"/0/private/{endpoint}"
        url = self.base_url.rstrip("/") + urlpath
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign(urlpath, data),
        }
        resp = self.session.post(url, headers=headers, data=data)
        resp.raise_for_status()
        res = resp.json()
        if res.get("error"):
            raise RuntimeError(f"Kraken API error: {res['error']}")
        return res.get("result", {})

    def _public_get(self, endpoint: str, params: dict | None = None) -> dict:
        url = self.base_url.rstrip("/") + f"/0/public/{endpoint}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        res = resp.json()
        if res.get("error"):
            raise RuntimeError(f"Kraken API error: {res['error']}")
        return res.get("result", {})

    def refresh(self) -> None:
        """Refresh credentials from settings."""
        self.base_url = settings.kraken_base_url or DEFAULT_KRAKEN_BASE_URL
        self.api_key = settings.kraken_api_key or ""
        self.api_secret = settings.kraken_secret_key or ""

    # --- Basic account helpers -------------------------------------------------
    def get_account(self):
        """Return basic account information including portfolio value."""
        result = self._private_post("Balance")

        cash = float(result.get("ZUSD", result.get("USD", 0)))
        portfolio_value = cash

        for asset, qty in result.items():
            amount = float(qty)
            if amount <= 0 or asset in ("ZUSD", "USD"):
                continue

            pair = asset if asset.endswith("USD") else f"{asset}ZUSD"

            try:
                quote = self.get_latest_crypto_quote(pair)
                price = float(getattr(quote, "ask_price", getattr(quote, "ap", 0)))
                portfolio_value += price * amount
            except Exception:
                # Ignore pricing errors for unsupported assets
                continue

        return SimpleNamespace(cash=cash, buying_power=cash, portfolio_value=portfolio_value)

    def get_positions(self):
        result = self._private_post("Balance")
        return [
            SimpleNamespace(symbol=s, qty=float(q))
            for s, q in result.items()
            if float(q) > 0
        ]

    def get_position(self, symbol: str):
        balances = self._private_post("Balance")

        # Direct match first
        qty = float(balances.get(symbol, 0))
        if qty:
            return SimpleNamespace(symbol=symbol, qty=qty)

        # Try alternate asset representations for crypto pairs
        candidates = []
        if "/" in symbol:
            base = symbol.split("/")[0]
            candidates.extend([base, f"X{base}", f"X{base}ZUSD"])
        elif symbol.upper().endswith("USD") and len(symbol) > 3:
            base = symbol[:-3]
            candidates.extend([base, f"X{base}", f"X{base}ZUSD"])
        else:
            candidates.append(f"X{symbol}")

        for alt in candidates:
            qty = float(balances.get(alt, 0))
            if qty:
                return SimpleNamespace(symbol=alt, qty=qty)

        return None

    # --- Trading ---------------------------------------------------------------
    def is_crypto_symbol(self, symbol: str) -> bool:
        return True

    def submit_order(self, symbol, qty, side, order_type="market"):
        return self.submit_crypto_order(symbol, qty, side, order_type)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        data = {
            "pair": symbol,
            "type": side,
            "ordertype": order_type,
            "volume": str(qty),
        }
        result = self._private_post("AddOrder", data)
        txids = result.get("txid", [""])
        order_id = txids[0] if txids else ""
        return SimpleNamespace(id=order_id, symbol=symbol, qty=qty, side=side)

    # --- Market data -----------------------------------------------------------
    def get_latest_crypto_quote(self, symbol: str):
        data = self._public_get("Ticker", {"pair": symbol})
        ticker = next(iter(data.values())) if isinstance(data, dict) else {}
        a = ticker.get("a", [])
        b = ticker.get("b", [])
        ask = float(a[0]) if isinstance(a, list) and a else float(a or 0)
        bid = float(b[0]) if isinstance(b, list) and b else float(b or 0)
        return SimpleNamespace(ask_price=ask, bid_price=bid)

    def get_latest_quote(self, symbol: str):
        return self.get_latest_crypto_quote(symbol)

    # --- Misc ------------------------------------------------------------------
    def list_orders(self, status="all", limit=10):
        orders = []
        if status in ("open", "all"):
            data = self._private_post("OpenOrders")
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
            data = self._private_post("ClosedOrders")
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
        data = self._public_get("AssetPairs")
        return list(data.keys())

    def get_latest_trade(self, symbol):
        return self.get_latest_crypto_quote(symbol)

    def list_assets(self, status="active", asset_class="crypto"):
        data = self._public_get("AssetPairs")
        return [SimpleNamespace(symbol=s) for s in data.keys()]

    def get_asset(self, symbol):
        data = self._public_get("AssetPairs")
        if symbol in data:
            return SimpleNamespace(symbol=symbol)
        return None

    @property
    def api(self):
        return self


# Global instance
kraken_client = KrakenClient()
