from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.types import NormalizedSignal
from app.signals.validator import SignalValidator
from app.models.signal import Signal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services import portfolio_service
import logging

logger = logging.getLogger(__name__)

class SignalRouter:
    """Enruta señales validadas al siguiente paso del pipeline"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.validator = SignalValidator(db_session)
    
    def process_signal(self, signal: NormalizedSignal, user: User) -> Dict[str, Any]:
        """Procesar una señal normalizada con risk management"""

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

        # 2. Obtener portfolio activo
        active_portfolio = portfolio_service.get_active(self.db, user)
        if not active_portfolio:
            return {
                "status": "rejected",
                "reason": "no_active_portfolio",
                "errors": ["User has no active portfolio"],
                "signal_id": None
            }

        # 3. NUEVO: Risk Management
        from app.risk.manager import RiskManager
        risk_manager = RiskManager(self.db)

        risk_result = risk_manager.evaluate_signal(signal, user, active_portfolio)
        if not risk_result["approved"]:
            logger.warning(f"Signal rejected by risk manager: {risk_result['reason']}")
            return {
                "status": "rejected",
                "reason": "risk_violation",
                "errors": [risk_result["reason"]],
                "signal_id": None
            }

        # 4. Guardar señal con status "validated" 
        try:
            db_signal = self._save_signal_to_db(signal, user, active_portfolio)
            db_signal.status = "validated"  # Pasó validación Y risk management
            self.db.commit()

            logger.info(f"Signal approved by risk manager: {db_signal.id}")

            # 5. NUEVO: Crear orden automáticamente
            try:
                from app.execution.order_manager import OrderManager

                order_manager = OrderManager(self.db)
                order = order_manager.create_order_from_signal(
                    signal=db_signal,
                    user_id=user.id,
                    portfolio_id=active_portfolio.id
                )

                # Actualizar señal para indicar que tiene orden asociada
                db_signal.status = "processing"
                self.db.commit()

                logger.info(
                    f"Order {order.client_order_id} created for signal {db_signal.id}"
                )

                return {
                    "status": "accepted",
                    "reason": "signal_approved_and_order_created",
                    "signal_id": db_signal.id,
                    "order_id": order.id,
                    "client_order_id": order.client_order_id,
                    "warnings": validation.get("warnings", []),
                    "risk_info": {
                        "suggested_quantity": risk_result["suggested_quantity"],
                        "checks_passed": risk_result.get("checks_passed", [])
                    }
                }

            except Exception as e:
                logger.error(
                    f"Error creating order from signal {db_signal.id}: {e}"
                )
                db_signal.status = "error"
                db_signal.error_message = f"Order creation failed: {str(e)}"
                self.db.commit()

                return {
                    "status": "error",
                    "reason": "order_creation_failed",
                    "error": str(e),
                    "signal_id": db_signal.id
                }

        except Exception as e:
            logger.error(f"Failed to save validated signal: {e}")
            return {
                "status": "error",
                "reason": "database_error",
                "error": str(e),
                "signal_id": None
            }

    def _save_signal_to_db(self, signal: NormalizedSignal, user: User, portfolio: Portfolio) -> Signal:
        """Guardar señal normalizada en la base de datos"""

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
            status="pending",
            user_id=user.id,
            portfolio_id=portfolio.id
        )

        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)

        return db_signal
