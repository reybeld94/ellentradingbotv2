from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.time import now_eastern

class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id = Column(Integer, primary_key=True, index=True)
    
    # Límites de drawdown
    max_daily_drawdown = Column(Float, nullable=False, default=0.02)  # 2%
    max_weekly_drawdown = Column(Float, nullable=False, default=0.05)  # 5%
    max_account_drawdown = Column(Float, nullable=False, default=0.10)  # 10%
    
    # Límites de exposición
    max_position_size = Column(Float, nullable=False, default=0.05)  # 5% del capital por posición
    max_symbol_exposure = Column(Float, nullable=False, default=0.10)  # 10% por símbolo
    max_sector_exposure = Column(Float, nullable=False, default=0.25)  # 25% por sector
    max_total_exposure = Column(Float, nullable=False, default=0.95)  # 95% máximo invertido
    
    # Límites operacionales
    max_orders_per_hour = Column(Integer, nullable=False, default=10)
    max_orders_per_day = Column(Integer, nullable=False, default=50)
    max_open_positions = Column(Integer, nullable=False, default=10)
    
    # Horarios de trading
    trading_start_time = Column(String(8), nullable=False, default="09:30:00")  # HH:MM:SS EST
    trading_end_time = Column(String(8), nullable=False, default="15:30:00")   # HH:MM:SS EST
    allow_extended_hours = Column(Boolean, default=False)
    
    # Filtros de mercado
    min_price = Column(Float, nullable=False, default=1.0)  # No penny stocks
    max_price = Column(Float, nullable=True)  # Sin límite por defecto
    min_volume = Column(Integer, nullable=False, default=100000)  # Volumen mínimo diario
    max_spread_percent = Column(Float, nullable=False, default=0.02)  # 2% máximo spread
    
    # Control de noticias/eventos
    block_earnings_days = Column(Boolean, default=True)
    block_fomc_days = Column(Boolean, default=True)
    block_news_sentiment_negative = Column(Boolean, default=False)
    
    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=now_eastern)
    updated_at = Column(DateTime(timezone=True), default=now_eastern, onupdate=now_eastern)
    
    # Relaciones
    user = relationship("User")
    portfolio = relationship("Portfolio")

    def __repr__(self):
        return f"<RiskLimit(user:{self.user_id}, portfolio:{self.portfolio_id}, max_dd:{self.max_daily_drawdown})>"
