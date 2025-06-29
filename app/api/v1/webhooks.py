# backend/app/api/v1/webhooks.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ...schemas.webhook import TradingViewWebhook, WebhookResponse
from ...models.signal import Signal
from ...services.order_executor import order_executor
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook", response_model=WebhookResponse)
async def receive_tradingview_webhook(
        webhook_data: TradingViewWebhook,
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Received webhook: {webhook_data.dict()}")

        # Crear nueva señal en la base de datos con campos extendidos
        signal = Signal(
            symbol=webhook_data.symbol,
            action=webhook_data.action,
            strategy_id=webhook_data.strategy_id,  # NUEVO
            quantity=webhook_data.quantity,
            price=webhook_data.price,
            source="tradingview",
            status="pending",
            reason=webhook_data.reason,
            confidence=webhook_data.confidence,
            tv_timestamp=webhook_data.timestamp
        )

        db.add(signal)
        db.commit()
        db.refresh(signal)

        logger.info(
            f"Signal created: ID {signal.id}, {signal.strategy_id}:{signal.symbol} {signal.action}, confidence: {signal.confidence}, reason: {signal.reason}")

        # Ejecutar orden en Alpaca con gestión por estrategia
        try:
            order = order_executor.execute_signal(signal)
            db.commit()  # Guardar cambios de status

            return WebhookResponse(
                status="success",
                message=f"Order executed: {signal.strategy_id} {signal.action} {signal.quantity} {signal.symbol} (confidence: {signal.confidence}%, reason: {signal.reason})",
                signal_id=signal.id
            )

        except Exception as e:
            db.commit()  # Guardar error en signal
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
async def get_signals(db: Session = Depends(get_db)):
    """Ver señales en nuestra base de datos con información extendida"""
    signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(10).all()
    return [
        {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "strategy_id": signal.strategy_id,  # NUEVO
            "quantity": signal.quantity,
            "status": signal.status,
            "error_message": signal.error_message,
            "timestamp": signal.timestamp,
            "reason": signal.reason,
            "confidence": signal.confidence,
            "tv_timestamp": signal.tv_timestamp
        }
        for signal in signals
    ]