from sqlalchemy.orm import Session
from app.schemas.webhook import TradingViewWebhook
from app.signals.normalizer import SignalNormalizer
from app.signals.router import SignalRouter
from app.models.user import User
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """Procesador principal de webhooks - orquesta todo el flujo"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.normalizer = SignalNormalizer()
        self.router = SignalRouter(db_session)
    
    def process_tradingview_webhook(
        self, 
        webhook_data: TradingViewWebhook, 
        user: User
    ) -> Dict[str, Any]:
        """
        Procesar webhook de TradingView siguiendo el nuevo flujo:
        Webhook -> Normalizar -> Validar -> Guardar -> Queue para Risk Management
        """
        
        try:
            # 1. Normalizar la señal
            normalized_signal = self.normalizer.from_tradingview(webhook_data)
            logger.info(f"Signal normalized: {normalized_signal.symbol} {normalized_signal.action}")
            
            # 2. Verificar duplicados
            if self.normalizer.is_duplicate(normalized_signal.idempotency_key, self.db):
                logger.warning(f"Duplicate signal detected: {normalized_signal.idempotency_key}")
                return {
                    "status": "duplicate",
                    "message": "Signal already processed",
                    "signal_id": None
                }
            
            # 3. Validar y enrutar
            result = self.router.process_signal(normalized_signal, user)
            
            if result["status"] == "accepted":
                logger.info(f"Signal accepted for processing: {result['signal_id']}")
            else:
                logger.warning(f"Signal rejected: {result.get('reason', 'unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {
                "status": "error",
                "message": f"Processing error: {str(e)}",
                "signal_id": None
            }
