# backend/app/schemas/trade.py

from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime

from app.utils.time import to_eastern


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

    @field_serializer('opened_at', 'closed_at', when_used='json')
    def serialize_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return to_eastern(dt).isoformat()


class EquityPointSchema(BaseModel):
    strategy_id: Optional[str] = None
    timestamp: datetime
    equity: float

    @field_serializer('timestamp', when_used='json')
    def serialize_ts(self, dt: datetime) -> str:
        return to_eastern(dt).isoformat()

