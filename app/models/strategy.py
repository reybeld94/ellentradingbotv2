from sqlalchemy import Column, Integer, String, DateTime
from app.utils.time import now_eastern

from app.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_eastern)
    updated_at = Column(DateTime(timezone=True), default=now_eastern, onupdate=now_eastern)

    def __repr__(self):
        return f"<Strategy({self.id}, {self.name})>"

