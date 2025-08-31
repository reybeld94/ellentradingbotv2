from sqlalchemy.orm import Session
from app.models.order import Order
from app.core.types import OrderStatus
from app.execution.order_manager import OrderManager
from app.execution.broker_executor import BrokerExecutor
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OrderProcessor:
    """Servicio que procesa órdenes pendientes y maneja su ciclo de vida"""

    def __init__(self, db: Session):
        self.db = db
        self.order_manager = OrderManager(db)
        self.broker_executor = BrokerExecutor(db)

    def process_pending_orders(self) -> Dict[str, Any]:
        """Procesar todas las órdenes pendientes"""

        # Obtener órdenes NEW (listas para enviar)
        pending_orders = self._get_pending_orders()

        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "retries_scheduled": 0,
            "orders_processed": []
        }

        logger.info(f"Processing {len(pending_orders)} pending orders")

        for order in pending_orders:
            try:
                with self.db.begin():
                    locked_order = (
                        self.db.query(Order)
                        .filter(Order.id == order.id)
                        .with_for_update()
                        .one()
                    )
                    result = self.broker_executor.execute_order(locked_order)

                order_result = {
                    "order_id": locked_order.id,
                    "client_order_id": locked_order.client_order_id,
                    "symbol": locked_order.symbol,
                    "side": locked_order.side,
                    "success": result["success"]
                }

                if result["success"]:
                    results["successful"] += 1
                    order_result["broker_order_id"] = result.get("broker_order_id")
                    logger.info(f"Order {locked_order.client_order_id} executed successfully")

                elif result.get("retry_scheduled"):
                    results["retries_scheduled"] += 1
                    order_result["retry_scheduled"] = True
                    order_result["retry_in_seconds"] = result.get("retry_in_seconds")
                    logger.info(f"Order {locked_order.client_order_id} scheduled for retry")

                else:
                    results["failed"] += 1
                    order_result["error"] = result.get("error")
                    logger.error(f"Order {locked_order.client_order_id} failed permanently")

                results["orders_processed"].append(order_result)
                results["processed"] += 1

            except Exception as e:
                logger.error(f"Unexpected error processing order {order.id}: {e}")
                # Marcar orden como error
                order.status = OrderStatus.ERROR
                order.last_error = f"Processing error: {str(e)}"
                self.db.commit()
                results["failed"] += 1

        logger.info(
            f"Order processing complete: {results['successful']} successful, "
            f"{results['failed']} failed, {results['retries_scheduled']} retries"
        )
        return results

    def process_single_order(self, order_id: int) -> Dict[str, Any]:
        """Procesar una orden específica"""

        try:
            with self.db.begin():
                order = (
                    self.db.query(Order)
                    .filter(Order.id == order_id)
                    .with_for_update()
                    .first()
                )
                if not order:
                    return {"success": False, "error": "Order not found"}

                if order.status != OrderStatus.NEW:
                    return {
                        "success": False,
                        "error": f"Order status is {order.status}, expected NEW",
                    }

                result = self.broker_executor.execute_order(order)

            return {
                "success": result["success"],
                "order_id": order.id,
                "client_order_id": order.client_order_id,
                "broker_order_id": result.get("broker_order_id"),
                "error": result.get("error"),
            }
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {e}")
            return {"success": False, "error": str(e)}

    def update_order_fills(self) -> Dict[str, Any]:
        """Actualizar órdenes aceptadas con información de fills del broker"""

        # Obtener órdenes que están en el broker pero no completadas
        active_orders = self._get_active_orders()

        results = {
            "checked": 0,
            "updated": 0,
            "filled": 0,
            "errors": 0
        }

        for order in active_orders:
            try:
                # Consultar estado en el broker
                broker_status = self.broker_executor.get_order_status(order)

                if broker_status:
                    self._update_order_from_broker_status(order, broker_status)
                    results["updated"] += 1

                    if order.status == OrderStatus.FILLED:
                        results["filled"] += 1
                        logger.info(
                            f"Order {order.client_order_id} filled: "
                            f"{order.filled_quantity} @ {order.avg_fill_price}"
                        )

                results["checked"] += 1

            except Exception as e:
                logger.error(f"Error updating order {order.id}: {e}")
                results["errors"] += 1

        return results

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """Cancelar una orden específica"""

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        if not order.is_active:
            return {
                "success": False,
                "error": f"Order is not active (status: {order.status})",
            }

        success = self.broker_executor.cancel_order(order)
        return {
            "success": success,
            "order_id": order.id,
            "client_order_id": order.client_order_id,
        }

    def _get_pending_orders(self) -> List[Order]:
        """Obtener órdenes pendientes de procesamiento"""
        return (
            self.db.query(Order)
            .filter(Order.status == OrderStatus.NEW)
            .order_by(Order.created_at.asc())
            .limit(50)  # Procesar máximo 50 por batch
            .all()
        )

    def _get_active_orders(self) -> List[Order]:
        """Obtener órdenes activas en el broker"""
        active_statuses = [
            OrderStatus.SENT,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
        ]
        return (
            self.db.query(Order)
            .filter(
                Order.status.in_(active_statuses),
                Order.broker_order_id.isnot(None)
            )
            .all()
        )

    def _update_order_from_broker_status(
        self, order: Order, broker_status: Dict[str, Any]
    ) -> None:
        """Actualizar orden local con información del broker"""

        broker_order_status = broker_status.get("status", "").lower()
        filled_qty = broker_status.get("filled_qty", 0)
        avg_price = broker_status.get("filled_avg_price", 0)

        # Mapear estados del broker a nuestros estados
        status_mapping = {
            "new": OrderStatus.ACCEPTED,
            "accepted": OrderStatus.ACCEPTED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELED,
            "rejected": OrderStatus.REJECTED,
        }

        new_status = status_mapping.get(broker_order_status, order.status)

        # Actualizar campos si hay cambios
        updated = False

        if order.status != new_status:
            order.status = new_status
            updated = True

            if new_status == OrderStatus.FILLED:
                order.filled_at = datetime.utcnow()

        if filled_qty > 0 and order.filled_quantity != filled_qty:
            order.filled_quantity = filled_qty
            updated = True

        if avg_price > 0 and order.avg_fill_price != avg_price:
            order.avg_fill_price = avg_price
            updated = True

        if updated:
            order.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(
                f"Updated order {order.client_order_id}: "
                f"status={new_status}, filled={filled_qty}"
            )

    def get_order_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de órdenes"""

        from sqlalchemy import func, and_

        # Estadísticas por estado
        status_stats = (
            self.db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )

        # Órdenes de las últimas 24 horas
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_orders = (
            self.db.query(func.count(Order.id))
            .filter(Order.created_at >= yesterday)
            .scalar()
        )

        # Órdenes con errores
        error_orders = (
            self.db.query(func.count(Order.id))
            .filter(Order.status == OrderStatus.ERROR)
            .scalar()
        )

        return {
            "status_breakdown": {status: count for status, count in status_stats},
            "recent_orders_24h": recent_orders,
            "error_orders": error_orders,
            "timestamp": datetime.utcnow().isoformat(),
        }
