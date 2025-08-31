"""
Bracket Order Processor - Maneja el ciclo de vida de bracket orders
"""
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.order import Order
from app.core.types import OrderStatus
from app.execution.order_executor import OrderExecutor

logger = logging.getLogger(__name__)


class BracketOrderProcessor:
    """Procesador especializado para bracket orders"""
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = OrderExecutor()
    
    async def activate_bracket_orders(self, parent_order_id: int) -> Dict[str, Any]:
        """
        Activar órdenes hijas cuando la orden padre se ejecuta completamente
        """
        try:
            # 1. Obtener orden padre
            parent_order = self.db.query(Order).filter(
                Order.id == parent_order_id,
                Order.is_bracket_parent == True
            ).first()
            
            if not parent_order:
                return {"status": "error", "message": "Parent order not found"}
            
            # 2. Verificar que la orden padre esté completamente ejecutada
            if parent_order.status != OrderStatus.FILLED:
                return {
                    "status": "waiting", 
                    "message": "Parent order not fully filled yet"
                }
            
            # 3. Obtener órdenes hijas pendientes
            child_orders = self.db.query(Order).filter(
                Order.parent_order_id == parent_order_id,
                Order.status == OrderStatus.PENDING_PARENT
            ).all()
            
            if not child_orders:
                return {
                    "status": "error", 
                    "message": "No pending child orders found"
                }
            
            # 4. Activar cada orden hija
            activated_orders = []
            failed_orders = []
            
            for child_order in child_orders:
                try:
                    # Enviar orden al broker
                    execution_result = await self.executor.execute_single_order(
                        symbol=child_order.symbol,
                        side=child_order.side,
                        quantity=child_order.quantity,
                        order_type=child_order.order_type,
                        limit_price=child_order.limit_price,
                        stop_price=child_order.stop_price,
                        client_order_id=child_order.client_order_id
                    )
                    
                    if execution_result["status"] == "success":
                        # Actualizar estado y broker order ID
                        child_order.status = OrderStatus.SENT
                        child_order.broker_order_id = execution_result.get("broker_order_id")
                        child_order.notes = f"Activated from parent {parent_order_id}"
                        activated_orders.append(child_order.id)
                        
                        logger.info(f"Activated child order {child_order.id} for parent {parent_order_id}")
                    else:
                        child_order.status = OrderStatus.REJECTED
                        child_order.notes = f"Failed to activate: {execution_result.get('message', 'Unknown error')}"
                        failed_orders.append(child_order.id)
                        
                        logger.error(f"Failed to activate child order {child_order.id}: {execution_result}")
                        
                except Exception as e:
                    child_order.status = OrderStatus.REJECTED
                    child_order.notes = f"Activation error: {str(e)}"
                    failed_orders.append(child_order.id)
                    logger.error(f"Error activating child order {child_order.id}: {str(e)}")
            
            # 5. Commit cambios
            self.db.commit()
            
            return {
                "status": "success" if activated_orders else "partial_failure",
                "activated_orders": activated_orders,
                "failed_orders": failed_orders,
                "message": f"Activated {len(activated_orders)} of {len(child_orders)} child orders"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error activating bracket orders for parent {parent_order_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def handle_child_order_fill(self, filled_order_id: int) -> Dict[str, Any]:
        """
        Manejar cuando una orden hija (SL o TP) se ejecuta - Lógica OCO
        """
        try:
            # 1. Obtener la orden que se ejecutó
            filled_order = self.db.query(Order).filter(Order.id == filled_order_id).first()
            
            if not filled_order or not filled_order.parent_order_id:
                return {"status": "error", "message": "Order is not a child order"}
            
            # 2. Obtener órdenes hermanas (sibling orders)
            sibling_orders = self.db.query(Order).filter(
                Order.parent_order_id == filled_order.parent_order_id,
                Order.id != filled_order_id,
                Order.status.in_([OrderStatus.SENT, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED])
            ).all()
            
            # 3. Cancelar órdenes hermanas (OCO Logic)
            cancelled_orders = []
            failed_cancellations = []
            
            for sibling in sibling_orders:
                try:
                    if sibling.broker_order_id:
                        # Cancelar en el broker
                        cancel_result = await self.executor.cancel_order(sibling.broker_order_id)
                        
                        if cancel_result["status"] == "success":
                            sibling.status = OrderStatus.CANCELED
                            sibling.notes = f"OCO cancelled - sibling {filled_order_id} filled"
                            cancelled_orders.append(sibling.id)
                            logger.info(f"OCO: Cancelled order {sibling.id} because {filled_order_id} filled")
                        else:
                            failed_cancellations.append(sibling.id)
                            logger.error(f"Failed to cancel sibling order {sibling.id}: {cancel_result}")
                    
                except Exception as e:
                    failed_cancellations.append(sibling.id)
                    logger.error(f"Error cancelling sibling order {sibling.id}: {str(e)}")
            
            # 4. Marcar bracket como completado
            parent_order = self.db.query(Order).filter(
                Order.id == filled_order.parent_order_id
            ).first()
            
            if parent_order:
                parent_order.notes = f"Bracket completed - {filled_order.order_type} executed"
            
            # 5. Commit cambios
            self.db.commit()
            
            return {
                "status": "success",
                "filled_order_id": filled_order_id,
                "cancelled_orders": cancelled_orders,
                "failed_cancellations": failed_cancellations,
                "message": f"OCO processed: cancelled {len(cancelled_orders)} sibling orders"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error handling child order fill {filled_order_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_bracket_status(self, parent_order_id: int) -> Dict[str, Any]:
        """
        Obtener estado completo de una bracket order
        """
        try:
            parent_order = self.db.query(Order).filter(
                Order.id == parent_order_id,
                Order.is_bracket_parent == True
            ).first()
            
            if not parent_order:
                return {"status": "error", "message": "Bracket order not found"}
            
            child_orders = self.db.query(Order).filter(
                Order.parent_order_id == parent_order_id
            ).all()
            
            return {
                "status": "success",
                "parent_order": {
                    "id": parent_order.id,
                    "status": parent_order.status,
                    "symbol": parent_order.symbol,
                    "quantity": parent_order.quantity,
                    "filled_qty": parent_order.filled_qty or 0
                },
                "child_orders": [
                    {
                        "id": child.id,
                        "type": child.order_type,
                        "status": child.status,
                        "price": child.limit_price or child.stop_price,
                        "broker_order_id": child.broker_order_id
                    }
                    for child in child_orders
                ],
                "bracket_active": any(
                    child.status in [OrderStatus.SENT, OrderStatus.ACCEPTED] 
                    for child in child_orders
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting bracket status {parent_order_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
