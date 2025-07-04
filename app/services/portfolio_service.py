from sqlalchemy.orm import Session
from ..models.portfolio import Portfolio
from ..config import settings
from ..integrations.alpaca.client import alpaca_client
import base64
import hashlib
from cryptography.fernet import Fernet


def _get_fernet():
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.secret_key.encode()).digest()
    )
    return Fernet(key)


def create_portfolio(db: Session, name: str, api_key: str, secret_key: str, base_url: str) -> Portfolio:
    f = _get_fernet()
    portfolio = Portfolio(
        name=name,
        api_key_encrypted=f.encrypt(api_key.encode()).decode(),
        secret_key_encrypted=f.encrypt(secret_key.encode()).decode(),
        base_url=base_url,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_all(db: Session):
    return db.query(Portfolio).all()


def get_active(db: Session) -> Portfolio | None:
    active = db.query(Portfolio).filter_by(is_active=True).first()
    if active:
        settings.update_from_portfolio(active)
        alpaca_client.refresh()
    return active


def activate_portfolio(db: Session, portfolio_id: int):
    portfolios = db.query(Portfolio).all()
    for p in portfolios:
        p.is_active = p.id == portfolio_id
    db.commit()
    active = db.query(Portfolio).filter_by(id=portfolio_id).first()
    settings.update_from_portfolio(active)
    alpaca_client.refresh()

