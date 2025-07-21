from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    api_key_encrypted = Column(String(255), nullable=False)
    secret_key_encrypted = Column(String(255), nullable=False)
    base_url = Column(String(255), nullable=False)
    broker = Column(String(20), nullable=False, default="kraken")
    is_paper = Column(Boolean, nullable=True)
    is_active = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="portfolios")
    signals = relationship("Signal", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")
