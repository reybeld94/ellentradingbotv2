import random
import statistics
from typing import List, Iterable, Dict

from ..models.trades import Trade


class MonteCarloAnalyzer:
    """Simple Monte Carlo analyzer for trade results."""

    def __init__(self, trades: Iterable[Trade]):
        self.trades = list(trades)

    def _trade_returns(self) -> List[float]:
        """Return list of trade returns as fraction of capital used."""
        returns = []
        for t in self.trades:
            if t.entry_price and t.quantity:
                capital = t.entry_price * t.quantity
                if capital != 0:
                    returns.append((t.pnl or 0.0) / capital)
        return returns

    def kelly_fraction(self) -> float:
        """Estimate optimal fixed fraction using the Kelly criterion."""
        returns = self._trade_returns()
        if not returns:
            return 0.0
        wins = [r for r in returns if r > 0]
        losses = [-r for r in returns if r < 0]
        if not losses:
            return 0.0
        win_rate = len(wins) / len(returns)
        avg_win = statistics.mean(wins) if wins else 0.0
        avg_loss = statistics.mean(losses)
        if avg_loss == 0:
            return 0.0
        reward_to_risk = avg_win / avg_loss
        return max(win_rate - (1 - win_rate) / reward_to_risk, 0.0)

    def run_simulation(
        self, iterations: int = 1000, starting_balance: float = 1.0
    ) -> List[Dict[str, float]]:
        """Run Monte Carlo simulations of equity curves."""
        returns = self._trade_returns()
        if not returns:
            return []
        results = []
        for _ in range(iterations):
            balance = starting_balance
            peak = balance
            max_dd = 0.0
            for r in random.sample(returns, len(returns)):
                balance *= 1 + r
                if balance > peak:
                    peak = balance
                dd = (peak - balance) / peak
                if dd > max_dd:
                    max_dd = dd
            results.append({"final_balance": balance, "max_drawdown": max_dd})
        return results

    def summarize(
        self, iterations: int = 1000, starting_balance: float = 1.0
    ) -> Dict[str, float]:
        """Return statistics from the Monte Carlo simulation."""
        sims = self.run_simulation(iterations=iterations, starting_balance=starting_balance)
        if not sims:
            return {}
        finals = [s["final_balance"] for s in sims]
        drawdowns = [s["max_drawdown"] for s in sims]
        return {
            "median_final_balance": statistics.median(finals),
            "worst_final_balance": min(finals),
            "average_drawdown": statistics.mean(drawdowns),
            "max_drawdown": max(drawdowns),
        }
