"""
Bracket Reconciliation Service - Mantiene sincronización automática de bracket orders
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.order import Order
from app.core.types import OrderStatus
from app.execution.order_executor import OrderExecutor
from app.execution.bracket_order_processor import BracketOrderProcessor

logger = logging.getLogger(__name__)


class BracketReconciliationService:
    """Servicio de reconciliación automática para bracket orders"""

    def __init__(self):
        self.db = None
        self.executor = None
        self.bracket_processor = None

    async def run_reconciliation_cycle(self) -> Dict[str, Any]:
        """Ejecutar un ciclo completo de reconciliación"""
        start_time = datetime.utcnow()
        results = {
            "start_time": start_time,
            "processed_brackets": 0,
            "fixed_inconsistencies": 0,
            "errors": [],
            "details": []
        }

        try:
            # Inicializar conexiones
            self.db = SessionLocal()
            self.executor = OrderExecutor()
            self.executor.db = self.db
            self.bracket_processor = BracketOrderProcessor(self.db)

            logger.info("Starting bracket orders reconciliation cycle")

            # 1. Reconciliar órdenes padre pendientes de activar hijas
            pending_activation = await self._reconcile_pending_activations()
            results["details"].append(pending_activation)

            # 2. Reconciliar órdenes hijas con estado inconsistente
            inconsistent_children = await self._reconcile_inconsistent_children()
            results["details"].append(inconsistent_children)

            # 3. Verificar OCO logic perdida
            broken_oco = await self._reconcile_broken_oco_logic()
            results["details"].append(broken_oco)

            # 4. Limpiar bracket orders huérfanas
            orphaned_cleanup = await self._cleanup_orphaned_brackets()
            results["details"].append(orphaned_cleanup)

            # Sumar totales
            results["processed_brackets"] = sum(detail.get("processed", 0) for detail in results["details"])
            results["fixed_inconsistencies"] = sum(detail.get("fixed", 0) for detail in results["details"])

            results["status"] = "success"
            results["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Reconciliation cycle completed: {results['processed_brackets']} processed, {results['fixed_inconsistencies']} fixed"
            )

        except Exception as e:
            logger.error(f"Error in reconciliation cycle: {str(e)}")
            results["status"] = "error"
            results["error_message"] = str(e)

        finally:
            if self.db:
                self.db.close()

        return results

    async def _reconcile_pending_activations(self) -> Dict[str, Any]:
        """Reconciliar órdenes padre que deberían haber activado sus hijas"""
        result = {"step": "pending_activations", "processed": 0, "fixed": 0, "errors": []}

        try:
            # Buscar órdenes padre filled con hijas aún pending_parent
            pending_brackets = self.db.query(Order).filter(
                and_(
                    Order.is_bracket_parent == True,
                    Order.status == OrderStatus.FILLED,
                    Order.updated_at < datetime.utcnow() - timedelta(minutes=5)
                )
            ).all()

            for parent_order in pending_brackets:
                try:
                    pending_children = self.db.query(Order).filter(
                        and_(
                            Order.parent_order_id == parent_order.id,
                            Order.status == OrderStatus.PENDING_PARENT
                        )
                    ).count()

                    if pending_children > 0:
                        logger.info(
                            f"Found parent order {parent_order.id} with {pending_children} pending children - attempting activation"
                        )

                        activation_result = await self.bracket_processor.activate_bracket_orders(parent_order.id)

                        if activation_result["status"] == "success":
                            result["fixed"] += 1
                            logger.info(f"Successfully activated bracket {parent_order.id}")
                        else:
                            result["errors"].append(
                                {
                                    "parent_order_id": parent_order.id,
                                    "error": activation_result.get("message", "Unknown error"),
                                }
                            )

                    result["processed"] += 1

                except Exception as e:
                    logger.error(f"Error processing parent order {parent_order.id}: {str(e)}")
                    result["errors"].append(
                        {
                            "parent_order_id": parent_order.id,
                            "error": str(e),
                        }
                    )

        except Exception as e:
            logger.error(f"Error in pending activations reconciliation: {str(e)}")
            result["errors"].append({"general_error": str(e)})

        return result

    async def _reconcile_inconsistent_children(self) -> Dict[str, Any]:
        """Reconciliar órdenes hijas con estado inconsistente vs broker"""
        result = {"step": "inconsistent_children", "processed": 0, "fixed": 0, "errors": []}

        try:
            child_orders = self.db.query(Order).filter(
                and_(
                    Order.parent_order_id.isnot(None),
                    Order.broker_order_id.isnot(None),
                    Order.status.in_([OrderStatus.SENT, OrderStatus.ACCEPTED]),
                    Order.updated_at < datetime.utcnow() - timedelta(minutes=10)
                )
            ).all()

            for child_order in child_orders:
                try:
                    broker_status = None
                    if hasattr(self.executor, "_get_order_status_from_broker"):
                        broker_status = await self.executor._get_order_status_from_broker(
                            child_order.broker_order_id
                        )

                    if broker_status and broker_status != child_order.status:
                        logger.info(
                            f"Found inconsistent child order {child_order.id}: DB={child_order.status}, Broker={broker_status}"
                        )

                        if broker_status == "filled":
                            child_order.status = OrderStatus.FILLED
                            await self.bracket_processor.handle_child_order_fill(child_order.id)
                            result["fixed"] += 1

                        elif broker_status == "canceled":
                            child_order.status = OrderStatus.CANCELED
                            result["fixed"] += 1

                        elif broker_status == "rejected":
                            child_order.status = OrderStatus.REJECTED
                            result["fixed"] += 1

                    result["processed"] += 1

                except Exception as e:
                    logger.error(
                        f"Error reconciling child order {child_order.id}: {str(e)}"
                    )
                    result["errors"].append(
                        {
                            "child_order_id": child_order.id,
                            "error": str(e),
                        }
                    )

            if result["fixed"] > 0:
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in children reconciliation: {str(e)}")
            result["errors"].append({"general_error": str(e)})

        return result

    async def _reconcile_broken_oco_logic(self) -> Dict[str, Any]:
        """Detectar y reparar lógica OCO rota"""
        result = {"step": "broken_oco", "processed": 0, "fixed": 0, "errors": []}

        try:
            problematic_parents = self.db.query(Order).filter(
                Order.is_bracket_parent == True
            ).all()

            for parent in problematic_parents:
                try:
                    active_children = self.db.query(Order).filter(
                        and_(
                            Order.parent_order_id == parent.id,
                            Order.status.in_(
                                [
                                    OrderStatus.SENT,
                                    OrderStatus.ACCEPTED,
                                    OrderStatus.FILLED,
                                ]
                            ),
                        )
                    ).all()

                    filled_children = [
                        child for child in active_children if child.status == OrderStatus.FILLED
                    ]
                    pending_children = [
                        child
                        for child in active_children
                        if child.status in [OrderStatus.SENT, OrderStatus.ACCEPTED]
                    ]

                    if len(filled_children) > 0 and len(pending_children) > 0:
                        logger.warning(
                            f"Found broken OCO logic for bracket {parent.id}: {len(filled_children)} filled, {len(pending_children)} still active"
                        )

                        for pending_child in pending_children:
                            if pending_child.broker_order_id:
                                cancel_result = await self.executor.cancel_order(
                                    pending_child.broker_order_id
                                )
                                if cancel_result["status"] == "success":
                                    pending_child.status = OrderStatus.CANCELED
                                    pending_child.notes = (
                                        "OCO repair - cancelled due to sibling fill"
                                    )
                                    result["fixed"] += 1

                    elif len(filled_children) > 1:
                        logger.error(
                            f"CRITICAL: Multiple child orders filled for bracket {parent.id}"
                        )
                        result["errors"].append(
                            {
                                "parent_order_id": parent.id,
                                "error": f"Multiple child orders filled: {[c.id for c in filled_children]}",
                            }
                        )

                    result["processed"] += 1

                except Exception as e:
                    logger.error(f"Error checking OCO for parent {parent.id}: {str(e)}")
                    result["errors"].append(
                        {
                            "parent_order_id": parent.id,
                            "error": str(e),
                        }
                    )

            if result["fixed"] > 0:
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in OCO reconciliation: {str(e)}")
            result["errors"].append({"general_error": str(e)})

        return result

    async def _cleanup_orphaned_brackets(self) -> Dict[str, Any]:
        """Limpiar bracket orders huérfanas o en estado inválido"""
        result = {"step": "orphaned_cleanup", "processed": 0, "fixed": 0, "errors": []}

        try:
            orphaned_children = self.db.query(Order).filter(
                and_(
                    Order.parent_order_id.isnot(None),
                    ~Order.parent_order_id.in_(
                        self.db.query(Order.id).filter(Order.is_bracket_parent == True)
                    ),
                )
            ).all()

            for orphaned in orphaned_children:
                logger.warning(
                    f"Found orphaned child order {orphaned.id} with missing parent {orphaned.parent_order_id}"
                )

                if (
                    orphaned.status in [OrderStatus.SENT, OrderStatus.ACCEPTED]
                    and orphaned.broker_order_id
                ):

                    cancel_result = await self.executor.cancel_order(
                        orphaned.broker_order_id
                    )
                    if cancel_result["status"] == "success":
                        orphaned.status = OrderStatus.CANCELED
                        orphaned.notes = "Cancelled - orphaned child order"
                        result["fixed"] += 1

                orphaned.parent_order_id = None
                result["processed"] += 1

            lonely_parents = self.db.query(Order).filter(
                and_(
                    Order.is_bracket_parent == True,
                    ~Order.id.in_(
                        self.db.query(Order.parent_order_id).filter(
                            Order.parent_order_id.isnot(None)
                        )
                    ),
                )
            ).all()

            for lonely in lonely_parents:
                logger.info(
                    f"Found parent order {lonely.id} with no children - removing bracket flag"
                )
                lonely.is_bracket_parent = False
                result["fixed"] += 1
                result["processed"] += 1

            if result["fixed"] > 0:
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in orphaned cleanup: {str(e)}")
            result["errors"].append({"general_error": str(e)})

        return result


async def run_bracket_reconciliation() -> None:
    """Función wrapper para ejecutar desde scheduler"""
    try:
        service = BracketReconciliationService()
        result = await service.run_reconciliation_cycle()

        if result["status"] == "success":
            logger.info(
                f"Bracket reconciliation completed successfully: {result['fixed_inconsistencies']} fixes applied"
            )
        else:
            logger.error(
                f"Bracket reconciliation failed: {result.get('error_message', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Critical error in bracket reconciliation: {str(e)}")

