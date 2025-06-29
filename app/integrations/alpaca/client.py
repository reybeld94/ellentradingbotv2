import alpaca_trade_api as tradeapi
from ...config import settings


class AlpacaClient:
    def __init__(self):
        self.api = tradeapi.REST(
            settings.alpaca_api_key,
            settings.alpaca_secret_key,
            settings.alpaca_base_url,
            api_version='v2'
        )

    def get_account(self):
        """Obtener información de la cuenta"""
        return self.api.get_account()

    def get_positions(self):
        """Obtener posiciones actuales"""
        return self.api.list_positions()

    def get_position(self, symbol):
        """Obtener posición específica"""
        try:
            return self.api.get_position(symbol)
        except Exception:
            return None

    def submit_order(self, symbol, qty, side, order_type='market'):
        """Enviar orden (stocks y crypto)"""
        time_in_force = 'gtc' if '/' in symbol else 'day'  # GTC para crypto, DAY para stocks

        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )

    def submit_crypto_order(self, symbol, qty, side, order_type='market'):
        """Enviar orden de crypto específicamente"""
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force='gtc'  # Good Till Canceled para crypto
        )

    def get_latest_quote(self, symbol):
        """Obtener último precio (stocks)"""
        return self.api.get_latest_trade(symbol)

    def get_latest_crypto_quote(self, symbol):
        """Obtener último precio de crypto"""
        try:
            # Para crypto usar el endpoint específico
            return self.api.get_latest_crypto_trade(symbol)
        except Exception:
            # Fallback al método normal
            return self.api.get_latest_trade(symbol)


# Instancia global
alpaca_client = AlpacaClient()