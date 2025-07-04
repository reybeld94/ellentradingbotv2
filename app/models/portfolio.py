from sqlalchemy import Column, Integer, String, Boolean
from ..database import Base

class Portfolio(Base):
    __tablename__ = 'portfolios'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    api_key_encrypted = Column(String(255), nullable=False)
    secret_key_encrypted = Column(String(255), nullable=False)
    base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)
