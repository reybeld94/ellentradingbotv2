from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, date


class DailyReportResponse(BaseModel):
    report_date: str
    summary: Dict[str, Any]
    strategy_breakdown: Dict[str, Any]
    top_symbols: List[Dict[str, Any]]
    winning_trades: int
    losing_trades: int
    win_rate: float
    generated_at: str


class WeeklyReportResponse(BaseModel):
    week_start: str
    week_end: str
    summary: Dict[str, Any]
    daily_breakdown: Dict[str, Any]
    best_day: Optional[Dict[str, Any]]
    worst_day: Optional[Dict[str, Any]]
    generated_at: str


class StrategyComparisonResponse(BaseModel):
    comparison_period_days: int
    strategies: List[Dict[str, Any]]
    summary: Dict[str, Any]
    highlights: Dict[str, Any]
    generated_at: str


class PortfolioHealthResponse(BaseModel):
    portfolio_health: Dict[str, Any]
    current_positions: Dict[str, Any]
    exposure_analysis: Dict[str, Any]
    today_performance: Dict[str, Any]
    recommendations: List[str]
    health_metrics: Dict[str, Any]
    generated_at: str


class ReportRequest(BaseModel):
    report_type: str = Field(..., regex="^(daily|weekly|strategy_comparison|portfolio_health)$")
    date: Optional[date] = None
    weeks_back: Optional[int] = Field(default=0, ge=0)
    days_period: Optional[int] = Field(default=30, ge=1, le=365)
