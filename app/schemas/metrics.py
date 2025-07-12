from pydantic import BaseModel

class StrategyMetricsSchema(BaseModel):
    strategy_id: str
    total_pl: float
    win_rate: float
    profit_factor: float
    drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    avg_win: float
    avg_loss: float
    win_loss_ratio: float
    expectancy: float
