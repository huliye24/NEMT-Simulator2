"""
RiskCalculator - 风险计算器

提供风险管理、风险指标计算能力。
"""

import logging
import math

__all__ = [
    "RiskMetrics",
    "RiskCalculator",
]


class RiskMetrics:
    """风险指标"""

    def __init__(
        self,
        total_exposure: float = 0,
        daily_var: float = 0,  # 日 VaR
        monthly_var: float = 0,  # 月 VaR
        max_drawdown: float = 0,
        sharpe_ratio: float = 0,
        sortino_ratio: float = 0,
        beta: float = 0,
        volatility: float = 0,
    ):
        self.total_exposure = total_exposure
        self.daily_var = daily_var
        self.monthly_var = monthly_var
        self.max_drawdown = max_drawdown
        self.sharpe_ratio = sharpe_ratio
        self.sortino_ratio = sortino_ratio
        self.beta = beta
        self.volatility = volatility

    def to_dict(self) -> dict:
        return {
            "total_exposure": self.total_exposure,
            "daily_var": self.daily_var,
            "monthly_var": self.monthly_var,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "beta": self.beta,
            "volatility": self.volatility,
        }


class RiskCalculator:
    """
    风险计算器

    示例:
    ```python
    calculator = RiskCalculator()

    # 计算风险指标
    metrics = calculator.calculate(
        returns=[0.01, -0.02, 0.03, -0.01, 0.02],
        portfolio_value=100000,
        benchmark_returns=[0.005, -0.01, 0.02, -0.005, 0.01],
    )

    print(f"VaR (95%): {metrics.daily_var}")
    print(f"夏普比率: {metrics.sharpe_ratio}")
    ```
    """

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self._logger = logging.getLogger("RiskCalculator")

    def calculate(
        self,
        returns: list[float],
        portfolio_value: float = 100000,
        benchmark_returns: list[float] = None,
    ) -> RiskMetrics:
        """计算风险指标"""
        if not returns:
            return RiskMetrics()

        # 基本统计
        n = len(returns)
        mean_return = sum(returns) / n

        # 波动率
        variance = sum((r - mean_return) ** 2 for r in returns) / n
        volatility = math.sqrt(variance * 252) if variance > 0 else 0  # 年化波动率

        # VaR (Value at Risk)
        sorted_returns = sorted(returns)
        var_index = int(n * (1 - self.confidence_level))
        daily_var = abs(sorted_returns[var_index]) * portfolio_value if var_index < n else 0
        monthly_var = daily_var * math.sqrt(21)  # 月 VaR

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(returns)

        # 夏普比率
        risk_free_rate = 0.02 / 252  # 日无风险利率
        excess_return = mean_return - risk_free_rate
        sharpe_ratio = (excess_return * 252 / volatility) if volatility > 0 else 0

        # 索提诺比率
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_std = math.sqrt(sum(r**2 for r in downside_returns) / n) * math.sqrt(252)
            sortino_ratio = (excess_return * 252 / downside_std) if downside_std > 0 else 0
        else:
            sortino_ratio = 0

        # Beta
        beta = 0
        if benchmark_returns and len(benchmark_returns) == n:
            bm_mean = sum(benchmark_returns) / n
            covariance = sum((r - mean_return) * (b - bm_mean) for r, b in zip(returns, benchmark_returns, strict=False)) / n
            bm_variance = sum((b - bm_mean) ** 2 for b in benchmark_returns) / n
            beta = covariance / bm_variance if bm_variance > 0 else 0

        # 总敞口（简化）
        total_exposure = portfolio_value * abs(sum(returns)) / n * 20 if returns else 0

        return RiskMetrics(
            total_exposure=total_exposure,
            daily_var=daily_var,
            monthly_var=monthly_var,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            beta=beta,
            volatility=volatility,
        )

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """计算最大回撤"""
        if not returns:
            return 0

        cumulative = [1.0]
        for r in returns:
            cumulative.append(cumulative[-1] * (1 + r))

        peak = cumulative[0]
        max_dd = 0

        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def check_risk_limits(
        self,
        position_value: float,
        portfolio_value: float,
        max_position_pct: float = 0.1,
        max_var_pct: float = 0.05,
    ) -> dict[str, bool]:
        """检查风险限制"""
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0

        return {
            "position_within_limit": position_pct <= max_position_pct,
            "var_within_limit": True,  # 需要 VaR 计算
            "position_pct": position_pct,
        }

    def calculate_margin_requirement(
        self,
        quantity: float,
        price: float,
        margin_rate: float = 0.25,
    ) -> float:
        """计算保证金要求"""
        return quantity * price * margin_rate

    def calculate_leverage(
        self,
        equity: float,
        borrowed: float,
    ) -> float:
        """计算杠杆率"""
        total_assets = equity + borrowed
        return total_assets / equity if equity > 0 else 0
