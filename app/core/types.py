from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class SignalAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    LONG_ENTRY = "long_entry"
    LONG_EXIT = "long_exit"
    SHORT_ENTRY = "short_entry"
    SHORT_EXIT = "short_exit"

class SignalStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    PROCESSING = "processing"
    EXECUTED = "executed"
    ERROR = "error"

class OrderStatus(str, Enum):
    NEW = "new"
    SENT = "sent"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    PENDING_CANCEL = "pending_cancel"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

# Schemas para el flujo de datos
class NormalizedSignal(BaseModel):
    """Señal normalizada después de procesar webhook"""
    symbol: str
    action: SignalAction
    strategy_id: str
    quantity: Optional[float] = None
    confidence: Optional[int] = None
    reason: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    source: str = "tradingview"
    raw_payload: Dict[str, Any]
    idempotency_key: str
    fired_at: datetime

class OrderIntent(BaseModel):
    """Intención de orden después de risk management"""
    symbol: str
    action: SignalAction
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_id: str
    client_order_id: str
    rationale: str
