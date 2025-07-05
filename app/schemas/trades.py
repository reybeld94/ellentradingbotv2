# backend/app/schemas/trade.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TradeSchema(BaseModel):
    id: int
    strategy_id: str
    symbol: str
    action: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    pnl: Optional[float] = None
    user_id: Optional[int] = None
    portfolio_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EquityPointSchema(BaseModel):
    timestamp: datetime
    equity: float

