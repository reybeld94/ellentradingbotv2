# backend/app/integrations/alpaca/client.py

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest, StockLatestQuoteRequest
from ...config import settings


class AlpacaClient:
    def __init__(self):
        # Nuevo SDK alpaca-py
        self.trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=True  # True para paper trading
        )

        # Clientes para datos
        self.crypto_data_client = CryptoHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )

        self.stock_data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )

    def get_account(self):
        """Obtener información de la cuenta"""
        return self.trading_client.get_account()

    def get_positions(self):
        """Obtener posiciones actuales"""
        return self.trading_client.get_all_positions()

    def get_position(self, symbol):
        """Obtener posición específica"""
        try:
            return self.trading_client.get_open_position(symbol)
        except Exception:
            return None

    def is_crypto_symbol(self, symbol):
        """Verificar si es un símbolo de crypto basado en formato correcto"""
        return '/' in symbol

    def submit_order(self, symbol, qty, side, order_type='market'):
        """Enviar orden (stocks) con nuevo SDK"""

        print(f"📤 Submitting stock order: {side} {qty} {symbol}")

        # Convertir side a enum
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL

        # Para stocks usar DAY
        time_in_force = TimeInForce.DAY

        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=time_in_force
        )

        return self.trading_client.submit_order(order_data=market_order_data)

    def submit_crypto_order(self, symbol, qty, side, order_type='market'):
        """Enviar orden de crypto con nuevo SDK"""

        print(f"📤 Submitting crypto order: {side} {qty} {symbol}")

        # Convertir side a enum
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL

        # Para crypto usar GTC
        time_in_force = TimeInForce.GTC

        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=time_in_force
        )

        return self.trading_client.submit_order(order_data=market_order_data)

    def get_latest_quote(self, symbol):
        """Obtener último precio (stocks)"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self.stock_data_client.get_stock_latest_quote(request)
            return quotes[symbol]
        except Exception as e:
            print(f"❌ Stock quote failed for {symbol}: {e}")
            raise

    def get_latest_crypto_quote(self, symbol):
        """Obtener último precio de crypto"""
        try:
            print(f"🔍 Getting crypto quote for: {symbol}")
            request = CryptoLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self.crypto_data_client.get_crypto_latest_quote(request)
            return quotes[symbol]
        except Exception as e:
            print(f"❌ Crypto quote failed for {symbol}: {e}")
            raise

    def list_orders(self, status='all', limit=10):
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus

        # FIX: Alpaca requiere status explícito
        if status == 'all':
            status_filter = QueryOrderStatus.CLOSED  # incluye ejecutadas
        elif status == 'open':
            status_filter = QueryOrderStatus.OPEN
        elif status == 'closed':
            status_filter = QueryOrderStatus.CLOSED
        else:
            status_filter = QueryOrderStatus.CLOSED  # fallback

        filter_request = GetOrdersRequest(status=status_filter, limit=limit)
        return self.trading_client.get_orders(filter=filter_request)

    def is_asset_fractionable(self, symbol):
        """Verificar si un activo es fraccionable"""
        try:
            asset = self.trading_client.get_asset(symbol)
            return asset.fractionable
        except Exception as e:
            print(f"❌ Error checking if {symbol} is fractionable: {e}")
            # Lista de activos conocidos como fraccionables
            known_fractionable = [
                'BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD',  # Crypto
                'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'MSFT'  # Stocks
            ]
            return symbol in known_fractionable

    def check_crypto_status(self):
        """Verificar el estado de crypto trading en la cuenta"""
        try:
            account = self.get_account()
            # FIXED: Usar el atributo correcto del nuevo SDK
            crypto_status = getattr(account, 'crypto_trading_enabled', False)
            print(f"🔍 Account crypto_trading_enabled: {crypto_status}")
            return crypto_status
        except Exception as e:
            print(f"❌ Error checking crypto status: {e}")
            return False

    def get_crypto_assets(self):
        """Obtener lista de activos crypto disponibles"""
        try:
            # Con nuevo SDK
            assets = self.trading_client.get_all_assets()
            crypto_assets = [asset for asset in assets if asset.asset_class == AssetClass.CRYPTO]

            print(f"📋 Available crypto assets: {len(crypto_assets)}")
            return crypto_assets
        except Exception as e:
            print(f"❌ Error getting crypto assets: {e}")
            return []

    def get_latest_trade(self, symbol):
        """Obtener último trade - Compatibilidad con código viejo"""
        if self.is_crypto_symbol(symbol):
            return self.get_latest_crypto_quote(symbol)
        else:
            return self.get_latest_quote(symbol)

    def list_assets(self, status='active', asset_class='us_equity'):
        """Listar activos - Compatibilidad"""
        try:
            from alpaca.trading.enums import AssetClass, AssetStatus

            # Mapear asset_class
            if asset_class == 'crypto':
                class_filter = AssetClass.CRYPTO
            elif asset_class == 'us_equity':
                class_filter = AssetClass.US_EQUITY
            else:
                class_filter = None

            # Mapear status
            if status == 'active':
                status_filter = AssetStatus.ACTIVE
            else:
                status_filter = None

            assets = self.trading_client.get_all_assets()

            # Filtrar manualmente ya que el SDK nuevo no tiene filtros directos
            filtered = []
            for asset in assets:
                if class_filter and asset.asset_class != class_filter:
                    continue
                if status_filter and asset.status != status_filter:
                    continue
                filtered.append(asset)

            return filtered
        except Exception as e:
            print(f"❌ Error listing assets: {e}")
            return []

    def get_asset(self, symbol):
        """Obtener activo específico"""
        try:
            return self.trading_client.get_asset(symbol)
        except Exception as e:
            print(f"❌ Error getting asset {symbol}: {e}")
            return None

    @property
    def api(self):
        """Compatibilidad con código viejo que usa .api"""
        return self.trading_client

# Instancia global
alpaca_client = AlpacaClient()