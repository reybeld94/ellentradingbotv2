from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services.trade_reporting import TradeReporting
from app.schemas.reporting import (
    DailyReportResponse,
    WeeklyReportResponse,
    StrategyComparisonResponse,
    PortfolioHealthResponse,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/daily", response_model=DailyReportResponse)
async def get_daily_report(
    report_date: Optional[date] = Query(None, description="Date for report (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Generar reporte diario de trading"""
    try:
        reporting = TradeReporting(db)
        target_date = None

        if report_date:
            target_date = datetime.combine(report_date, datetime.min.time())

        report = reporting.generate_daily_report(current_user.id, target_date)

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=report["error"],
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate daily report",
        )


@router.get("/reports/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    weeks_back: int = Query(0, ge=0, le=52, description="Number of weeks back (0 = current week)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Generar reporte semanal de trading"""
    try:
        reporting = TradeReporting(db)
        report = reporting.generate_weekly_report(current_user.id, weeks_back)

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=report["error"],
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate weekly report",
        )


@router.get("/reports/strategy-comparison", response_model=StrategyComparisonResponse)
async def get_strategy_comparison_report(
    days: int = Query(30, ge=1, le=365, description="Period in days for comparison"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Reporte comparativo de todas las estrategias"""
    try:
        reporting = TradeReporting(db)
        report = reporting.generate_strategy_comparison_report(current_user.id, days)

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=report["error"],
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating strategy comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate strategy comparison",
        )


@router.get("/reports/portfolio-health", response_model=PortfolioHealthResponse)
async def get_portfolio_health_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Reporte completo de salud del portfolio"""
    try:
        reporting = TradeReporting(db)
        report = reporting.generate_portfolio_health_report(current_user.id)

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=report["error"],
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating portfolio health report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate portfolio health report",
        )


@router.get("/reports/summary", response_model=Dict[str, Any])
async def get_reports_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Resumen rápido de todos los reportes para dashboard"""
    try:
        reporting = TradeReporting(db)

        # Generar múltiples reportes en paralelo (simplificado)
        daily = reporting.generate_daily_report(current_user.id)
        weekly = reporting.generate_weekly_report(current_user.id, 0)
        health = reporting.generate_portfolio_health_report(current_user.id)

        # Extraer métricas clave
        summary = {
            "today": {
                "pnl": daily.get("summary", {}).get("daily_pnl", 0),
                "trades": daily.get("summary", {}).get("trades_closed", 0),
                "win_rate": daily.get("win_rate", 0),
            },
            "this_week": {
                "pnl": weekly.get("summary", {}).get("weekly_pnl", 0),
                "trades": weekly.get("summary", {}).get("total_trades", 0),
                "consistency": weekly.get("summary", {}).get("consistency_score", 0),
            },
            "portfolio_health": {
                "risk_level": health.get("portfolio_health", {}).get("risk_level", "Unknown"),
                "risk_score": health.get("portfolio_health", {}).get("risk_score", 0),
                "open_positions": health.get("current_positions", {}).get("total_positions", 0),
                "total_exposure": health.get("exposure_analysis", {}).get("total_exposure_pct", 0),
            },
            "generated_at": datetime.now().isoformat(),
        }

        return summary

    except Exception as e:
        logger.error(f"Error generating reports summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate reports summary",
        )
