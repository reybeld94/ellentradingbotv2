# backend/app/services/position_manager.py

from ..integrations.alpaca.client import alpaca_client
from ..models.signal import Signal
import logging

logger = logging.getLogger(__name__)


class PositionManager:
    def __init__(self):
        self.alpaca = alpaca_client
        self.max_positions = 7  # Límite de posiciones simultáneas

    def get_current_positions(self):
        """Obtener todas las posiciones actuales"""
        try:
            positions = self.alpaca.get_positions()
            return {pos.symbol: float(pos.qty) for pos in positions}
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}

    def get_position_quantity(self, symbol):
        """Obtener cantidad específica de un símbolo"""
        try:
            position = self.alpaca.get_position(symbol)
            return float(position.qty) if position else 0.0
        except Exception:
            return 0.0

    def count_open_positions(self):
        """Contar posiciones abiertas"""
        positions = self.get_current_positions()
        return len([qty for qty in positions.values() if qty > 0])

    def validate_buy_signal(self, signal: Signal, calculated_quantity):
        """Validar señal de compra"""
        # 1. Verificar límite de posiciones
        current_positions = self.count_open_positions()
        current_qty = self.get_position_quantity(signal.symbol)

        # Si ya tenemos el símbolo, no cuenta como nueva posición
        if current_qty == 0 and current_positions >= self.max_positions:
            raise ValueError(f"Maximum positions limit reached ({self.max_positions}). Current: {current_positions}")

        # 2. Verificar efectivo disponible
        account = self.alpaca.get_account()
        available_cash = float(account.cash)

        # Estimar costo de la orden (precio aproximado)
        try:
            if self.is_crypto(signal.symbol):
                quote = self.alpaca.get_latest_crypto_quote(signal.symbol)
            else:
                quote = self.alpaca.get_latest_quote(signal.symbol)

            estimated_cost = float(quote.price) * calculated_quantity

            if estimated_cost > available_cash:
                raise ValueError(f"Insufficient cash. Need: ${estimated_cost:.2f}, Available: ${available_cash:.2f}")

        except Exception as e:
            logger.warning(f"Could not validate cash for {signal.symbol}: {e}")

        return True

    def validate_sell_signal(self, signal: Signal, calculated_quantity):
        """Validar señal de venta"""
        # 1. Verificar que tenemos posición del símbolo
        current_qty = self.get_position_quantity(signal.symbol)

        if current_qty <= 0:
            raise ValueError(f"No position found for {signal.symbol}. Cannot sell.")

        # 2. Verificar que no vendemos más de lo que tenemos
        if calculated_quantity > current_qty:
            raise ValueError(
                f"Cannot sell {calculated_quantity} shares. Only have {current_qty} shares of {signal.symbol}")

        return True

    def adjust_sell_quantity(self, signal: Signal, calculated_quantity):
        """Ajustar cantidad de venta si es necesario"""
        current_qty = self.get_position_quantity(signal.symbol)

        if current_qty <= 0:
            raise ValueError(f"No position to sell for {signal.symbol}")

        # Si intentamos vender más de lo que tenemos, vender todo
        if calculated_quantity > current_qty:
            logger.warning(f"Adjusting sell quantity for {signal.symbol}: {calculated_quantity} -> {current_qty}")
            return current_qty

        return calculated_quantity

    def is_crypto(self, symbol):
        """Verificar si es crypto"""
        return '/' in symbol or symbol.endswith('USD')

    def get_portfolio_summary(self):
        """Resumen del portafolio"""
        try:
            positions = self.get_current_positions()
            account = self.alpaca.get_account()

            return {
                "total_positions": len(positions),
                "max_positions": self.max_positions,
                "remaining_slots": max(0, self.max_positions - len(positions)),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "positions": positions
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}


# Instancia global
position_manager = PositionManager()

