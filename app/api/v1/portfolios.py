from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ...services import portfolio_service
from ...models.user import User
from ...core.auth import get_current_verified_user

router = APIRouter()


@router.get("/portfolios")
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolios = portfolio_service.get_all(db, current_user)
    return [{"id": p.id, "name": p.name, "is_active": p.is_active} for p in portfolios]


@router.post("/portfolios")
def create_portfolio(
    name: str,
    api_key: str,
    secret_key: str,
    base_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio = portfolio_service.create_portfolio(
        db, current_user, name, api_key, secret_key, base_url
    )
    return {"id": portfolio.id, "name": portfolio.name}


@router.post("/portfolios/{portfolio_id}/activate")
def activate_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio_service.activate_portfolio(db, current_user, portfolio_id)
    return {"status": "ok"}
