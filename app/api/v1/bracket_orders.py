"""
Bracket Orders API - Endpoints para monitoreo y control de bracket orders
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.database import get_db
from app.core.auth import get_current_verified_user
from app.models.user import User
from app.models.order import Order
from app.core.types import OrderStatus
from app.execution.order_executor import OrderExecutor
from app.execution.bracket_order_processor import BracketOrderProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/active")
async def get_active_bracket_orders(
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las bracket orders activas"""
    try:
        # Si no es admin, solo puede ver sus propias órdenes
        filter_user_id = current_user.id
        if current_user.is_admin and user_id:
            filter_user_id = user_id
        
        executor = OrderExecutor()
        executor.db = db
        
        bracket_orders = executor.get_active_bracket_orders(filter_user_id)
        
        return {
            "status": "success",
            "bracket_orders": bracket_orders,
            "total_count": len(bracket_orders),
            "user_id": filter_user_id
        }
        
    except Exception as e:
        logger.error(f"Error getting active bracket orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{parent_order_id}/status")
async def get_bracket_order_status(
    parent_order_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Obtener estado detallado de una bracket order específica"""
    try:
        # Verificar que el usuario tenga acceso a esta orden
        parent_order = db.query(Order).filter(
            Order.id == parent_order_id,
            Order.is_bracket_parent == True
        ).first()
        
        if not parent_order:
            raise HTTPException(status_code=404, detail="Bracket order not found")
        
        if not current_user.is_admin and parent_order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this bracket order")
        
        bracket_processor = BracketOrderProcessor(db)
        status = bracket_processor.get_bracket_status(parent_order_id)
        
        if status["status"] != "success":
            raise HTTPException(status_code=404, detail=status["message"])
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bracket status {parent_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{parent_order_id}/activate")
async def force_activate_bracket_orders(
    parent_order_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Forzar activación de órdenes hijas (para debugging)"""
    try:
        # Verificar acceso
        parent_order = db.query(Order).filter(
            Order.id == parent_order_id,
            Order.is_bracket_parent == True
        ).first()
        
        if not parent_order:
            raise HTTPException(status_code=404, detail="Bracket order not found")
        
        if not current_user.is_admin and parent_order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Forzar activación
        executor = OrderExecutor()
        executor.db = db
        
        result = await executor.force_bracket_reconciliation(parent_order_id)
        
        return {
            "status": "success",
            "parent_order_id": parent_order_id,
            "activation_result": result,
            "message": "Bracket activation forced"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing bracket activation {parent_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{parent_order_id}/cancel")
async def cancel_entire_bracket_order(
    parent_order_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Cancelar completamente una bracket order (parent + todas las child orders)"""
    try:
        # Verificar acceso
        parent_order = db.query(Order).filter(
            Order.id == parent_order_id,
            Order.is_bracket_parent == True
        ).first()
        
        if not parent_order:
            raise HTTPException(status_code=404, detail="Bracket order not found")
        
        if not current_user.is_admin and parent_order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Obtener todas las órdenes del bracket
        child_orders = db.query(Order).filter(
            Order.parent_order_id == parent_order_id,
            Order.status.in_([
                OrderStatus.SENT, 
                OrderStatus.ACCEPTED, 
                OrderStatus.PARTIALLY_FILLED,
                OrderStatus.PENDING_PARENT
            ])
        ).all()
        
        executor = OrderExecutor()
        executor.db = db
        
        cancelled_orders = []
        failed_cancellations = []
        
        # Cancelar orden parent si está activa
        if parent_order.status in [OrderStatus.SENT, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED]:
            if parent_order.broker_order_id:
                cancel_result = await executor.cancel_order(parent_order.broker_order_id)
                if cancel_result["status"] == "success":
                    parent_order.status = OrderStatus.CANCELED
                    cancelled_orders.append(parent_order.id)
                else:
                    failed_cancellations.append(parent_order.id)
        
        # Cancelar órdenes hijas
        for child in child_orders:
            try:
                if child.broker_order_id and child.status in [OrderStatus.SENT, OrderStatus.ACCEPTED]:
                    cancel_result = await executor.cancel_order(child.broker_order_id)
                    if cancel_result["status"] == "success":
                        child.status = OrderStatus.CANCELED
                        cancelled_orders.append(child.id)
                    else:
                        failed_cancellations.append(child.id)
                elif child.status == OrderStatus.PENDING_PARENT:
                    # Si está pendiente, simplemente marcarla como cancelada
                    child.status = OrderStatus.CANCELED
                    cancelled_orders.append(child.id)
                    
            except Exception as e:
                logger.error(f"Error cancelling child order {child.id}: {str(e)}")
                failed_cancellations.append(child.id)
        
        db.commit()
        
        return {
            "status": "success",
            "parent_order_id": parent_order_id,
            "cancelled_orders": cancelled_orders,
            "failed_cancellations": failed_cancellations,
            "message": f"Bracket cancellation completed: {len(cancelled_orders)} cancelled, {len(failed_cancellations)} failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling bracket order {parent_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_bracket_orders_statistics(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de bracket orders"""
    try:
        from datetime import datetime, timedelta
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query base
        query = db.query(Order).filter(
            Order.is_bracket_parent == True,
            Order.created_at >= since_date
        )
        
        # Filtrar por usuario si no es admin
        if not current_user.is_admin:
            query = query.filter(Order.user_id == current_user.id)
        
        parent_orders = query.all()
        
        # Calcular estadísticas
        total_brackets = len(parent_orders)
        completed_brackets = len([o for o in parent_orders if o.status == OrderStatus.FILLED])
        
        # Estadísticas de órdenes hijas
        all_child_ids = [o.id for o in parent_orders]
        child_orders = db.query(Order).filter(
            Order.parent_order_id.in_(all_child_ids)
        ).all() if all_child_ids else []
        
        executed_sl = len([o for o in child_orders if o.order_type == "stop" and o.status == OrderStatus.FILLED])
        executed_tp = len([o for o in child_orders if o.order_type == "limit" and o.status == OrderStatus.FILLED])
        
        return {
            "status": "success",
            "period_days": days,
            "statistics": {
                "total_bracket_orders": total_brackets,
                "completed_entry_orders": completed_brackets,
                "completion_rate": round(completed_brackets / total_brackets * 100, 2) if total_brackets > 0 else 0,
                "executed_stop_losses": executed_sl,
                "executed_take_profits": executed_tp,
                "sl_vs_tp_ratio": round(executed_sl / executed_tp, 2) if executed_tp > 0 else "N/A"
            },
            "user_scope": "all_users" if current_user.is_admin else "current_user"
        }
        
    except Exception as e:
        logger.error(f"Error getting bracket statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-flow")
async def test_bracket_order_flow(
    symbol: str = Query("AAPL", description="Symbol to test"),
    quantity: float = Query(1.0, description="Quantity to test"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Endpoint de testing para validar el flujo completo de bracket orders"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required for testing")
    
    try:
        executor = OrderExecutor()
        executor.db = db
        
        result = await executor.test_bracket_flow(symbol, quantity)
        
        return {
            "status": "success",
            "test_parameters": {
                "symbol": symbol,
                "quantity": quantity
            },
            "test_result": result,
            "message": "Bracket flow test completed (no real orders created)"
        }
        
    except Exception as e:
        logger.error(f"Error in bracket flow test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconcile")
async def manual_bracket_reconciliation(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Ejecutar reconciliación manual de bracket orders (solo admin)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.services.bracket_reconciliation_service import BracketReconciliationService

        service = BracketReconciliationService()
        result = await service.run_reconciliation_cycle()

        return {
            "status": "success",
            "reconciliation_result": result,
            "message": "Manual reconciliation completed"
        }

    except Exception as e:
        logger.error(f"Error in manual reconciliation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
