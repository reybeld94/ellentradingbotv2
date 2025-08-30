from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.types import NormalizedSignal
from app.signals.validator import SignalValidator, SignalValidationError
from app.models.signal import Signal
from app.models.user import User
from app.services import portfolio_service
import logging

logger = logging.getLogger(__name__)

class SignalRouter:
    """Enruta señales validadas al siguiente paso del pipeline"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.validator = SignalValidator(db_session)
    
    def process_signal(self, signal: NormalizedSignal, user: User) -> Dict[str, Any]:
        """Procesar una señal normalizada"""
        
        # 1. Validar la señal
        validation = self.validator.validate(signal)
        if not validation["is_valid"]:
            logger.warning(f"Signal validation failed: {validation['errors']}")
            return {
                "status": "rejected",
                "reason": "validation_failed",
                "errors": validation["errors"],
                "signal_id": None
            }
        
        # Log warnings if any
        if validation["warnings"]:
            logger.warning(f"Signal warnings: {validation['warnings']}")
        
        # 2. Guardar señal en base de datos
        try:
            db_signal = self._save_signal_to_db(signal, user)
            logger.info(f"Signal saved to DB: {db_signal.id}")
            
            # 3. TODO: Aquí irá el risk management y execution
            # Por ahora, marcamos como "pending" para procesamiento posterior
            
            return {
                "status": "accepted",
                "reason": "signal_queued_for_processing",
                "signal_id": db_signal.id,
                "warnings": validation.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return {
                "status": "error",
                "reason": "database_error",
                "error": str(e),
                "signal_id": None
            }
    
    def _save_signal_to_db(self, signal: NormalizedSignal, user: User) -> Signal:
        """Guardar señal normalizada en la base de datos"""
        
        # Obtener portfolio activo del usuario
        active_portfolio = portfolio_service.get_active(self.db, user)
        if not active_portfolio:
            raise SignalValidationError("User has no active portfolio")
        
        # Crear registro en la base de datos
        db_signal = Signal(
            symbol=signal.symbol,
            action=signal.action.value,
            strategy_id=signal.strategy_id,
            quantity=signal.quantity,
            source=signal.source,
            reason=signal.reason,
            confidence=signal.confidence,
            idempotency_key=signal.idempotency_key,
            status="pending",  # Será procesado por el risk manager
            user_id=user.id,
            portfolio_id=active_portfolio.id
        )
        
        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)
        
        return db_signal
