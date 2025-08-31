from sqlalchemy.orm import Session
from app.schemas.webhook import TradingViewWebhook
from app.signals.normalizer import SignalNormalizer
from app.signals.router import SignalRouter
from app.models.user import User
from typing import Dict, Any
import logging
from app.execution.order_manager import OrderManager
from app.models.signal import Signal

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """Procesador principal de webhooks - orquesta todo el flujo"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.normalizer = SignalNormalizer()
        self.router = SignalRouter(db_session)
    
    async def process_tradingview_webhook(self, webhook_data: TradingViewWebhook, user: User) -> Dict[str, Any]:
        """Procesar webhook de TradingView con bracket orders automáticas"""
        try:
            # 1. Pipeline existente (normalizar, validar, risk management)
            normalized_signal = self.normalizer.from_tradingview(webhook_data)

            if self.normalizer.is_duplicate(normalized_signal.idempotency_key, self.db):
                return {
                    "status": "duplicate",
                    "message": f"Signal already processed: {normalized_signal.idempotency_key}",
                    "signal_id": None
                }

            validation = self.router.validator.validate(normalized_signal)
            if not validation["is_valid"]:
                return {
                    "status": "validation_failed",
                    "errors": validation["errors"],
                    "signal_id": None
                }

            # 2. Risk Management
            from app.risk.manager import RiskManager
            risk_manager = RiskManager(self.db)

            active_portfolio = self._get_active_portfolio(user.id)
            if not active_portfolio:
                return {
                    "status": "error",
                    "message": "No active portfolio found",
                    "signal_id": None
                }

            risk_evaluation = risk_manager.evaluate_signal(normalized_signal, user, active_portfolio)
            if not risk_evaluation["approved"]:
                return {
                    "status": "risk_rejected",
                    "reason": risk_evaluation["reason"],
                    "signal_id": None
                }

            # 3. Crear y guardar señal como "validated"
            signal = Signal(
                symbol=normalized_signal.symbol,
                action=normalized_signal.action,
                strategy_id=normalized_signal.strategy_id,
                quantity=risk_evaluation.get("suggested_quantity"),
                confidence=normalized_signal.confidence,
                reason=normalized_signal.reason,
                status="validated",
                idempotency_key=normalized_signal.idempotency_key,
                user_id=user.id,
                portfolio_id=active_portfolio.id,
            )

            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)

            # 4. NUEVA FUNCIONALIDAD: Crear bracket orders automáticamente
            bracket_result = await self._create_automatic_bracket_orders(signal, user.id, active_portfolio.id)

            logger.info(
                f"Processed TradingView signal {signal.id} with bracket orders: {bracket_result['status']}"
            )

            return {
                "status": "success",
                "message": "Signal processed with bracket orders",
                "signal_id": signal.id,
                "bracket_orders": bracket_result,
                "risk_evaluation": risk_evaluation
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Processing failed: {str(e)}",
                "signal_id": None
            }

    async def _create_automatic_bracket_orders(self, signal: Signal, user_id: int, portfolio_id: int) -> Dict[str, Any]:
        """Crear bracket orders automáticamente para señales de entrada"""
        try:
            # Solo crear bracket orders para acciones de entrada
            if signal.action not in ["buy", "long_entry"]:
                return {
                    "status": "skipped",
                    "reason": "Not an entry signal",
                    "orders_created": 0
                }

            # Crear bracket orders usando OrderManager
            order_manager = OrderManager(self.db)
            result = order_manager.create_bracket_order_from_signal(signal, user_id, portfolio_id)

            if result["status"] == "success":
                # Actualizar el estado de la señal
                signal.status = "bracket_created"
                self.db.commit()

                return {
                    "status": "success",
                    "main_order_id": result["main_order_id"],
                    "exit_order_ids": result["exit_orders"],
                    "exit_prices": result["exit_prices"],
                    "orders_created": 1 + len(result["exit_orders"])
                }
            else:
                return {
                    "status": "failed",
                    "reason": result["message"],
                    "orders_created": 0
                }

        except Exception as e:
            logger.error(f"Error creating bracket orders for signal {signal.id}: {str(e)}")
            return {
                "status": "error",
                "reason": str(e),
                "orders_created": 0
            }

    def _get_active_portfolio(self, user_id: int):
        """Obtener portfolio activo del usuario"""
        from app.models.portfolio import Portfolio
        return self.db.query(Portfolio).filter(
            Portfolio.user_id == user_id,
            Portfolio.is_active == True
        ).first()
