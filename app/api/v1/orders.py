# backend/app/api/v1/orders.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...integrations.alpaca.client import alpaca_client
from ...services.position_manager import position_manager
from ...database import get_db
from ...models.signal import Signal

router = APIRouter()

@router.get("/orders")
async def get_alpaca_orders():
    """Ver órdenes en Alpaca"""
    try:
        orders = alpaca_client.api.list_orders(status='all', limit=10)
        return [
            {
                "id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side,
                "status": order.status,
                "submitted_at": order.submitted_at,
                "filled_at": getattr(order, 'filled_at', None),
                "rejected_reason": getattr(order, 'rejected_reason', None)
            }
            for order in orders
        ]
    except Exception as e:
        return {"error": str(e)}

@router.get("/account")
async def get_account():
    """Ver info de cuenta Alpaca"""
    try:
        account = alpaca_client.get_account()
        return {
            "buying_power": account.buying_power,
            "cash": account.cash,
            "portfolio_value": account.portfolio_value,
            "status": account.status,
            "trading_blocked": account.trading_blocked,
            "crypto_status": getattr(account, 'crypto_status', 'unknown')
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/positions")
async def get_positions():
    """Ver posiciones actuales y resumen del portafolio"""
    try:
        return position_manager.get_portfolio_summary()
    except Exception as e:
        return {"error": str(e)}

@router.get("/signals")
async def get_signals(db: Session = Depends(get_db)):
    """Ver señales en nuestra base de datos"""
    signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(10).all()
    return [
        {
            "id": signal.id,
            "symbol": signal.symbol,
            "action": signal.action,
            "quantity": signal.quantity,
            "status": signal.status,
            "error_message": signal.error_message,
            "timestamp": signal.timestamp
        }
        for signal in signals
    ]

@router.get("/test-crypto-quote/{symbol}")
async def test_crypto_quote(symbol: str):
    """Probar obtener precio de crypto"""
    try:
        quote = alpaca_client.get_latest_crypto_quote(symbol)
        return {
            "symbol": symbol,
            "price": quote.price,
            "timestamp": quote.timestamp
        }
    except Exception as e:
        return {"error": str(e)}