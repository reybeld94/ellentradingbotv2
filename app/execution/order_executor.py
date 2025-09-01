import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.order import Order
from app.core.types import OrderStatus

# NOTE: BracketOrderProcessor is imported for type checking to avoid
# circular import issues at runtime.
if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from app.execution.bracket_order_processor import BracketOrderProcessor

logger = logging.getLogger(__name__)


class OrderExecutor:
    """Basic order execution and fill handling service."""

    def __init__(self, db: Optional[Session] = None) -> None:
        # Allow passing a custom session for testing; otherwise use default
        self.db: Session = db or SessionLocal()

    async def execute_single_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate order submission to broker.

        This simplified implementation just returns a fake broker order id.
        """

        broker_order_id = f"SIM-{uuid4().hex[:10]}"
        logger.info(
            "Simulated order submission: %s %s %s (%s)",
            side,
            quantity,
            symbol,
            broker_order_id,
        )
        return {"status": "success", "broker_order_id": broker_order_id}

    async def cancel_order(self, broker_order_id: str) -> Dict[str, Any]:
        """Simulate cancellation of an order at the broker."""
        logger.info("Simulated cancel of broker order %s", broker_order_id)
        return {"status": "success", "broker_order_id": broker_order_id}

    async def get_market_hours(self, symbol: str) -> Dict[str, Any]:
        """Check with the broker if the market for ``symbol`` is open.

        Returns a dictionary with ``is_open`` and ``status`` keys. If the broker
        cannot be reached or doesn't provide the information, the method falls
        back to a best-effort offline check and returns ``{"is_open": False,
        "status": "unknown"}``.
        """
        try:
            from app.integrations.alpaca.client import AlpacaClient, _in_regular_trading_hours

            client = AlpacaClient()

            # Crypto markets trade 24/7
            if client.is_crypto_symbol(symbol):
                return {"is_open": True, "status": "open"}

            trading = client.api
            if trading:
                clock = trading.get_clock()
                is_open = bool(getattr(clock, "is_open", False))
                status = "open" if is_open else "closed"
                return {"is_open": is_open, "status": status}

            # Fallback to local time check if broker client isn't available
            is_open = _in_regular_trading_hours()
            status = "open" if is_open else "closed"
            return {"is_open": is_open, "status": status}

        except Exception as e:  # pragma: no cover - best effort
            logger.warning("Market hours check failed for %s: %s", symbol, str(e))
            return {"is_open": False, "status": "unknown"}

    async def _get_order_status_from_broker(self, broker_order_id: str) -> Optional[str]:
        """Obtener el estado actual de una orden desde el broker.

        Esta implementación simplificada utiliza el BrokerExecutor para
        consultar el estado. En entornos de prueba donde no se pueda
        conectar con el broker, devuelve ``None``.
        """
        try:
            from app.execution.broker_executor import BrokerExecutor

            broker_exec = BrokerExecutor(self.db)
            order = self.db.query(Order).filter(
                Order.broker_order_id == broker_order_id
            ).first()
            if not order:
                order = Order(broker_order_id=broker_order_id)

            status_info = broker_exec.get_order_status(order)
            if status_info:
                return str(status_info.get("status"))
        except Exception as e:  # pragma: no cover - best effort logging
            logger.error(
                "Error getting broker status for %s: %s", broker_order_id, str(e)
            )
        return None

    async def _handle_order_fill(self, order: Order, fill_data: Dict[str, Any]) -> None:
        """Handle when an order gets filled - with bracket order support"""
        try:
            # Actualizar datos de fill existentes (mantener lógica actual)
            filled_qty = fill_data.get("filled_qty", float(order.quantity or 0))
            order.filled_qty = filled_qty  # backward compatibility
            order.filled_quantity = filled_qty
            order.avg_fill_price = fill_data.get("avg_price", 0.0)
            order.status = OrderStatus.FILLED
            order.updated_at = datetime.utcnow()

            # Log del fill
            logger.info(
                "Order %s filled: %s @ %s",
                order.id,
                order.filled_qty,
                order.avg_fill_price,
            )

            # NUEVO: Manejar bracket orders
            await self._process_bracket_order_fill(order)

            self.db.commit()

        except Exception as e:  # pragma: no cover - defensive logging
            logger.error("Error handling order fill %s: %s", order.id, str(e))
            self.db.rollback()
            raise

    async def _process_bracket_order_fill(self, filled_order: Order) -> None:
        """Procesar fills de bracket orders"""
        try:
            from app.execution.bracket_order_processor import BracketOrderProcessor

            bracket_processor = BracketOrderProcessor(self.db)

            # Caso 1: Orden padre completada -> Activar órdenes hijas
            if getattr(filled_order, "is_bracket_parent", False):
                logger.info(
                    "Bracket parent order %s filled - activating child orders",
                    filled_order.id,
                )

                activation_result = await bracket_processor.activate_bracket_orders(
                    filled_order.id
                )

                if activation_result["status"] == "success":
                    logger.info(
                        "Successfully activated bracket orders for parent %s",
                        filled_order.id,
                    )
                else:
                    logger.error(
                        "Failed to activate bracket orders: %s", activation_result
                    )

            # Caso 2: Orden hija completada -> Aplicar lógica OCO
            elif getattr(filled_order, "parent_order_id", None):
                logger.info(
                    "Bracket child order %s filled - applying OCO logic",
                    filled_order.id,
                )

                oco_result = await bracket_processor.handle_child_order_fill(
                    filled_order.id
                )

                if oco_result["status"] == "success":
                    cancelled_count = len(oco_result["cancelled_orders"])
                    logger.info(
                        "OCO processed: cancelled %s sibling orders", cancelled_count
                    )
                else:
                    logger.error(
                        "Failed to process OCO logic: %s", oco_result
                    )

        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                "Error processing bracket order fill for order %s: %s",
                filled_order.id,
                str(e),
            )
            # No re-raise aquí para no afectar el fill principal

    def get_active_bracket_orders(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtener todas las bracket orders activas"""
        try:
            from app.execution.bracket_order_processor import BracketOrderProcessor

            query = self.db.query(Order).filter(
                Order.is_bracket_parent == True,  # noqa: E712
                Order.status.in_(
                    [OrderStatus.FILLED, OrderStatus.SENT, OrderStatus.ACCEPTED]
                ),
            )

            if user_id:
                query = query.filter(Order.user_id == user_id)

            parent_orders = query.all()
            bracket_processor = BracketOrderProcessor(self.db)

            bracket_statuses: List[Dict[str, Any]] = []
            for parent in parent_orders:
                status = bracket_processor.get_bracket_status(parent.id)
                if status["status"] == "success":
                    bracket_statuses.append(status)

            return bracket_statuses

        except Exception as e:  # pragma: no cover - defensive logging
            logger.error("Error getting active bracket orders: %s", str(e))
            return []

    async def force_bracket_reconciliation(
        self, parent_order_id: int
    ) -> Dict[str, Any]:
        """Forzar reconciliación de una bracket order específica"""
        try:
            from app.execution.bracket_order_processor import BracketOrderProcessor

            bracket_processor = BracketOrderProcessor(self.db)

            # Obtener estado actual
            current_status = bracket_processor.get_bracket_status(parent_order_id)

            if current_status["status"] != "success":
                return current_status

            parent_order = (
                self.db.query(Order).filter(Order.id == parent_order_id).first()
            )

            # Si el parent está filled pero las child orders siguen pending_parent
            if parent_order and (
                parent_order.status == OrderStatus.FILLED
                and any(
                    child["status"] == OrderStatus.PENDING_PARENT.value
                    for child in current_status["child_orders"]
                )
            ):
                logger.info("Force reconciling bracket %s", parent_order_id)
                return await bracket_processor.activate_bracket_orders(parent_order_id)

            return {
                "status": "no_action_needed",
                "message": "Bracket order is in correct state",
                "current_status": current_status,
            }

        except Exception as e:  # pragma: no cover - defensive logging
            logger.error("Error in force bracket reconciliation: %s", str(e))
            return {"status": "error", "message": str(e)}

    async def test_bracket_flow(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Método de testing para validar flujo completo de bracket orders"""
        try:
            from app.execution.bracket_order_processor import BracketOrderProcessor

            logger.info("Testing bracket flow for %s x %s", symbol, quantity)

            # Simular orden parent completada
            test_parent = Order(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                order_type="market",
                status=OrderStatus.FILLED,
                is_bracket_parent=True,
                user_id=1,  # Test user
                portfolio_id=1,  # Test portfolio
            )

            self.db.add(test_parent)
            self.db.flush()  # Get ID without committing

            bracket_processor = BracketOrderProcessor(self.db)
            result = await bracket_processor.activate_bracket_orders(test_parent.id)

            # Cleanup test data
            self.db.rollback()

            return {"test_result": result, "message": "Bracket flow test completed"}

        except Exception as e:  # pragma: no cover - defensive logging
            self.db.rollback()
            return {"status": "error", "message": f"Test failed: {str(e)}"}
