# backend/app/api/v1/testing.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user, get_admin_user
from app.execution.testing import ExecutionTester
from typing import Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test-signal")
async def create_test_signal(
    symbol: str = "AAPL",
    action: str = "buy",
    strategy_id: str = "test_strategy",
    quantity: float = 1.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Crear una señal de test que pase por todo el pipeline"""
    try:
        tester = ExecutionTester(db)
        result = tester.create_test_signal(
            user=current_user,
            symbol=symbol,
            action=action,
            strategy_id=strategy_id,
            quantity=quantity,
        )

        if result["success"]:
            return {
                "status": "success",
                "message": f"Test signal created: {strategy_id} {action} {symbol}",
                "result": result,
                "user": current_user.username,
            }
        else:
            return {
                "status": "failed",
                "message": "Test signal creation failed",
                "result": result,
                "user": current_user.username,
            }

    except Exception as e:
        logger.error(f"Error creating test signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-full-pipeline")
async def test_full_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Test completo del pipeline: señal -> orden -> procesamiento"""
    try:
        tester = ExecutionTester(db)
        result = tester.test_full_pipeline(current_user)

        return {
            "status": "completed",
            "message": "Full pipeline test completed",
            "overall_success": result["overall_success"],
            "test_results": result,
            "user": current_user.username,
        }

    except Exception as e:
        logger.error(f"Error in full pipeline test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-statistics")
async def get_test_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Obtener estadísticas de órdenes de test"""
    try:
        tester = ExecutionTester(db)
        stats = tester.get_test_statistics()

        return {
            "statistics": stats,
            "generated_by": current_user.username,
        }

    except Exception as e:
        logger.error(f"Error getting test statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup-test-data")
async def cleanup_test_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Limpiar datos de test del usuario actual"""
    try:
        tester = ExecutionTester(db)
        result = tester.cleanup_test_data(current_user)

        if result["success"]:
            return {
                "status": "success",
                "message": "Test data cleaned up successfully",
                "cleanup_summary": result["cleanup_summary"],
                "user": current_user.username,
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to cleanup test data",
                "error": result["error"],
                "user": current_user.username,
            }

    except Exception as e:
        logger.error(f"Error cleaning up test data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-full-bracket-flow")
async def test_full_bracket_flow(
    test_request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Test completo del flujo bracket orders sin ejecutar en broker real"""
    try:
        # 1. Crear reglas de salida temporales si no existen
        from app.services.exit_rules_service import ExitRulesService
        exit_service = ExitRulesService(db)
        strategy_id = test_request.get("strategy_id", "test_strategy")
        rules = exit_service.get_rules(strategy_id)

        # 2. Calcular precios de salida
        entry_price = Decimal(str(test_request.get("entry_price", 100.0)))
        exit_calculation = exit_service.calculate_exit_prices(strategy_id, entry_price, "buy")

        # 3. Simular creación de señal
        from app.models.signal import Signal
        test_signal = Signal(
            symbol=test_request.get("symbol", "AAPL"),
            action="buy",
            strategy_id=strategy_id,
            quantity=10,
            status="validated",
            user_id=current_user.id,
            portfolio_id=1
        )

        # 4. Simular bracket order creation (sin guardar en DB)
        bracket_preview = {
            "entry_order": {
                "symbol": test_signal.symbol,
                "side": "buy",
                "quantity": test_signal.quantity,
                "order_type": "market"
            },
            "stop_loss_order": {
                "symbol": test_signal.symbol,
                "side": "sell",
                "quantity": test_signal.quantity,
                "order_type": "stop",
                "stop_price": exit_calculation["stop_loss_price"]
            },
            "take_profit_order": {
                "symbol": test_signal.symbol,
                "side": "sell",
                "quantity": test_signal.quantity,
                "order_type": "limit",
                "limit_price": exit_calculation["take_profit_price"]
            }
        }

        return {
            "status": "success",
            "test_scenario": test_request,
            "exit_rules": {
                "stop_loss_pct": rules.stop_loss_pct,
                "take_profit_pct": rules.take_profit_pct,
                "trailing_enabled": rules.use_trailing
            },
            "calculated_prices": exit_calculation,
            "bracket_orders_preview": bracket_preview,
            "orders_that_would_be_created": 3,
            "message": "Bracket order flow tested successfully (simulation only)"
        }

    except Exception as e:
        logger.error(f"Error in bracket flow test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get("/execution-flow")
async def get_execution_flow_info(
    current_user: User = Depends(get_current_verified_user),
):
    """Obtener información sobre el flujo de ejecución"""
    return {
        "execution_flow": {
            "steps": [
                {
                    "step": 1,
                    "name": "Signal Reception",
                    "description": "TradingView webhook received and normalized",
                    "component": "WebhookProcessor -> SignalNormalizer",
                },
                {
                    "step": 2,
                    "name": "Signal Validation",
                    "description": "Signal validated for format and content",
                    "component": "SignalValidator",
                },
                {
                    "step": 3,
                    "name": "Risk Management",
                    "description": "Signal evaluated against risk limits",
                    "component": "RiskManager",
                },
                {
                    "step": 4,
                    "name": "Order Creation",
                    "description": "Order created from approved signal",
                    "component": "OrderManager",
                },
                {
                    "step": 5,
                    "name": "Order Processing",
                    "description": "Order sent to broker with retry logic",
                    "component": "BrokerExecutor",
                },
                {
                    "step": 6,
                    "name": "Fill Tracking",
                    "description": "Order status and fills updated from broker",
                    "component": "OrderProcessor",
                },
            ]
        },
        "status_transitions": {
            "signal": [
                "pending",
                "validated",
                "processing",
                "executed",
                "rejected",
                "error",
            ],
            "order": [
                "new",
                "sent",
                "accepted",
                "partially_filled",
                "filled",
                "canceled",
                "rejected",
                "error",
            ],
        },
        "user": current_user.username,
    }
