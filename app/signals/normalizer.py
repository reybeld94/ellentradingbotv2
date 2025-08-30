import hashlib
from datetime import datetime
from typing import Dict, Any
from app.core.types import NormalizedSignal, SignalAction
from app.schemas.webhook import TradingViewWebhook

class SignalNormalizer:
    """Normaliza señales de diferentes fuentes a formato común"""
    
    @staticmethod
    def from_tradingview(webhook_data: TradingViewWebhook) -> NormalizedSignal:
        """Normaliza webhook de TradingView"""
        
        # Mapear acciones
        action_mapping = {
            "buy": SignalAction.BUY,
            "sell": SignalAction.SELL,
            "long_entry": SignalAction.LONG_ENTRY,
            "long_exit": SignalAction.LONG_EXIT,
            "short_entry": SignalAction.SHORT_ENTRY,
            "short_exit": SignalAction.SHORT_EXIT,
        }
        
        action = action_mapping.get(
            webhook_data.action.lower(), 
            SignalAction.BUY
        )
        
        # Generar clave de idempotencia
        idempotency_parts = [
            webhook_data.symbol,
            webhook_data.action,
            webhook_data.strategy_id,
            str(int(datetime.now().timestamp() / 60))  # Redondear a minuto
        ]
        idempotency_key = hashlib.md5(
            "|".join(idempotency_parts).encode()
        ).hexdigest()
        
        return NormalizedSignal(
            symbol=webhook_data.symbol.upper(),
            action=action,
            strategy_id=webhook_data.strategy_id,
            quantity=webhook_data.quantity,
            confidence=webhook_data.confidence,
            reason=webhook_data.reason,
            stop_loss=getattr(webhook_data, 'stop_loss', None),
            take_profit=getattr(webhook_data, 'take_profit', None),
            source="tradingview",
            raw_payload=webhook_data.dict(),
            idempotency_key=idempotency_key,
            fired_at=datetime.now()
        )
    
    @staticmethod
    def is_duplicate(idempotency_key: str, db_session) -> bool:
        """Verificar si ya existe una señal con esta clave"""
        from app.models.signal import Signal
        existing = db_session.query(Signal).filter(
            Signal.idempotency_key == idempotency_key
        ).first()
        return existing is not None
