from __future__ import annotations
"""Alpaca integration client used as the main broker interface."""

from types import SimpleNamespace
from datetime import datetime, time
from app.utils.time import EASTERN_TZ, now_eastern

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
from alpaca.data import (
    StockHistoricalDataClient,
    CryptoHistoricalDataClient,
    StockLatestQuoteRequest,
    CryptoLatestQuoteRequest,
    StockLatestTradeRequest,
    CryptoLatestTradeRequest,
)
from alpaca.common.exceptions import APIError

from app.config import settings


def _in_regular_trading_hours(now: datetime | None = None) -> bool:
    current = now.astimezone(EASTERN_TZ) if now else now_eastern()
    start = time(9, 30)
    end = time(16, 0)
    return current.weekday() < 5 and start <= current.time() < end


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
        paper_mode = getattr(settings, "alpaca_paper", None)
        if paper_mode is None:
            paper_mode = "paper" in (self.base_url or "").lower()
        if self.api_key and self.api_secret:
            self._trading = TradingClient(
                self.api_key,
                self.api_secret,
                paper=paper_mode,
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
        """Get all positions with complete information including unrealized PnL"""
        if not self._trading:
            return []
        positions = self._trading.get_all_positions()
        return [
            SimpleNamespace(
                symbol=p.symbol,
                qty=float(p.qty),
                market_value=float(getattr(p, "market_value", 0) or 0),
                unrealized_pl=float(getattr(p, "unrealized_pl", 0) or 0),  # SOLO PnL TOTAL
                unrealized_plpc=float(getattr(p, "unrealized_plpc", 0) or 0),
                cost_basis=float(getattr(p, "cost_basis", 0) or 0),
                avg_entry_price=float(getattr(p, "avg_entry_price", 0) or 0),
                current_price=float(getattr(p, "current_price", 0) or 0),
            )
            for p in positions
        ]

    def get_position(self, symbol: str):
        """Get single position with complete information"""
        if not self._trading:
            return None
        try:
            p = self._trading.get_open_position(symbol)
            return SimpleNamespace(
                symbol=p.symbol,
                qty=float(p.qty),
                market_value=float(getattr(p, "market_value", 0) or 0),
                unrealized_pl=float(getattr(p, "unrealized_pl", 0) or 0),  # SOLO PnL TOTAL
                unrealized_plpc=float(getattr(p, "unrealized_plpc", 0) or 0),
                cost_basis=float(getattr(p, "cost_basis", 0) or 0),
                avg_entry_price=float(getattr(p, "avg_entry_price", 0) or 0),
                current_price=float(getattr(p, "current_price", 0) or 0),
            )
        except Exception:
            return None

    # --- Trading --------------------------------------------------------------
    def submit_order(self, symbol, qty, side, order_type="market", price=None):
        if not self._trading:
            raise RuntimeError("Alpaca API credentials not configured")

        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        extended_hours = not _in_regular_trading_hours()

        if order_type == "market":
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                extended_hours=extended_hours,
            )
        else:
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=price,
                extended_hours=extended_hours,
            )

        order = self._trading.submit_order(order_data)
        return SimpleNamespace(id=order.id, symbol=symbol, qty=qty, side=side, status=order.status)

    def submit_crypto_order(self, symbol, qty, side, order_type="market"):
        return self.submit_order(symbol, qty, side, order_type)

    def is_crypto_symbol(self, symbol: str) -> bool:
        """Return True if ``symbol`` represents a crypto asset.

        Alpaca identifies crypto either with a slash (``BTC/USD``) or by
        concatenating the base and quote (``BTCUSD``). We use a simple heuristic
        to detect these formats so the service can choose the appropriate quote
        endpoint.
        """
        symbol = (symbol or "").upper()
        if "/" in symbol:
            return True
        return symbol.endswith(("USD", "USDT", "USDC"))

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

    def get_latest_trade(self, symbol: str):
        if self.is_crypto_symbol(symbol):
            if not self._crypto_data:
                raise RuntimeError("Alpaca API credentials not configured")
            req = CryptoLatestTradeRequest(symbol_or_symbols=symbol)
            t = self._crypto_data.get_crypto_latest_trade(req)[symbol]
            return SimpleNamespace(price=float(t.price))
        else:
            if not self._stock_data:
                raise RuntimeError("Alpaca API credentials not configured")
            req = StockLatestTradeRequest(symbol_or_symbols=symbol)
            t = self._stock_data.get_stock_latest_trade(req)[symbol]
            return SimpleNamespace(price=float(t.price))

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
        """Check if the account has crypto trading permissions.

        Attempts to retrieve the list of active crypto assets from Alpaca. If the
        request fails or returns an empty list, crypto trading is assumed to be
        unavailable.
        """
        if not self._trading:
            print("⚠️ Alpaca client not initialized; cannot check crypto status")
            return False
        try:
            assets = self._trading.get_all_assets(
                status="active", asset_class="crypto"
            )
            if not assets:
                print(
                    "⚠️ Crypto trading not enabled for this account or no assets returned"
                )
                return False
            return True
        except APIError as e:
            print(f"⚠️ Failed to fetch crypto assets: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Unexpected error checking crypto status: {e}")
            return False

    def get_crypto_assets(self):
        if not self._trading:
            return []
        assets = self._trading.get_all_assets(status="active", asset_class="crypto")
        return [a.symbol for a in assets]

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
