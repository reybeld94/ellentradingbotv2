from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator


class EntryRules(BaseModel):
    indicators: List[str] = []
    conditions: List[Dict[str, Any]] = []
    timeframe: str = "1h"


class ExitRules(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    max_hold_time: Optional[int] = None  # en horas


class RiskParameters(BaseModel):
    max_position_size: float = 0.05  # 5% del capital
    max_daily_loss: Optional[float] = None
    max_correlation: Optional[float] = 0.7


class PositionSizing(BaseModel):
    type: str = "fixed"  # fixed, percentage, kelly, etc
    amount: Optional[float] = None
    percentage: Optional[float] = None


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    entry_rules: EntryRules
    exit_rules: ExitRules
    risk_parameters: RiskParameters
    position_sizing: PositionSizing
    is_active: bool = True


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entry_rules: Optional[EntryRules] = None
    exit_rules: Optional[ExitRules] = None
    risk_parameters: Optional[RiskParameters] = None
    position_sizing: Optional[PositionSizing] = None
    is_active: Optional[bool] = None


class StrategyOut(StrategyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

