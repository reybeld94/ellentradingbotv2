from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.portfolio import Portfolio
from app.models.user import User
from app.config import settings
from app.integrations.alpaca.client import alpaca_client
from app.integrations import refresh_broker_client
import base64
import hashlib
from cryptography.fernet import Fernet


def _get_fernet():
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.secret_key.encode()).digest()
    )
    return Fernet(key)


def create_portfolio(
    db: Session,
    user: User,
    name: str,
    api_key: str,
    secret_key: str,
    base_url: str,
    is_paper: bool | None = None,
) -> Portfolio:
    f = _get_fernet()
    if is_paper is None:
        is_paper = "paper" in base_url.lower()
    portfolio = Portfolio(
        name=name,
        api_key_encrypted=f.encrypt(api_key.encode()).decode(),
        secret_key_encrypted=f.encrypt(secret_key.encode()).decode(),
        base_url=base_url,
        broker="alpaca",
        is_paper=is_paper,
        user_id=user.id,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    # If the user doesn't have an active portfolio yet, activate the new one
    existing_active = (
        db.query(Portfolio)
        .filter_by(user_id=user.id, is_active=True)
        .first()
    )
    if not existing_active:
        activate_portfolio(db, user, portfolio.id)
        db.refresh(portfolio)

    return portfolio


def get_all(db: Session, user: User):
    return db.query(Portfolio).filter_by(user_id=user.id).all()


def get_active(db: Session, user: User | None = None) -> Portfolio | None:
    query = db.query(Portfolio)
    if user:
        query = query.filter_by(user_id=user.id)
    active = query.filter_by(is_active=True).first()
    if active:
        settings.update_from_portfolio(active)
        alpaca_client.refresh()
    else:
        settings.clear_alpaca_credentials()
        alpaca_client.refresh()
    refresh_broker_client()
    return active


def activate_portfolio(db: Session, user: User, portfolio_id: int):
    portfolios = db.query(Portfolio).filter_by(user_id=user.id).all()
    for p in portfolios:
        p.is_active = p.id == portfolio_id
    db.commit()
    active = db.query(Portfolio).filter_by(id=portfolio_id, user_id=user.id).first()
    settings.update_from_portfolio(active)
    alpaca_client.refresh()
    refresh_broker_client()


def deactivate_portfolio(db: Session, user: User, portfolio_id: int):
    portfolio = (
        db.query(Portfolio)
        .filter_by(id=portfolio_id, user_id=user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    portfolio.is_active = False
    db.commit()
    get_active(db, user)


def update_portfolio(db: Session, user: User, portfolio_id: int, **updates) -> Portfolio:
    portfolio = (
        db.query(Portfolio)
        .filter_by(id=portfolio_id, user_id=user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    f = _get_fernet()
    for field, value in updates.items():
        if value is None:
            continue
        if field == "api_key":
            portfolio.api_key_encrypted = f.encrypt(value.encode()).decode()
        elif field == "secret_key":
            portfolio.secret_key_encrypted = f.encrypt(value.encode()).decode()
        elif field == "broker":
            continue
        elif hasattr(portfolio, field):
            setattr(portfolio, field, value)
    db.commit()
    db.refresh(portfolio)
    if portfolio.is_active:
        settings.update_from_portfolio(portfolio)
        alpaca_client.refresh()
        refresh_broker_client()
    return portfolio


def delete_portfolio(db: Session, user: User, portfolio_id: int):
    portfolio = (
        db.query(Portfolio)
        .filter_by(id=portfolio_id, user_id=user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    was_active = portfolio.is_active
    db.delete(portfolio)
    db.commit()
    if was_active:
        get_active(db, user)
