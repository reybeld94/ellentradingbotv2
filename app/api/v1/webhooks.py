# backend/app/api/v1/webhooks.py

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas.webhook import TradingViewWebhook, WebhookResponse
from app.models.signal import Signal
from app.models.user import User
from app.services.order_executor import order_executor
from app.core.auth import get_current_verified_user
from app.config import settings
from app.websockets import ws_manager
from app.services import portfolio_service
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook", response_model=WebhookResponse)
async def receive_tradingview_webhook(
        webhook_data: TradingViewWebhook,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_verified_user)  # PROTEGIDO
):
    """Recibir webhook de TradingView (requiere autenticación)"""
    try:
        logger.info(
            f"Received webhook from user {current_user.username}: {webhook_data.dict()}"
        )

        # Verify that the strategy exists before creating the signal
        strategy_exists = db.execute(
            text("SELECT 1 FROM strategies WHERE id = :sid"),
            {"sid": webhook_data.strategy_id},
        ).first()
        if not strategy_exists:
            logger.warning(
                f"Unknown strategy received: {webhook_data.strategy_id}"
            )
            raise HTTPException(status_code=400, detail="Unknown strategy_id")

        active_portfolio = portfolio_service.get_active(db, current_user)
        if not active_portfolio:
            raise HTTPException(status_code=400, detail="No active portfolio configured")

        # Crear nueva señal en la base de datos con información del usuario
        signal = Signal(
            symbol=webhook_data.symbol,
            action=webhook_data.action,
            strategy_id=webhook_data.strategy_id,
            quantity=webhook_data.quantity,
            price=webhook_data.price,
            source="tradingview",
            status="pending",
            reason=webhook_data.reason,
            confidence=webhook_data.confidence,
            tv_timestamp=webhook_data.timestamp,
            user_id=current_user.id,  # NUEVO: Asociar señal con usuario
            portfolio_id=active_portfolio.id
        )

        db.add(signal)
        db.commit()
        db.refresh(signal)

        signal_data = {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "quantity": signal.quantity,
            "status": signal.status,
            "strategy_id": signal.strategy_id,
            "timestamp": signal.timestamp.isoformat(),
        }
        asyncio.create_task(
            ws_manager.broadcast(json.dumps({"event": "new_signal", "payload": signal_data}))
        )

        signal_data = {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "quantity": signal.quantity,
            "status": signal.status,
            "strategy_id": signal.strategy_id,
            "timestamp": signal.timestamp.isoformat(),
        }
        asyncio.create_task(
            ws_manager.broadcast(json.dumps({"event": "new_signal", "payload": signal_data}))
        )

        logger.info(
            f"Signal created: ID {signal.id}, User: {current_user.username}, {signal.strategy_id}:{signal.symbol} {signal.action}")

        # Ejecutar orden en Alpaca con gestión por estrategia
        try:
            order = order_executor.execute_signal(signal, current_user)
            db.commit()

            return WebhookResponse(
                status="success",
                message=f"Order executed: {signal.strategy_id} {signal.action} {signal.quantity} {signal.symbol} (user: {current_user.username})",
                signal_id=signal.id
            )

        except Exception as e:
            db.commit()
            logger.error(f"Error executing order: {e}")
            return WebhookResponse(
                status="error",
                message=f"Failed to execute order: {str(e)}",
                signal_id=signal.id
            )

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def get_signals(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_verified_user)  # PROTEGIDO
):
    """Ver señales del usuario actual"""

    # Filtrar señales por usuario
    if current_user.is_admin:
        # Admin puede ver todas las señales
        signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(50).all()
    else:
        # Usuario normal solo ve sus señales
        active_portfolio = portfolio_service.get_active(db, current_user)
        if not active_portfolio:
            return []
        signals = (
            db.query(Signal)
            .filter(
                Signal.user_id == current_user.id,
                Signal.portfolio_id == active_portfolio.id,
            )
            .order_by(Signal.timestamp.desc())
            .limit(50)
            .all()
        )

    return [
        {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "strategy_id": signal.strategy_id,
            "quantity": signal.quantity,
            "status": signal.status,
            "error_message": signal.error_message,
            "timestamp": signal.timestamp,
            "reason": signal.reason,
            "confidence": signal.confidence,
            "tv_timestamp": signal.tv_timestamp,
            "user_id": signal.user_id if current_user.is_admin else None  # Solo admin ve user_id
        }
        for signal in signals
    ]


