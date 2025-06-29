# backend/app/services/order_executor.py

from sqlalchemy.orm import Session
from ..integrations.alpaca.client import alpaca_client
from ..models.signal import Signal
from ..config import settings
from .position_manager import position_manager
from .strategy_position_manager import StrategyPositionManager
from ..database import get_db
import logging

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self):
        self.alpaca = alpaca_client
        self.position_manager = position_manager

    def is_crypto(self, symbol):
        """Verificar si es un símbolo de crypto"""
        return '/' in symbol or symbol.endswith('USD')

    def calculate_position_size(self, symbol, action):
        """Calcular tamaño de posición (10% del capital)"""
        account = self.alpaca.get_account()
        buying_power = float(account.buying_power)

        # 10% del capital total
        position_value = buying_power * 0.10

        # Obtener precio actual
        if self.is_crypto(symbol):
            quote = self.alpaca.get_latest_crypto_quote(symbol)
        else:
            quote = self.alpaca.get_latest_quote(symbol)

        current_price = float(quote.price)

        # Para crypto, permitir decimales
        if self.is_crypto(symbol):
            quantity = round(position_value / current_price, 6)  # 6 decimales para crypto
            return max(0.000001, quantity)  # Mínimo muy pequeño para crypto
        else:
            # Para stocks, solo enteros
            quantity = int(position_value / current_price)
            return max(1, quantity)  # Mínimo 1 acción

    def execute_signal(self, signal: Signal):
        """Ejecutar señal con gestión por estrategia"""
        # Obtener sesión de base de datos
        db = next(get_db())
        strategy_manager = StrategyPositionManager(db)

        try:
            # Calcular cantidad si no se especificó
            if not signal.quantity:
                signal.quantity = self.calculate_position_size(signal.symbol, signal.action)

            if signal.action.lower() == 'buy':
                # COMPRA: Validaciones básicas + ejecutar
                self._execute_buy_signal(signal, strategy_manager)

            elif signal.action.lower() == 'sell':
                # VENTA: Solo vender lo que esta estrategia tiene
                self._execute_sell_signal(signal, strategy_manager)

            # Actualizar señal con resultado
            signal.status = "processed"
            signal.error_message = None

            logger.info(f"Order processed: {signal.strategy_id} {signal.action} {signal.symbol}")
            return True

        except Exception as e:
            signal.status = "error"
            signal.error_message = str(e)
            logger.error(f"Error executing signal for {signal.strategy_id}:{signal.symbol}: {e}")
            raise
        finally:
            db.close()

    def _execute_buy_signal(self, signal: Signal, strategy_manager: StrategyPositionManager):
        """Ejecutar señal de compra"""
        # Validaciones básicas del position_manager original
        current_positions = self.position_manager.count_open_positions()
        if current_positions >= self.position_manager.max_positions:
            raise ValueError(f"Maximum positions limit reached ({self.position_manager.max_positions})")

        # Verificar efectivo disponible
        account = self.alpaca.get_account()
        available_cash = float(account.cash)

        if self.is_crypto(signal.symbol):
            quote = self.alpaca.get_latest_crypto_quote(signal.symbol)
        else:
            quote = self.alpaca.get_latest_quote(signal.symbol)

        estimated_cost = float(quote.price) * signal.quantity
        if estimated_cost > available_cash:
            raise ValueError(f"Insufficient cash. Need: ${estimated_cost:.2f}, Available: ${available_cash:.2f}")

        # Ejecutar compra en Alpaca
        if self.is_crypto(signal.symbol):
            order = self.alpaca.submit_crypto_order(
                symbol=signal.symbol,
                qty=signal.quantity,
                side=signal.action
            )
        else:
            order = self.alpaca.submit_order(
                symbol=signal.symbol,
                qty=signal.quantity,
                side=signal.action
            )

        # Actualizar tracking de estrategia
        strategy_manager.add_position(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            quantity=signal.quantity,
            price=float(quote.price)
        )

        logger.info(f"Buy order executed: {signal.strategy_id} bought {signal.quantity} {signal.symbol}")
        return order

    def _execute_sell_signal(self, signal: Signal, strategy_manager: StrategyPositionManager):
        """Ejecutar señal de venta - solo vender lo que esta estrategia tiene"""
        # Obtener posición de esta estrategia específica
        strategy_position = strategy_manager.get_strategy_position(signal.strategy_id, signal.symbol)

        if strategy_position.quantity <= 0:
            raise ValueError(f"Strategy {signal.strategy_id} has no position in {signal.symbol} to sell")

        # Determinar cuánto vender (lo que pidió o lo que tiene, lo que sea menor)
        quantity_to_sell = min(signal.quantity, strategy_position.quantity)

        # Actualizar la cantidad en la señal
        signal.quantity = quantity_to_sell

        # Ejecutar venta en Alpaca
        if self.is_crypto(signal.symbol):
            order = self.alpaca.submit_crypto_order(
                symbol=signal.symbol,
                qty=quantity_to_sell,
                side=signal.action
            )
        else:
            order = self.alpaca.submit_order(
                symbol=signal.symbol,
                qty=quantity_to_sell,
                side=signal.action
            )

        # Actualizar tracking de estrategia
        actual_sold = strategy_manager.reduce_position(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            quantity=quantity_to_sell
        )

        logger.info(f"Sell order executed: {signal.strategy_id} sold {actual_sold} {signal.symbol}")
        return order


# Instancia global
order_executor = OrderExecutor()