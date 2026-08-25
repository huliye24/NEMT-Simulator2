"""
Risk Gate
风险闸门 - 所有订单必须通过风险检查
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCK = "BLOCK"


@dataclass
class RiskCheck:
    """风险检查结果"""
    name: str
    level: RiskLevel
    message: str
    passed: bool


@dataclass
class RiskConfig:
    """风险配置"""
    max_position_size: float = 10000.0  # 最大仓位 USDT
    max_position_ratio: float = 0.3  # 最大仓位比例
    daily_loss_limit: float = 500.0  # 日亏损限制
    max_leverage: float = 3.0  # 最大杠杆
    emergency_stop: bool = False  # 紧急停止
    allowed_symbols: List[str] = None  # 允许交易的币种

    def __post_init__(self):
        if self.allowed_symbols is None:
            self.allowed_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]


class RiskGate:
    """风险闸门"""

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now()
        self._emergency_stop = False

    def check_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        current_balance: float,
        current_position: float,
    ) -> Tuple[bool, List[RiskCheck]]:
        """
        检查订单风险

        Returns:
            (是否通过, 检查详情列表)
        """
        checks = []

        # 1. 紧急停止检查
        if self._emergency_stop or self.config.emergency_stop:
            checks.append(RiskCheck(
                name="Emergency Stop",
                level=RiskLevel.BLOCK,
                message="Emergency stop is active",
                passed=False,
            ))
            return False, checks

        # 2. 交易对检查
        if symbol not in self.config.allowed_symbols:
            checks.append(RiskCheck(
                name="Symbol Allowlist",
                level=RiskLevel.BLOCK,
                message=f"Symbol {symbol} not in allowed list",
                passed=False,
            ))
            return False, checks
        else:
            checks.append(RiskCheck(
                name="Symbol Allowlist",
                level=RiskLevel.PASS,
                message=f"Symbol {symbol} approved",
                passed=True,
            ))

        # 3. 仓位大小检查
        order_value = quantity * price
        if order_value > self.config.max_position_size:
            checks.append(RiskCheck(
                name="Max Position Size",
                level=RiskLevel.BLOCK,
                message=f"Order value {order_value:.2f} exceeds max {self.config.max_position_size}",
                passed=False,
            ))
            return False, checks
        else:
            checks.append(RiskCheck(
                name="Max Position Size",
                level=RiskLevel.PASS,
                message=f"Order value {order_value:.2f} within limit",
                passed=True,
            ))

        # 4. 仓位比例检查
        new_position = current_position + order_value
        position_ratio = new_position / current_balance if current_balance > 0 else 1.0

        if position_ratio > self.config.max_position_ratio:
            checks.append(RiskCheck(
                name="Position Ratio",
                level=RiskLevel.BLOCK,
                message=f"Position ratio {position_ratio:.2%} exceeds max {self.config.max_position_ratio:.2%}",
                passed=False,
            ))
            return False, checks
        elif position_ratio > self.config.max_position_ratio * 0.8:
            checks.append(RiskCheck(
                name="Position Ratio",
                level=RiskLevel.WARNING,
                message=f"Position ratio {position_ratio:.2%} approaching limit",
                passed=True,
            ))
        else:
            checks.append(RiskCheck(
                name="Position Ratio",
                level=RiskLevel.PASS,
                message=f"Position ratio {position_ratio:.2%} within limit",
                passed=True,
            ))

        # 5. 日亏损限制检查
        if self.daily_pnl < -self.config.daily_loss_limit:
            checks.append(RiskCheck(
                name="Daily Loss Limit",
                level=RiskLevel.BLOCK,
                message=f"Daily loss {self.daily_pnl:.2f} exceeds limit {self.config.daily_loss_limit}",
                passed=False,
            ))
            return False, checks
        else:
            checks.append(RiskCheck(
                name="Daily Loss Limit",
                level=RiskLevel.PASS,
                message=f"Daily loss {self.daily_pnl:.2f} within limit",
                passed=True,
            ))

        # 全部通过
        return True, checks

    def update_pnl(self, pnl: float):
        """更新盈亏"""
        self.daily_pnl += pnl

    def reset_daily_stats(self):
        """重置日统计"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now()

    def set_emergency_stop(self, enabled: bool):
        """设置紧急停止"""
        self._emergency_stop = enabled
        if enabled:
            print("🚨 EMERGENCY STOP ACTIVATED")
        else:
            print("✅ Emergency stop released")

    def is_emergency_stop(self) -> bool:
        """是否紧急停止"""
        return self._emergency_stop

    def get_status(self) -> Dict:
        """获取风险状态"""
        return {
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "emergency_stop": self._emergency_stop,
            "config": {
                "max_position_size": self.config.max_position_size,
                "max_position_ratio": self.config.max_position_ratio,
                "daily_loss_limit": self.config.daily_loss_limit,
            },
        }
