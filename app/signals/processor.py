from sqlalchemy.orm import Session
from app.schemas.webhook import TradingViewWebhook
from app.signals.normalizer import SignalNormalizer
from app.signals.router import SignalRouter
from app.models.user import User
from app.execution.bracket_order_processor import BracketOrderProcessor
from typing import Dict, List, Any
import logging
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

            # Additional symbol and quantity checks
            errors = []
            symbol = normalized_signal.symbol
            if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
                errors.append(f"Invalid symbol format: {symbol}")

            quantity = normalized_signal.quantity
            if quantity is not None:
                try:
                    if float(quantity) <= 0:
                        errors.append(f"Invalid quantity: {quantity}")
                except (TypeError, ValueError):
                    errors.append(f"Invalid quantity: {quantity}")

            if errors:
                return {
                    "status": "validation_failed",
                    "errors": errors,
                    "signal_id": None,
                }

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
            bracket_result = await self._create_automatic_bracket_orders(
                signal, user.id, active_portfolio.id
            )

            if bracket_result["status"] == "success":
                logger.info(
                    f"✅ Processed TradingView signal {signal.id} with {bracket_result['orders_created']} bracket orders"
                )

                return {
                    "status": "success",
                    "message": "Signal processed with bracket orders successfully",
                    "signal_id": signal.id,
                    "signal_status": signal.status,
                    "bracket_orders": {
                        "main_order_id": bracket_result["main_order_id"],
                        "exit_orders_count": len(bracket_result["exit_order_ids"]),
                        "exit_prices": bracket_result["exit_prices"],
                    },
                    "risk_evaluation": risk_evaluation,
                }

            elif bracket_result["status"] in ["failed", "error", "critical_error"]:
                logger.error(
                    f"❌ Failed to create bracket orders for signal {signal.id}: {bracket_result['reason']}"
                )

                return {
                    "status": "partial_success",
                    "message": f"Signal processed but bracket orders failed: {bracket_result['reason']}",
                    "signal_id": signal.id,
                    "signal_status": signal.status,
                    "bracket_orders": bracket_result,
                    "risk_evaluation": risk_evaluation,
                }

            else:  # skipped
                logger.info(
                    f"⏭️ Processed TradingView signal {signal.id} - bracket orders skipped: {bracket_result['reason']}"
                )

                return {
                    "status": "success",
                    "message": f"Signal processed - {bracket_result['reason']}",
                    "signal_id": signal.id,
                    "signal_status": signal.status,
                    "bracket_orders": bracket_result,
                    "risk_evaluation": risk_evaluation,
                }

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Processing failed: {str(e)}",
                "signal_id": None
            }

    async def _create_automatic_bracket_orders(
        self, signal: Signal, user_id: int, portfolio_id: int
    ) -> Dict[str, Any]:
        """Crear bracket orders automáticamente para señales de entrada - VERSIÓN COMPLETA"""
        try:
            logger.info(f"Starting bracket order creation for signal {signal.id}")

            # 1. Validar que es una señal de entrada
            if signal.action not in ["buy", "long_entry"]:
                signal.status = "processed_no_bracket"
                self.db.commit()
                return {
                    "status": "skipped",
                    "reason": "Not an entry signal - bracket orders only for entries",
                    "signal_action": signal.action,
                    "orders_created": 0,
                }

            # 2. Verificar que existen reglas de salida para la estrategia
            from app.services.exit_rules_service import ExitRulesService

            exit_rules_service = ExitRulesService(self.db)
            try:
                # Intentar obtener reglas - si no existen, se creará error
                rules = exit_rules_service.get_exit_rules(signal.strategy_id, user_id)
                if not rules:
                    signal.status = "bracket_failed"
                    signal.notes = "No exit rules configured for strategy"
                    self.db.commit()
                    return {
                        "status": "failed",
                        "reason": "No exit rules configured for this strategy",
                        "strategy_id": signal.strategy_id,
                        "orders_created": 0,
                    }
            except Exception as e:
                logger.error(
                    f"Error getting exit rules for strategy {signal.strategy_id}: {str(e)}"
                )
                signal.status = "bracket_failed"
                signal.notes = f"Exit rules error: {str(e)}"
                self.db.commit()
                return {
                    "status": "failed",
                    "reason": f"Exit rules service error: {str(e)}",
                    "orders_created": 0,
                }

            # 3. Validar que el símbolo es tradeable en horarios de mercado
            from app.execution.order_executor import OrderExecutor

            executor = OrderExecutor()

            try:
                market_status = await executor.get_market_hours(signal.symbol)
                if not market_status["is_open"]:
                    signal.status = "bracket_failed"
                    signal.notes = f"Market closed: {market_status.get('status', 'Unknown')}"
                    self.db.commit()
                    return {
                        "status": "failed",
                        "reason": "Market is closed - cannot create bracket orders",
                        "market_status": market_status,
                        "orders_created": 0,
                    }
            except Exception as e:
                logger.warning(
                    f"Could not verify market hours for {signal.symbol}: {str(e)}"
                )
                # Continuar anyway - no bloquear por error de validación de horario

            # 4. Crear bracket order usando OrderManager mejorado
            from app.execution.order_manager import OrderManager

            order_manager = OrderManager(self.db)

            # Usar transacción anidada para rollback parcial si es necesario
            savepoint = self.db.begin_nested()

            try:
                bracket_result = order_manager.create_bracket_order_from_signal(
                    signal, user_id, portfolio_id
                )

                if bracket_result["status"] == "success":
                    # Actualizar estado de la señal a bracket_created
                    signal.status = "bracket_created"
                    signal.notes = (
                        f"Bracket orders created: 1 entry + {len(bracket_result['exit_orders'])} exits"
                    )

                    # Commit de la transacción anidada
                    savepoint.commit()

                    # Inicializar seguimiento automático si hay OrderProcessor
                    try:
                        await self._initialize_bracket_tracking(
                            bracket_result["main_order_id"]
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not initialize bracket tracking: {str(e)}"
                        )
                        # No fallar por esto

                    logger.info(
                        f"Successfully created bracket orders for signal {signal.id}: main_order={bracket_result['main_order_id']}"
                    )

                    return {
                        "status": "success",
                        "main_order_id": bracket_result["main_order_id"],
                        "exit_order_ids": bracket_result["exit_orders"],
                        "exit_prices": bracket_result["exit_prices"],
                        "orders_created": 1 + len(bracket_result["exit_orders"]),
                        "strategy_id": signal.strategy_id,
                        "symbol": signal.symbol,
                    }

                else:
                    # Rollback de la transacción anidada
                    savepoint.rollback()

                    signal.status = "bracket_failed"
                    signal.notes = (
                        f"Bracket creation failed: {bracket_result.get('message', 'Unknown error')}"
                    )

                    logger.error(
                        f"Failed to create bracket orders for signal {signal.id}: {bracket_result}"
                    )

                    return {
                        "status": "failed",
                        "reason": bracket_result.get(
                            "message", "OrderManager returned failure"
                        ),
                        "orders_created": 0,
                        "details": bracket_result,
                    }

            except Exception as e:
                # Rollback de la transacción anidada
                savepoint.rollback()

                signal.status = "bracket_failed"
                signal.notes = f"Exception in bracket creation: {str(e)}"

                logger.error(
                    f"Exception creating bracket orders for signal {signal.id}: {str(e)}"
                )

                return {
                    "status": "error",
                    "reason": f"Exception in bracket creation: {str(e)}",
                    "orders_created": 0,
                }

            finally:
                # Commit del estado de la señal
                self.db.commit()

        except Exception as e:
            logger.error(
                f"Critical error in _create_automatic_bracket_orders for signal {signal.id}: {str(e)}"
            )

            # Intentar actualizar estado de señal si es posible
            try:
                signal.status = "error"
                signal.notes = f"Critical error: {str(e)}"
                self.db.commit()
            except:
                pass

            return {
                "status": "critical_error",
                "reason": str(e),
                "orders_created": 0,
            }


    async def _initialize_bracket_tracking(self, main_order_id: int) -> None:
        """Inicializar seguimiento automático de bracket order"""
        try:
            # Si tienes OrderProcessor background, notificarle aquí
            from app.execution.order_processor import OrderProcessor

            processor = OrderProcessor(self.db)
            await processor.start_tracking_order(main_order_id)

            logger.info(f"Initialized bracket tracking for order {main_order_id}")

        except ImportError:
            # OrderProcessor no existe aún - skip
            logger.debug("OrderProcessor not available for bracket tracking")
        except Exception as e:
            logger.error(f"Error initializing bracket tracking: {str(e)}")
            raise


    async def test_bracket_integration(self, test_symbol: str = "AAPL") -> Dict[str, Any]:
        """Test completo de integración de bracket orders"""
        try:
            # Crear señal de prueba
            test_signal = Signal(
                symbol=test_symbol,
                action="buy",
                strategy_id="test_strategy",
                quantity=1.0,
                status="validated",
                user_id=1,  # Usuario de prueba
                portfolio_id=1,
                confidence=85,
                reason="integration_test",
            )

            self.db.add(test_signal)
            self.db.flush()

            # Probar creación de bracket orders
            bracket_result = await self._create_automatic_bracket_orders(
                test_signal, 1, 1
            )

            # Cleanup - rollback test data
            self.db.rollback()

            return {
                "test_status": "completed",
                "bracket_result": bracket_result,
                "test_signal_id": test_signal.id,
                "message": "Bracket integration test completed (no data saved)",
            }

        except Exception as e:
            self.db.rollback()
            return {
                "test_status": "failed",
                "error": str(e),
                "message": "Bracket integration test failed",
            }

    def _get_active_portfolio(self, user_id: int):
        """Obtener portfolio activo del usuario"""
        from app.models.portfolio import Portfolio
        return self.db.query(Portfolio).filter(
            Portfolio.user_id == user_id,
            Portfolio.is_active == True
        ).first()
