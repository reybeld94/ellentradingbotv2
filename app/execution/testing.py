# backend/app/execution/testing.py

from sqlalchemy.orm import Session
from app.models.signal import Signal
from app.models.user import User
from app.models.order import Order
from app.core.types import SignalAction, OrderStatus
from app.execution.order_manager import OrderManager
from app.execution.order_processor import OrderProcessor
from app.schemas.webhook import TradingViewWebhook
from app.signals.processor import WebhookProcessor
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionTester:
    """Utilidad para testing del execution engine"""

    def __init__(self, db: Session):
        self.db = db
        self.webhook_processor = WebhookProcessor(db)
        self.order_manager = OrderManager(db)
        self.order_processor = OrderProcessor(db)

    def create_test_signal(
        self,
        user: User,
        symbol: str = "AAPL",
        action: str = "buy",
        strategy_id: str = "test_strategy",
        quantity: float = 1.0,
    ) -> Dict[str, Any]:
        """Crear una señal de prueba completa que pase por todo el pipeline"""

        try:
            # Crear webhook de test
            test_webhook = TradingViewWebhook(
                symbol=symbol,
                action=action,
                strategy_id=strategy_id,
                quantity=quantity,
                confidence=85,
                reason="test_signal",
            )

            # Procesar através del pipeline completo
            result = self.webhook_processor.process_tradingview_webhook(test_webhook, user)

            return {
                "success": True,
                "webhook_result": result,
                "test_data": {
                    "symbol": symbol,
                    "action": action,
                    "strategy_id": strategy_id,
                    "quantity": quantity,
                    "user": user.username,
                },
            }

        except Exception as e:
            logger.error(f"Error creating test signal: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_data": {
                    "symbol": symbol,
                    "action": action,
                    "strategy_id": strategy_id,
                    "quantity": quantity,
                    "user": user.username,
                },
            }

    def test_full_pipeline(self, user: User) -> Dict[str, Any]:
        """Test completo del pipeline: señal -> orden -> procesamiento"""

        results = {
            "steps": [],
            "overall_success": False,
            "errors": [],
        }

        try:
            # Paso 1: Crear señal de test
            logger.info("Step 1: Creating test signal...")
            signal_result = self.create_test_signal(user)

            step1 = {
                "step": "create_signal",
                "success": signal_result["success"],
                "data": signal_result.get("webhook_result", {}),
                "error": signal_result.get("error"),
            }
            results["steps"].append(step1)

            if not signal_result["success"]:
                results["errors"].append(f"Step 1 failed: {signal_result.get('error')}")
                return results

            signal_id = signal_result["webhook_result"].get("signal_id")
            if not signal_id:
                results["errors"].append("No signal_id returned from webhook processing")
                return results

            # Paso 2: Verificar que se creó la orden
            logger.info("Step 2: Checking order creation...")
            signal_db = self.db.query(Signal).filter(Signal.id == signal_id).first()

            if not signal_db:
                results["errors"].append("Signal not found in database")
                return results

            # Buscar órdenes asociadas a esta señal
            orders = self.db.query(Order).filter(Order.signal_id == signal_id).all()

            step2 = {
                "step": "check_order_creation",
                "success": len(orders) > 0,
                "data": {
                    "signal_status": signal_db.status,
                    "orders_created": len(orders),
                    "order_ids": [order.id for order in orders],
                },
            }
            results["steps"].append(step2)

            if len(orders) == 0:
                results["errors"].append("No orders created from signal")
                return results

            test_order = orders[0]

            # Paso 3: Procesar la orden (sin enviar al broker real)
            logger.info("Step 3: Processing order (test mode)...")

            # Simular procesamiento sin enviar al broker
            process_result = self._simulate_order_processing(test_order)

            step3 = {
                "step": "process_order",
                "success": process_result["success"],
                "data": process_result,
            }
            results["steps"].append(step3)

            # Paso 4: Verificar estado final
            logger.info("Step 4: Verifying final state...")
            self.db.refresh(test_order)

            step4 = {
                "step": "verify_final_state",
                "success": True,
                "data": {
                    "order_status": test_order.status,
                    "signal_status": signal_db.status,
                    "order_id": test_order.id,
                    "client_order_id": test_order.client_order_id,
                },
            }
            results["steps"].append(step4)

            # Determinar éxito general
            results["overall_success"] = all(step["success"] for step in results["steps"])

            return results

        except Exception as e:
            logger.error(f"Error in full pipeline test: {e}")
            results["errors"].append(f"Unexpected error: {str(e)}")
            return results

    def _simulate_order_processing(self, order) -> Dict[str, Any]:
        """Simular procesamiento de orden sin enviar al broker real"""

        try:
            # Simular que la orden fue enviada exitosamente
            order.status = OrderStatus.ACCEPTED
            order.broker_order_id = f"SIMULATED_{order.client_order_id}"
            order.sent_at = datetime.utcnow()

            # Simular fill parcial o completo
            import random

            if random.choice([True, False]):
                # Simular fill completo
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.avg_fill_price = 150.0 + random.uniform(-5, 5)  # Precio simulado
                order.filled_at = datetime.utcnow()
            else:
                # Simular fill parcial
                order.status = OrderStatus.PARTIALLY_FILLED
                order.filled_quantity = order.quantity * 0.5
                order.avg_fill_price = 150.0 + random.uniform(-5, 5)

            self.db.commit()

            return {
                "success": True,
                "simulated": True,
                "final_status": order.status,
                "filled_quantity": float(order.filled_quantity),
                "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
            }

        except Exception as e:
            return {
                "success": False,
                "simulated": True,
                "error": str(e),
            }

    def get_test_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de órdenes de test"""

        try:
            from sqlalchemy import func

            # Contar órdenes por estrategia de test
            test_orders = (
                self.db.query(Order)
                .join(Signal)
                .filter(Signal.strategy_id.like("test_%"))
                .all()
            )

            # Agrupar por estado
            status_counts = {}
            for order in test_orders:
                status = order.status
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "test_statistics": {
                    "total_test_orders": len(test_orders),
                    "status_breakdown": status_counts,
                    "test_order_ids": [order.id for order in test_orders[-5:]],
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting test statistics: {e}")
            return {
                "test_statistics": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
            }

    def cleanup_test_data(self, user: User) -> Dict[str, Any]:
        """Limpiar datos de test creados"""

        try:
            # Buscar señales de test
            test_signals = (
                self.db.query(Signal)
                .filter(
                    Signal.user_id == user.id,
                    Signal.strategy_id.like("test_%"),
                )
                .all()
            )

            # Buscar órdenes asociadas
            test_signal_ids = [s.id for s in test_signals]
            test_orders = (
                self.db.query(Order)
                .filter(Order.signal_id.in_(test_signal_ids))
                .all()
            ) if test_signal_ids else []

            # Eliminar órdenes primero (foreign key)
            orders_deleted = len(test_orders)
            for order in test_orders:
                self.db.delete(order)

            # Eliminar señales
            signals_deleted = len(test_signals)
            for signal in test_signals:
                self.db.delete(signal)

            self.db.commit()

            return {
                "success": True,
                "cleanup_summary": {
                    "signals_deleted": signals_deleted,
                    "orders_deleted": orders_deleted,
                },
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up test data: {e}")
            return {
                "success": False,
                "error": str(e),
            }
