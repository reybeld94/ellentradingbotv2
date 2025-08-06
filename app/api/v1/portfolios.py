from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import portfolio_service
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
)

router = APIRouter()


@router.get("/portfolios", response_model=list[PortfolioResponse])
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolios = portfolio_service.get_all(db, current_user)
    return portfolios


@router.get("/portfolios/active", response_model=PortfolioResponse)
def get_active_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    active = portfolio_service.get_active(db, current_user)
    if not active:
        raise HTTPException(status_code=404, detail="No active portfolio")
    return active


@router.post("/portfolios", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio_obj = portfolio_service.create_portfolio(
        db,
        current_user,
        portfolio.name,
        portfolio.api_key,
        portfolio.secret_key,
        portfolio.base_url,
        portfolio.is_paper,
    )
    return portfolio_obj


@router.post("/portfolios/{portfolio_id}/activate")
def activate_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio_service.activate_portfolio(db, current_user, portfolio_id)
    return {"status": "ok"}


@router.post("/portfolios/{portfolio_id}/deactivate")
def deactivate_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio_service.deactivate_portfolio(db, current_user, portfolio_id)
    return {"status": "ok"}


@router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    updates: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio = portfolio_service.update_portfolio(db, current_user, portfolio_id, **updates.model_dump(exclude_unset=True))
    return portfolio


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio_service.delete_portfolio(db, current_user, portfolio_id)
    return None
