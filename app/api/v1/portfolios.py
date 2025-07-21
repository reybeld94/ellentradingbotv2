from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import portfolio_service
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse

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
        portfolio.broker,
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
