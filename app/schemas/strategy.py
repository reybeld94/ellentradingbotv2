from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class StrategyOut(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
