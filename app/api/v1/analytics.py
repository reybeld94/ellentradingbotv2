from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services import portfolio_service
from app.analytics.portfolio_analytics import PortfolioAnalytics
from pydantic import BaseModel
from enum import Enum

router = APIRouter()


class TimeframeEnum(str, Enum):
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    ALL_TIME = "ALL"


class PerformanceMetricsResponse(BaseModel):
    total_pnl: float
    total_pnl_percentage: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_hold_time: str
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    avg_win: float
    avg_loss: float
    timeframe: str
    start_date: str
    end_date: str


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    timeframe: TimeframeEnum = Query(TimeframeEnum.ONE_MONTH, description="Período para análisis"),
    portfolio_id: Optional[int] = Query(None, description="ID del portfolio específico (opcional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Obtiene métricas de performance del portfolio"""
    try:
        if portfolio_id:
            portfolio = portfolio_service.get_by_id(db, portfolio_id, current_user.id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
        else:
            portfolio = portfolio_service.get_active(db, current_user)
            if not portfolio:
                raise HTTPException(status_code=400, detail="No active portfolio found")

        analytics = PortfolioAnalytics(db)
        metrics = analytics.get_performance_metrics(
            user_id=current_user.id,
            portfolio_id=portfolio.id,
            timeframe=timeframe.value,
        )
        return PerformanceMetricsResponse(**metrics)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating performance metrics: {str(e)}",
        )


@router.get("/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Obtiene resumen rápido de analytics para dashboard"""
    try:
        portfolio = portfolio_service.get_active(db, current_user)
        if not portfolio:
            raise HTTPException(status_code=400, detail="No active portfolio found")

        analytics = PortfolioAnalytics(db)
        summary: Dict[str, Dict[str, Any]] = {}
        timeframes = ["1D", "1W", "1M", "3M"]

        for tf in timeframes:
            metrics = analytics.get_performance_metrics(
                user_id=current_user.id,
                portfolio_id=portfolio.id,
                timeframe=tf,
            )
            summary[tf.lower()] = {
                "total_pnl": metrics["total_pnl"],
                "total_pnl_percentage": metrics["total_pnl_percentage"],
                "win_rate": metrics["win_rate"],
                "total_trades": metrics["total_trades"],
                "sharpe_ratio": metrics["sharpe_ratio"],
            }

        all_time_metrics = analytics.get_performance_metrics(
            user_id=current_user.id,
            portfolio_id=portfolio.id,
            timeframe="ALL",
        )

        return {
            "timeframes": summary,
            "all_time": {
                "total_pnl": all_time_metrics["total_pnl"],
                "max_drawdown": all_time_metrics["max_drawdown"],
                "profit_factor": all_time_metrics["profit_factor"],
                "largest_win": all_time_metrics["largest_win"],
                "largest_loss": all_time_metrics["largest_loss"],
                "avg_hold_time": all_time_metrics["avg_hold_time"],
            },
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
        }
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=500,
            detail=f"Error getting analytics summary: {str(e)}",
        )