# FIXED: Endpoint público para webhooks externos usando usuario 'reybel'
@router.post("/webhook-public", response_model=WebhookResponse)
async def receive_public_webhook(
        webhook_data: TradingViewWebhook,
        db: Session = Depends(get_db),
        # Opción 1: API key como query parameter
        api_key: Optional[str] = Query(None, description="API key for authentication"),
        # Opción 2: API key como header (alternativa)
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Webhook público con API key para TradingView - usa usuario 'reybel'"""

    # Verificar API key desde query param o header
    provided_api_key = api_key or x_api_key

    if not provided_api_key:
        logger.warning("Public webhook called without API key")
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide it as 'api_key' query parameter or 'X-API-Key' header"
        )

    # Verificar que la API key sea válida
    expected_api_key = getattr(settings, 'webhook_api_key', None)
    if not expected_api_key:
        logger.error("Webhook API key not configured in settings")
        raise HTTPException(status_code=500, detail="Webhook API key not configured")

    if provided_api_key != expected_api_key:
        logger.warning(f"Invalid API key provided: {provided_api_key}")
        raise HTTPException(status_code=401, detail="Invalid API key")

    # CAMBIADO: Buscar usuario 'reybel' en lugar de 'tradingview_bot'
    target_user = db.query(User).filter(User.username == "reybel").first()

    if not target_user:
        logger.error("User 'reybel' not found")
        raise HTTPException(
            status_code=500,
            detail="Target user 'reybel' not found. Please check that the user exists and is active."
        )

    if not target_user.is_active:
        logger.error("User 'reybel' is not active")
        raise HTTPException(
            status_code=500,
            detail="Target user 'reybel' is not active"
        )

    try:
        logger.info(f"Processing public webhook for user 'reybel': {webhook_data.dict()}")

        # Verify that the strategy exists before creating the signal
        strategy_exists = db.execute(
            text("SELECT 1 FROM strategies WHERE id = :sid"),
            {"sid": webhook_data.strategy_id},
        ).first()
        if not strategy_exists:
            logger.warning(
                f"Unknown strategy received: {webhook_data.strategy_id}"
            )
            return WebhookResponse(
                status="error",
                message="Unknown strategy_id",
                signal_id=None,
            )

        active_portfolio = portfolio_service.get_active(db, target_user)
        if not active_portfolio:
            return WebhookResponse(
                status="error",
                message="No active portfolio configured",
                signal_id=None,
            )

        signal = Signal(
            symbol=webhook_data.symbol,
            action=webhook_data.action,
            strategy_id=webhook_data.strategy_id,
            quantity=webhook_data.quantity,
            price=webhook_data.price,
            source="tradingview_public",
            status="pending",
            reason=webhook_data.reason,
            confidence=webhook_data.confidence,
            tv_timestamp=webhook_data.timestamp,
            user_id=target_user.id,  # Usar ID del usuario 'reybel'
            portfolio_id=active_portfolio.id
        )

        db.add(signal)
        db.commit()
        db.refresh(signal)

        logger.info(f"Public signal created for reybel: ID {signal.id}")

        # Ejecutar orden
        try:
            order = order_executor.execute_signal(signal, target_user)
            db.commit()

            logger.info(f"Order executed successfully for reybel: {signal.strategy_id} {signal.action} {signal.symbol}")

            return WebhookResponse(
                status="success",
                message=f"Public webhook processed for reybel: {signal.strategy_id} {signal.action} {signal.symbol}",
                signal_id=signal.id
            )
        except Exception as e:
            db.commit()
            logger.error(f"Error executing public webhook order for reybel: {e}")
            return WebhookResponse(
                status="error",
                message=f"Signal received but order failed: {str(e)}",
                signal_id=signal.id
            )

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing public webhook for reybel: {e}")
        return WebhookResponse(
            status="error",
            message=f"Failed to process webhook: {str(e)}",
            signal_id=None
        )


# Test endpoint for debugging
@router.post("/test-webhook")
async def test_webhook_endpoint(
        db: Session = Depends(get_db),
        api_key: Optional[str] = Query(None)
):
    """Test endpoint to verify webhook functionality"""

    # Simple test payload
    test_data = TradingViewWebhook(
        symbol="AAPL",
        action="buy",
        strategy_id="test_strategy",
        quantity=1,
        reason="test",
        confidence=100
    )

    # Use the public webhook function
    return await receive_public_webhook(test_data, db, api_key)


# Health check endpoint
@router.get("/webhook-health")
async def webhook_health(db: Session = Depends(get_db)):
    """Health check for webhook endpoints"""

    # Verificar si el usuario reybel existe
    reybel_user = db.query(User).filter(User.username == "reybel").first()
    reybel_status = "not_found"
    if reybel_user:
        if reybel_user.is_active:
            reybel_status = "active"
        else:
            reybel_status = "inactive"

    return {
        "status": "healthy",
        "webhook_api_key_configured": hasattr(settings, 'webhook_api_key') and settings.webhook_api_key is not None,
        "target_user": {
            "username": "reybel",
            "status": reybel_status,
            "found": reybel_user is not None,
            "active": reybel_user.is_active if reybel_user else False,
            "verified": reybel_user.is_verified if reybel_user else False
        },
        "endpoints": {
        "authenticated": "/api/v1/webhook",
        "public": "/api/v1/webhook-public",
        "test": "/api/v1/test-webhook"
    }
    }

