from __future__ import annotations
"""Alpaca integration client used as the main broker interface."""

from types import SimpleNamespace

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
from alpaca.data import (
    StockHistoricalDataClient,
    CryptoHistoricalDataClient,
    StockLatestQuoteRequest,
    CryptoLatestQuoteRequest,
)

from app.config import settings


class AlpacaClient:
    def __init__(self) -> None:
        self.api_key = getattr(settings, "alpaca_api_key", None) or ""
        self.api_secret = getattr(settings, "alpaca_secret_key", None) or ""
        self.base_url = getattr(settings, "alpaca_base_url", None)
        self._trading: TradingClient | None = None
        self._stock_data: StockHistoricalDataClient | None = None
        self._crypto_data: CryptoHistoricalDataClient | None = None
        self.refresh()

    def refresh(self) -> None:
        """Refresh credentials from settings."""
        self.api_key = getattr(settings, "alpaca_api_key", None) or ""
        self.api_secret = getattr(settings, "alpaca_secret_key", None) or ""
        self.base_url = getattr(settings, "alpaca_base_url", None)
        if self.api_key and self.api_secret:
            self._trading = TradingClient(
                self.api_key,
                self.api_secret,
                paper=True,
                url_override=self.base_url,
            )
            self._stock_data = StockHistoricalDataClient(self.api_key, self.api_secret)
            self._crypto_data = CryptoHistoricalDataClient(self.api_key, self.api_secret)
            print("🔌 Alpaca credentials detected, REST client ready")
        else:
            self._trading = None
            self._stock_data = None
            self._crypto_data = None
            print("⚠️ Alpaca API credentials not provided; REST client not initialized")

    # --- Basic account helpers -------------------------------------------------
    def get_account(self):
        if not self._trading:
            raise RuntimeError("Alpaca API credentials not configured")
        acc = self._trading.get_account()
        return SimpleNamespace(
            cash=float(acc.cash),
            buying_power=float(acc.buying_power),
            portfolio_value=float(acc.portfolio_value),
        )

    def get_positions(self):
        if not self._trading:
            return []
        positions = self._trading.get_all_positions()
        return [SimpleNamespace(symbol=p.symbol, qty=float(p.qty)) for p in positions]

    def get_position(self, symbol: str):
        if not self._trading:
            return None
        try:
            p = self._trading.get_open_position(symbol)
            return SimpleNamespace(symbol=p.symbol, qty=float(p.qty))
        except Exception:
            return None

    # --- Trading --------------------------------------------------------------
    def submit_order(self, symbol, qty, side, order_type="market"):
        if not self._trading:
            raise RuntimeError("Alpaca API credentials not configured")
        order = self._trading.submit_order(symbol=symbol, qty=qty, side=side, type=order_type)
        return SimpleNamespace(id=order.id, symbol=symbol, qty=qty, side=side, status=order.status)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        return self.submit_order(symbol, qty, side, order_type)

    # --- Market data ----------------------------------------------------------
    def get_latest_quote(self, symbol: str):
        if not self._stock_data:
            raise RuntimeError("Alpaca API credentials not configured")
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        q = self._stock_data.get_stock_latest_quote(req)[symbol]
        return SimpleNamespace(ask_price=float(q.ask_price), bid_price=float(q.bid_price))

    def get_latest_crypto_quote(self, symbol: str):
        if not self._crypto_data:
            raise RuntimeError("Alpaca API credentials not configured")
        req = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
        q = self._crypto_data.get_crypto_latest_quote(req)[symbol]
        return SimpleNamespace(ask_price=float(q.ask_price), bid_price=float(q.bid_price))

    # --- Misc -----------------------------------------------------------------
    def list_orders(self, status="all", limit=10):
        if not self._trading:
            return []
        req = GetOrdersRequest(status=QueryOrderStatus(status), limit=limit)
        orders = self._trading.get_orders(req)
        return [
            SimpleNamespace(
                id=o.id,
                symbol=o.symbol,
                qty=float(o.qty),
                side=o.side,
                status=o.status,
            )
            for o in orders
        ]

    def is_asset_fractionable(self, symbol):
        if not self._trading:
            return True
        try:
            asset = self._trading.get_asset(symbol)
            return bool(getattr(asset, "fractionable", True))
        except Exception:
            return True

    def check_crypto_status(self):
        return True

    def get_crypto_assets(self):
        if not self._trading:
            return []
        assets = self._trading.get_all_assets(status="active", asset_class="crypto")
        return [a.symbol for a in assets]

    def get_latest_trade(self, symbol):
        return self.get_latest_crypto_quote(symbol)

    def list_assets(self, status="active", asset_class="us_equity"):
        if not self._trading:
            return []
        assets = self._trading.get_all_assets(status=status, asset_class=asset_class)
        return [SimpleNamespace(symbol=a.symbol) for a in assets]

    def get_asset(self, symbol):
        if not self._trading:
            return None
        try:
            a = self._trading.get_asset(symbol)
            return SimpleNamespace(symbol=a.symbol)
        except Exception:
            return None

    @property
    def api(self):
        return self._trading


alpaca_client = AlpacaClient()
