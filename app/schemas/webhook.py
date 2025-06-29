# backend/app/schemas/webhook.py

from pydantic import BaseModel
from typing import Optional


class TradingViewWebhook(BaseModel):
    symbol: str
    action: str  # "buy" or "sell"
    strategy_id: str  # Identificador único de la estrategia
    quantity: Optional[int] = None
    price: Optional[float] = None
    message: Optional[str] = None

    # Nuevos campos de la estrategia Fibonacci
    reason: Optional[str] = None  # "fibonacci_entry", "fibonacci_exit", "trailing_stop"
    confidence: Optional[int] = None  # Score de confianza 0-100
    timestamp: Optional[str] = None  # Timestamp de TradingView


class WebhookResponse(BaseModel):
    status: str
    message: str
    signal_id: Optional[int] = None