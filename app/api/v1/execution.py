# backend/app/api/v1/execution.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.core.auth import get_current_verified_user, get_admin_user
from app.execution.order_processor import OrderProcessor
from app.execution.order_manager import OrderManager
from app.execution.broker_executor import BrokerExecutor
from app.core.types import OrderStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/process-orders")
async def process_pending_orders(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo admins
):
    """Procesar todas las órdenes pendientes manualmente"""
    try:
        processor = OrderProcessor(db)
        
        # Ejecutar en background para no bloquear la respuesta
        def process_orders():
            result = processor.process_pending_orders()
            logger.info(f"Manual order processing completed: {result}")
        
        background_tasks.add_task(process_orders)
        
        return {
            "status": "processing_started",
            "message": "Order processing started in background",
            "initiated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error starting order processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-order/{order_id}")
async def process_single_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Procesar una orden específica"""
    try:
        processor = OrderProcessor(db)
        
        # Verificar que la orden pertenece al usuario (o es admin)
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not current_user.is_admin and order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to process this order")
        
        result = processor.process_single_order(order_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Order {order_id} processed successfully",
                "order_id": result["order_id"],
                "client_order_id": result["client_order_id"],
                "broker_order_id": result.get("broker_order_id")
            }
        else:
            return {
                "status": "failed",
                "message": f"Order {order_id} processing failed",
                "error": result.get("error")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing single order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-fills")
async def update_order_fills(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo admins
):
    """Actualizar información de fills desde el broker"""
    try:
        processor = OrderProcessor(db)
        
        def update_fills():
            result = processor.update_order_fills()
            logger.info(f"Fill update completed: {result}")
        
        background_tasks.add_task(update_fills)
        
        return {
            "status": "update_started",
            "message": "Fill update started in background",
            "initiated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error starting fill update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cancel-order/{order_id}")
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Cancelar una orden específica"""
    try:
        processor = OrderProcessor(db)
        
        # Verificar autorización
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not current_user.is_admin and order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this order")
        
        result = processor.cancel_order(order_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Order {order_id} cancelled successfully",
                "order_id": result["order_id"],
                "client_order_id": result["client_order_id"]
            }
        else:
            return {
                "status": "failed",
                "message": f"Failed to cancel order {order_id}",
                "error": result.get("error")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/my")
async def get_my_orders(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener órdenes del usuario actual"""
    try:
        query = db.query(Order).filter(Order.user_id == current_user.id)
        
        if status:
            if status.upper() not in [s.value for s in OrderStatus]:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            query = query.filter(Order.status == status.upper())
        
        orders = (
            query.order_by(Order.created_at.desc())
            .limit(min(limit, 100))  # Max 100
            .all()
        )
        
        return {
            "orders": [
                {
                    "id": order.id,
                    "client_order_id": order.client_order_id,
                    "broker_order_id": order.broker_order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": float(order.quantity),
                    "order_type": order.order_type,
                    "status": order.status,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "filled_quantity": float(order.filled_quantity),
                    "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
                    "created_at": order.created_at.isoformat(),
                    "sent_at": order.sent_at.isoformat() if order.sent_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "retry_count": order.retry_count,
                    "last_error": order.last_error,
                    "signal_id": order.signal_id
                }
                for order in orders
            ],
            "total_count": len(orders),
            "user": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener detalles de una orden específica"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verificar autorización
        if not current_user.is_admin and order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
        
        return {
            "id": order.id,
            "client_order_id": order.client_order_id,
            "broker_order_id": order.broker_order_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": float(order.quantity),
            "order_type": order.order_type,
            "status": order.status,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "filled_quantity": float(order.filled_quantity),
            "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
            "total_fees": float(order.total_fees),
            "created_at": order.created_at.isoformat(),
            "sent_at": order.sent_at.isoformat() if order.sent_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "retry_count": order.retry_count,
            "last_error": order.last_error,
            "time_in_force": order.time_in_force,
            "stop_loss_price": float(order.stop_loss_price) if order.stop_loss_price else None,
            "take_profit_price": float(order.take_profit_price) if order.take_profit_price else None,
            "signal_id": order.signal_id,
            "user_id": order.user_id,
            "portfolio_id": order.portfolio_id,
            "is_active": order.is_active,
            "fill_percentage": order.fill_percentage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order detail {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_execution_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo admins
):
    """Obtener estadísticas del execution engine"""
    try:
        processor = OrderProcessor(db)
        stats = processor.get_order_statistics()
        
        return {
            "execution_statistics": stats,
            "generated_at": stats["timestamp"],
            "generated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error getting execution statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def execution_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Health check del execution engine"""
    try:
        # Contar órdenes pendientes
        pending_count = db.query(Order).filter(Order.status == OrderStatus.NEW).count()
        
        # Contar órdenes con error
        error_count = db.query(Order).filter(Order.status == OrderStatus.ERROR).count()
        
        # Determinar status general
        status = "healthy"
        if pending_count > 10:
            status = "warning"  # Muchas órdenes pendientes
        if error_count > 5:
            status = "critical"  # Muchas órdenes con error
        
        first_order = db.query(Order).first()
        timestamp = first_order.created_at.isoformat() if first_order else None

        return {
            "status": status,
            "pending_orders": pending_count,
            "error_orders": error_count,
            "message": f"Execution engine is {status}",
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": None
        }
