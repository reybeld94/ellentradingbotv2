from sqlalchemy.orm import Session
from app.models.order import Order
from app.core.types import OrderStatus
from app.integrations.alpaca.client import AlpacaClient
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BrokerExecutor:
    """Ejecuta órdenes en el broker con retry y manejo de errores"""

    def __init__(self, db: Session):
        self.db = db
        self.broker = AlpacaClient()
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # segundos entre intentos

    def execute_order(self, order: Order) -> Dict[str, Any]:
        """Ejecutar una orden en el broker con retry automático"""

        try:
            # Actualizar estado a "enviando"
            order.status = OrderStatus.SENT
            order.retry_count += 1
            self.db.flush()

            logger.info(
                f"Executing order {order.client_order_id}: {order.side} {order.quantity} {order.symbol}"
            )

            # Determinar si es crypto o stock
            if self._is_crypto_symbol(order.symbol):
                broker_order = self._execute_crypto_order(order)
            else:
                broker_order = self._execute_stock_order(order)

            # Actualizar orden con respuesta del broker
            if broker_order:
                order.broker_order_id = str(broker_order.id)
                order.status = OrderStatus.ACCEPTED
                order.last_error = None
                self.db.flush()

                logger.info(
                    f"Order {order.client_order_id} accepted by broker: {broker_order.id}"
                )

                return {
                    "success": True,
                    "broker_order_id": broker_order.id,
                    "status": "accepted",
                }
            else:
                raise Exception("Broker returned None for order")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Order {order.client_order_id} failed: {error_msg}")

            # Decidir si reintentar o marcar como error
            if order.retry_count < self.max_retries:
                # Programar retry
                order.status = OrderStatus.NEW  # Volver a NEW para retry
                order.last_error = f"Retry {order.retry_count}: {error_msg}"
                self.db.flush()

                # Delay antes del retry
                delay = self.retry_delays[
                    min(order.retry_count - 1, len(self.retry_delays) - 1)
                ]
                logger.info(
                    f"Will retry order {order.client_order_id} in {delay} seconds"
                )

                return {
                    "success": False,
                    "retry_scheduled": True,
                    "retry_in_seconds": delay,
                    "error": error_msg,
                }
            else:
                # Max retries alcanzado
                order.status = OrderStatus.ERROR
                order.last_error = f"Max retries exceeded: {error_msg}"
                self.db.flush()

                return {
                    "success": False,
                    "retry_scheduled": False,
                    "error": f"Max retries exceeded: {error_msg}",
                }

    def _execute_stock_order(self, order: Order) -> Any:
        """Ejecutar orden de acciones"""
        return self.broker.submit_order(
            symbol=order.symbol,
            qty=float(order.quantity),
            side=order.side,
            order_type=order.order_type or "market",
            price=float(order.limit_price) if order.limit_price else None,
        )

    def _execute_crypto_order(self, order: Order) -> Any:
        """Ejecutar orden de crypto"""
        return self.broker.submit_crypto_order(
            symbol=order.symbol,
            qty=float(order.quantity),
            side=order.side,
            order_type=order.order_type or "market",
        )

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Determinar si el símbolo es crypto"""
        return self.broker.is_crypto_symbol(symbol)

    def get_order_status(self, order: Order) -> Optional[Dict[str, Any]]:
        """Consultar estado actual de una orden en el broker"""
        if not order.broker_order_id:
            return None

        try:
            # Obtener orden del broker
            broker_order = self.broker.get_order(order.broker_order_id)

            if broker_order:
                return {
                    "broker_order_id": order.broker_order_id,
                    "status": str(getattr(broker_order, "status", "unknown")),
                    "filled_qty": float(getattr(broker_order, "filled_qty", 0) or 0),
                    "filled_avg_price": float(
                        getattr(broker_order, "filled_avg_price", 0) or 0
                    ),
                }

        except Exception as e:
            logger.error(
                f"Error getting order status for {order.broker_order_id}: {e}"
            )

        return None

    def cancel_order(self, order: Order) -> bool:
        """Cancelar una orden en el broker"""
        if not order.broker_order_id:
            return False

        try:
            self.broker.cancel_order(order.broker_order_id)
            order.status = OrderStatus.CANCELED
            self.db.commit()

            logger.info(f"Order {order.client_order_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Error cancelling order {order.client_order_id}: {e}")
            return False
