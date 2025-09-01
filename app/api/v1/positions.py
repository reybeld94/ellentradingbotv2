from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services.advanced_position_manager import AdvancedPositionManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/positions/current", response_model=Dict[str, Any])
async def get_current_positions(
    portfolio_id: Optional[int] = Query(None, description="Portfolio ID (optional, uses active if not provided)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Obtener todas las posiciones abiertas actuales"""
    try:
        position_manager = AdvancedPositionManager(db)
        positions = position_manager.track_open_positions(current_user.id, portfolio_id)

        if "error" in positions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=positions["error"],
            )

        return positions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current positions",
        )


@router.get("/positions/exposure", response_model=Dict[str, Any])
async def get_exposure_analysis(
    portfolio_id: Optional[int] = Query(None, description="Portfolio ID (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Análisis completo de exposición por símbolo, sector y estrategia"""
    try:
        position_manager = AdvancedPositionManager(db)
        exposure = position_manager.calculate_exposure(current_user.id, portfolio_id)

        if "error" in exposure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exposure["error"],
            )

        return exposure

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating exposure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate exposure",
        )


@router.get("/positions/history", response_model=Dict[str, Any])
async def get_position_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Historial de posiciones en los últimos N días"""
    try:
        position_manager = AdvancedPositionManager(db)
        history = position_manager.get_position_history(current_user.id, days)

        if "error" in history:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=history["error"],
            )

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve position history",
        )


@router.get("/positions/sizing-analysis", response_model=Dict[str, Any])
async def get_position_sizing_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Análisis de patrones de position sizing"""
    try:
        position_manager = AdvancedPositionManager(db)
        analysis = position_manager.analyze_position_sizing(current_user.id)

        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=analysis["error"],
            )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing position sizing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze position sizing",
        )
