"""Strategy management endpoints.

This module exposes a full CRUD API for strategy management using the
``StrategyManager`` service.  Each endpoint validates that the authenticated user
owns the strategy and leverages the manager for validation and persistence.  In
addition to the basic CRUD operations we provide activation and configuration
validation endpoints to mirror the behaviour of the service layer.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut
from app.services.strategy_manager import StrategyManager
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/strategies", response_model=List[StrategyOut])
async def list_strategies(
    active_only: bool = Query(False, description="Only return active strategies"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """List all strategies belonging to the current user."""
    try:
        strategy_manager = StrategyManager(db)
        strategies = strategy_manager.get_user_strategies(
            user_id=current_user.id, active_only=active_only
        )
        return strategies
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategies",
        )


@router.post("/strategies", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Create a new strategy for the authenticated user."""
    try:
        strategy_manager = StrategyManager(db)

        # Validate configuration prior to creation
        validation = strategy_manager.validate_strategy_config(strategy)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Strategy configuration invalid",
                    "errors": validation["errors"],
                    "warnings": validation["warnings"],
                },
            )

        new_strategy = strategy_manager.create_strategy(
            user_id=current_user.id, config=strategy
        )

        if validation["warnings"]:
            logger.warning(
                "Strategy created with warnings: %s", validation["warnings"]
            )

        return new_strategy

    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create strategy",
        )


@router.get("/strategies/{strategy_id}", response_model=StrategyOut)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Retrieve a specific strategy owned by the current user."""
    try:
        strategy_manager = StrategyManager(db)
        strategy = strategy_manager.get_strategy_by_id(
            strategy_id=strategy_id, user_id=current_user.id
        )

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        return strategy

    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error retrieving strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy",
        )


@router.put("/strategies/{strategy_id}", response_model=StrategyOut)
async def update_strategy(
    strategy_id: int,
    updates: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Update an existing strategy."""
    try:
        strategy_manager = StrategyManager(db)

        existing_strategy = strategy_manager.get_strategy_by_id(
            strategy_id=strategy_id, user_id=current_user.id
        )

        if not existing_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        updated_strategy = strategy_manager.update_strategy(
            strategy_id=strategy_id, user_id=current_user.id, updates=updates
        )
        return updated_strategy

    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error updating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy",
        )


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Soft delete (deactivate) a strategy."""
    try:
        strategy_manager = StrategyManager(db)
        success = strategy_manager.delete_strategy(
            strategy_id=strategy_id, user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy",
        )


@router.post("/strategies/{strategy_id}/activate", response_model=StrategyOut)
async def activate_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Reactivate a previously deactivated strategy."""
    try:
        strategy_manager = StrategyManager(db)
        strategy = strategy_manager.get_strategy_by_id(strategy_id, current_user.id)

        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        updates = StrategyUpdate(is_active=True)
        updated_strategy = strategy_manager.update_strategy(
            strategy_id=strategy_id, user_id=current_user.id, updates=updates
        )
        return updated_strategy

    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error activating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate strategy",
        )


@router.post("/strategies/validate", status_code=status.HTTP_200_OK)
async def validate_strategy_config(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Validate a strategy configuration without creating it."""
    try:
        strategy_manager = StrategyManager(db)
        validation = strategy_manager.validate_strategy_config(strategy)
        return {
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "message": "Configuration valid"
            if validation["valid"]
            else "Configuration has errors",
        }
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error(f"Error validating strategy config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate configuration",
        )

