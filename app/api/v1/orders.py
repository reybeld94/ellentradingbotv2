# backend/app/api/v1/orders.py

from fastapi import APIRouter, Depends, HTTPException
from alpaca.common.exceptions import APIError
from sqlalchemy.orm import Session
import logging
from app.integrations import broker_client
from app.services.position_manager import position_manager
from app.database import get_db
from app.models.signal import Signal
from app.models.user import User
from app.core.auth import get_current_verified_user, get_admin_user
from app.services import portfolio_service
from app.utils.time import to_eastern

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/orders")
async def get_orders(
        current_user: User = Depends(get_current_verified_user)
):
    """Ver órdenes en la cuenta del broker"""
    try:
        orders = broker_client.list_orders(status="all", limit=200)

        if not orders:
            return {
                "orders": [],
                "message": "No orders found in your account",
                "user": current_user.username,
                "total_count": 0
            }

        def _get_value(obj, attr):
            value = getattr(obj, attr, None)
            if hasattr(value, "value"):
                value = value.value
            return value

        def _to_str(value):
            return "" if value is None else str(value)

        def _format_dt(value):
            return value.isoformat() if value else None

        order_list = []
        for order in orders:
            try:
                order_data = {
                    "id": _to_str(_get_value(order, "id")),
                    "symbol": _to_str(_get_value(order, "symbol")),
                    "qty": _to_str(_get_value(order, "qty")),
                    "side": _to_str(_get_value(order, "side")),
                    "status": _to_str(_get_value(order, "status")),
                    "order_type": _to_str(_get_value(order, "order_type")),
                    "time_in_force": _to_str(_get_value(order, "time_in_force")),
                    "submitted_at": _format_dt(_get_value(order, "submitted_at")),
                    "filled_at": _format_dt(_get_value(order, "filled_at")),
                    "filled_qty": _to_str(_get_value(order, "filled_qty")),
                    "filled_avg_price": _to_str(_get_value(order, "filled_avg_price")),
                    "rejected_reason": _get_value(order, "rejected_reason"),
                }
                order_list.append(order_data)
            except (AttributeError, TypeError, ValueError) as order_exc:
                logger.warning("Failed to process order %s: %s", getattr(order, "id", "unknown"), order_exc)
                continue

        return {
            "orders": order_list,
            "total_count": len(order_list),
            "user": current_user.username
        }

    except APIError as e:
        logger.exception("Alpaca API error fetching orders")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception:
        logger.exception("Unexpected error fetching orders")
        raise


@router.get("/account")
async def get_account(
        current_user: User = Depends(get_current_verified_user)
):
    """Ver info de cuenta del broker"""
    try:
        account = broker_client.get_account()

        portfolio_value = float(getattr(account, "portfolio_value", 0))
        cash = float(getattr(account, "cash", 0))
        buying_power = float(getattr(account, "buying_power", 0))
        prev_close = float(getattr(account, "last_equity", portfolio_value))
        day_change = portfolio_value - prev_close
        day_change_percent = (day_change / prev_close * 100) if prev_close else 0

        return {
            "buying_power": buying_power,
            "cash": cash,
            "portfolio_value": portfolio_value,
            "day_change": day_change,
            "day_change_percent": day_change_percent,
            "prev_close": prev_close,
            "status": str(getattr(account, "status", "N/A")),
            "trading_blocked": getattr(account, "trading_blocked", False),
            "crypto_status": str(getattr(account, "crypto_trading_enabled", False)),
            "pattern_day_trader": getattr(account, "pattern_day_trader", False),
            "day_trade_count": getattr(account, "day_trade_count", 0),
            "user": current_user.username,
        }
    except APIError as e:
        logger.exception("Alpaca API error fetching account info")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception:
        logger.exception("Unexpected error fetching account info")
        raise


@router.get("/positions")
async def get_positions(
        current_user: User = Depends(get_current_verified_user)
):
    """Ver posiciones actuales"""
    try:
        portfolio_summary = position_manager.get_portfolio_summary(
            current_user.position_limit
        )
        portfolio_summary["user"] = current_user.username
        return portfolio_summary
    except APIError as e:
        logger.exception("Alpaca API error fetching positions")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception:
        logger.exception("Unexpected error fetching positions")
        raise


@router.get("/signals")
async def get_signals(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_verified_user)
):
    """Ver señales del usuario actual"""
    if current_user.is_admin:
        # Admin puede ver todas
        signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(50).all()
    else:
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
            "quantity": signal.quantity,
            "status": signal.status,
            "error_message": signal.error_message,
            "timestamp": to_eastern(signal.timestamp).isoformat(),
            "strategy_id": signal.strategy_id,
            "source": "tradingview"
        }
        for signal in signals
    ]


# Endpoints administrativos
@router.get("/admin/all-signals")
async def get_all_signals(
        db: Session = Depends(get_db),
        admin_user: User = Depends(get_admin_user)
):
    """Ver todas las señales de todos los usuarios (solo admin)"""
    signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(100).all()

    return [
        {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "strategy_id": signal.strategy_id,
            "quantity": signal.quantity,
            "status": signal.status,
            "timestamp": to_eastern(signal.timestamp).isoformat(),
            "user_id": signal.user_id,
            "username": signal.user.username if signal.user else "Unknown"
        }
        for signal in signals
    ]


@router.get("/admin/user-stats")
async def get_user_stats(
        db: Session = Depends(get_db),
        admin_user: User = Depends(get_admin_user)
):
    """Estadísticas de usuarios (solo admin)"""
    from sqlalchemy import func
    from app.models.user import User

    stats = db.query(
        func.count(Signal.id).label('total_signals'),
        Signal.user_id,
        User.username
    ).join(User).group_by(Signal.user_id, User.username).all()

    return [
        {
            "user_id": stat.user_id,
            "username": stat.username,
            "total_signals": stat.total_signals
        }
        for stat in stats
    ]
