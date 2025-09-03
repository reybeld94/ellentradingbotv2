import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.trades import Trade
from app.models.user import User
from app.services import portfolio_service
from app.integrations.alpaca.client import AlpacaClient

logger = logging.getLogger(__name__)


class TradeValidator:
    """Valida consistencia entre trades en BD y posiciones reales en Alpaca"""

    def __init__(self, db: Session):
        self.db = db

    def validate_user_trades(self, user_id: int) -> Dict[str, Any]:
        """Valida todos los trades del usuario contra Alpaca"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            active_portfolio = portfolio_service.get_active(self.db, user)
            if not active_portfolio:
                return {"error": "No active portfolio found"}

            # Inicializar cliente Alpaca
            alpaca_client = AlpacaClient(active_portfolio)

            # Obtener trades abiertos en BD
            open_trades = (
                self.db.query(Trade)
                .filter(
                    Trade.user_id == user_id,
                    Trade.portfolio_id == active_portfolio.id,
                    Trade.status == "open",
                )
                .all()
            )

            # Obtener posiciones reales de Alpaca
            try:
                alpaca_positions = alpaca_client.get_all_positions()
            except Exception as e:
                logger.error(f"Error getting Alpaca positions: {e}")
                alpaca_positions = []

            validation_results = []
            issues_found: List[Dict[str, Any]] = []

            # Validar cada trade abierto
            for trade in open_trades:
                alpaca_position = None
                for pos in alpaca_positions:
                    if pos.symbol == trade.symbol:
                        alpaca_position = pos
                        break

                trade_validation = self._validate_single_trade(trade, alpaca_position)
                validation_results.append(trade_validation)

                if trade_validation["has_issues"]:
                    issues_found.append(trade_validation)

            # Buscar posiciones en Alpaca que no están en BD
            orphaned_positions = self._find_orphaned_positions(
                alpaca_positions, open_trades
            )

            return {
                "validation_results": validation_results,
                "issues_found": issues_found,
                "orphaned_positions": orphaned_positions,
                "total_trades_validated": len(validation_results),
                "issues_count": len(issues_found),
                "orphaned_count": len(orphaned_positions),
            }

        except Exception as e:
            logger.error(f"Error in trade validation: {e}")
            return {"error": str(e)}

    def _validate_single_trade(self, trade: Trade, alpaca_position) -> Dict[str, Any]:
        """Valida un trade específico contra posición de Alpaca"""
        issues: List[str] = []

        # Si no hay posición en Alpaca pero el trade está abierto
        if alpaca_position is None:
            issues.append(
                f"Trade {trade.id} shows as open but no position found in Alpaca"
            )
            return {
                "trade_id": trade.id,
                "symbol": trade.symbol,
                "db_quantity": float(trade.quantity),
                "alpaca_quantity": 0,
                "db_pnl": float(trade.pnl or 0),
                "alpaca_pnl": 0,
                "has_issues": True,
                "issues": issues,
            }

        # Comparar cantidades
        db_qty = float(trade.quantity)
        alpaca_qty = float(alpaca_position.qty)

        if abs(db_qty - alpaca_qty) > 0.0001:
            issues.append(f"Quantity mismatch: DB={db_qty}, Alpaca={alpaca_qty}")

        # Comparar PnL
        db_pnl = float(trade.pnl or 0)
        alpaca_pnl = float(getattr(alpaca_position, "unrealized_pl", 0) or 0)

        # Tolerancia del 5% o $1
        pnl_diff = abs(db_pnl - alpaca_pnl)
        if pnl_diff > max(1.0, abs(alpaca_pnl) * 0.05):
            issues.append(f"PnL mismatch: DB={db_pnl:.2f}, Alpaca={alpaca_pnl:.2f}")

        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "db_quantity": db_qty,
            "alpaca_quantity": alpaca_qty,
            "db_pnl": db_pnl,
            "alpaca_pnl": alpaca_pnl,
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _find_orphaned_positions(
        self, alpaca_positions: List, open_trades: List[Trade]
    ) -> List[Dict]:
        """Encuentra posiciones en Alpaca que no están en la BD"""
        orphaned: List[Dict[str, Any]] = []
        trade_symbols = {trade.symbol for trade in open_trades}

        for pos in alpaca_positions:
            if pos.symbol not in trade_symbols:
                orphaned.append(
                    {
                        "symbol": pos.symbol,
                        "quantity": float(pos.qty),
                        "unrealized_pnl": float(getattr(pos, "unrealized_pl", 0) or 0),
                        "market_value": float(getattr(pos, "market_value", 0) or 0),
                    }
                )

        return orphaned

    def cleanup_orphaned_trades(self, user_id: int, dry_run: bool = True) -> Dict[str, Any]:
        """Elimina trades huérfanos (que no existen en Alpaca)"""
        validation = self.validate_user_trades(user_id)

        if "error" in validation:
            return validation

        trades_to_remove = []
        for issue in validation["issues_found"]:
            # Si el trade no tiene posición en Alpaca, marcarlo para eliminación
            if issue["alpaca_quantity"] == 0 and issue["alpaca_pnl"] == 0:
                trades_to_remove.append(issue["trade_id"])

        if dry_run:
            return {
                "dry_run": True,
                "trades_to_remove": trades_to_remove,
                "count": len(trades_to_remove),
            }

        # Eliminar trades huérfanos
        removed_count = 0
        for trade_id in trades_to_remove:
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                self.db.delete(trade)
                removed_count += 1

        self.db.commit()

        return {"removed_count": removed_count, "trades_removed": trades_to_remove}
