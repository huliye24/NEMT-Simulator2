"""
Risk Domain Models - 风控领域模型

定义风控上下文中所有业务实体：
- RiskCheckResult: 风控检查结果聚合根
- Position: 持仓实体
- RiskRule: 风控规则值对象

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    """风险等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskRuleType(Enum):
    """风控规则类型"""

    BALANCE = "balance"  # 余额检查
    DRAWDOWN = "drawdown"  # 回撤检查
    POSITION_SIZE = "position_size"  # 仓位检查
    EXPOSURE = "exposure"  # 暴露率检查
    RISK_REWARD = "risk_reward"  # 风险回报检查
    COOLDOWN = "cooldown"  # 冷却期检查


@dataclass
class RiskRule:
    """
    风控规则值对象

    定义风控检查的具体规则。
    值对象：无唯一标识，不可变。

    INVARIANTS:
    - threshold > 0
    """

    rule_id: str
    name: str
    rule_type: RiskRuleType
    threshold: float
    enabled: bool = True
    severity: RiskLevel = RiskLevel.MEDIUM
    message: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "rule_type": self.rule_type.value,
            "threshold": self.threshold,
            "enabled": self.enabled,
            "severity": self.severity.value,
            "message": self.message,
            "params": self.params,
        }


@dataclass
class Position:
    """
    持仓实体

    表示当前持有的仓位。
    实体：有唯一标识 (symbol)，生命周期内可变。

    INVARIANTS:
    - size >= 0
    - entry >= 0
    """

    symbol: str
    side: str  # "long" or "short"
    size: float
    entry: float  # 开仓均价

    # 盈亏计算
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    # 时间戳
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 元数据
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.size < 0:
            raise ValueError("size must be non-negative")
        if self.entry < 0:
            raise ValueError("entry must be non-negative")

    def update_pnl(self, current_price: float) -> None:
        """
        更新浮动盈亏

        Args:
            current_price: 当前市场价格
        """
        if self.side == "long":
            self.unrealized_pnl = (current_price - self.entry) * self.size
        else:
            self.unrealized_pnl = (self.entry - current_price) * self.size
        self.updated_at = datetime.now()
        self.version += 1

    def update_size(self, delta: float) -> None:
        """
        更新持仓数量

        Args:
            delta: 变化量 (正数为增加，负数为减少)
        """
        new_size = self.size + delta
        if new_size < 0:
            raise ValueError("size cannot be negative")
        self.size = new_size
        self.updated_at = datetime.now()
        self.version += 1

    def close(self, exit_price: float) -> float:
        """
        平仓

        Args:
            exit_price: 平仓价格

        Returns:
            平仓盈亏
        """
        if self.side == "long":
            pnl = (exit_price - self.entry) * self.size
        else:
            pnl = (self.entry - exit_price) * self.size

        self.realized_pnl += pnl
        self.size = 0.0
        self.updated_at = datetime.now()
        self.version += 1
        return pnl

    @property
    def notional_value(self) -> float:
        """持仓名义价值"""
        return self.size * self.entry

    @property
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.unrealized_pnl > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "entry": self.entry,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "opened_at": self.opened_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Position:
        opened = data.get("opened_at")
        if isinstance(opened, str):
            opened = datetime.fromisoformat(opened)
        elif opened is None:
            opened = datetime.now()

        updated = data.get("updated_at")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif updated is None:
            updated = datetime.now()

        return cls(
            symbol=data.get("symbol", ""),
            side=data.get("side", "long"),
            size=float(data.get("size", 0)),
            entry=float(data.get("entry", 0)),
            unrealized_pnl=float(data.get("unrealized_pnl", 0)),
            realized_pnl=float(data.get("realized_pnl", 0)),
            opened_at=opened,
            updated_at=updated,
            version=int(data.get("version", 1)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RiskCheckResult:
    """
    风控检查结果聚合根

    表示风控检查的最终结果，决定信号是否允许执行。
    聚合根：外部只能通过此类访问风控结果。

    INVARIANTS:
    - approved=False 时 position_size=0
    """

    approved: bool
    signal_id: str
    symbol: str

    # 调整后的参数
    position_size: float = 0.0
    adjusted_entry: float = 0.0
    adjusted_stop_loss: float = 0.0
    adjusted_take_profit: float = 0.0

    # 决策信息
    reasons: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW

    # 风控规则详情
    applied_rules: list[RiskRule] = field(default_factory=list)

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    version: int = 1
    result_id: str = field(default_factory="")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"risk_{uuid.uuid4()[:8]}"

        # 如果不批准，仓位必须为0
        if not self.approved and self.position_size > 0:
            raise ValueError("position_size must be 0 when not approved")

    @property
    def is_approved(self) -> bool:
        """是否批准"""
        return self.approved

    @property
    def rejection_reasons(self) -> list[str]:
        """获取拒绝原因"""
        if self.approved:
            return []
        return self.reasons

    def add_reason(self, reason: str) -> None:
        """添加原因"""
        self.reasons.append(reason)

    def add_rule(self, rule: RiskRule) -> None:
        """添加应用的规则"""
        self.applied_rules.append(rule)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "approved": self.approved,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "position_size": self.position_size,
            "adjusted_entry": self.adjusted_entry,
            "adjusted_stop_loss": self.adjusted_stop_loss,
            "adjusted_take_profit": self.adjusted_take_profit,
            "reasons": self.reasons,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "applied_rules": [r.to_dict() for r in self.applied_rules],
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskCheckResult:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()

        risk_level = data.get("risk_level", "low")
        if isinstance(risk_level, str):
            risk_level = RiskLevel(risk_level)

        return cls(
            result_id=data.get("result_id", ""),
            approved=data.get("approved", False),
            signal_id=data.get("signal_id", ""),
            symbol=data.get("symbol", ""),
            position_size=float(data.get("position_size", 0)),
            adjusted_entry=float(data.get("adjusted_entry", 0)),
            adjusted_stop_loss=float(data.get("adjusted_stop_loss", 0)),
            adjusted_take_profit=float(data.get("adjusted_take_profit", 0)),
            reasons=data.get("reasons", []),
            risk_score=float(data.get("risk_score", 0)),
            risk_level=risk_level,
            timestamp=ts,
            version=int(data.get("version", 1)),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# Factory Methods
# =============================================================================


def create_approved_result(
    signal_id: str,
    symbol: str,
    position_size: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    reasons: list[str] | None = None,
    risk_score: float = 0.0,
) -> RiskCheckResult:
    """
    工厂方法：创建批准结果

    Args:
        signal_id: 信号ID
        symbol: 交易对
        position_size: 仓位大小
        entry_price: 入场价格
        stop_loss: 止损价格
        take_profit: 止盈价格
        reasons: 通过原因
        risk_score: 风险评分

    Returns:
        RiskCheckResult 实例
    """
    return RiskCheckResult(
        approved=True,
        signal_id=signal_id,
        symbol=symbol,
        position_size=position_size,
        adjusted_entry=entry_price,
        adjusted_stop_loss=stop_loss,
        adjusted_take_profit=take_profit,
        reasons=reasons or [],
        risk_score=risk_score,
    )


def create_rejected_result(
    signal_id: str,
    symbol: str,
    reason: str,
    risk_score: float = 1.0,
) -> RiskCheckResult:
    """
    工厂方法：创建拒绝结果

    Args:
        signal_id: 信号ID
        symbol: 交易对
        reason: 拒绝原因
        risk_score: 风险评分

    Returns:
        RiskCheckResult 实例
    """
    return RiskCheckResult(
        approved=False,
        signal_id=signal_id,
        symbol=symbol,
        position_size=0.0,
        adjusted_entry=0.0,
        adjusted_stop_loss=0.0,
        adjusted_take_profit=0.0,
        reasons=[reason],
        risk_score=risk_score,
        risk_level=RiskLevel.HIGH,
    )


def create_position(
    symbol: str,
    side: str,
    size: float,
    entry: float,
) -> Position:
    """
    工厂方法：创建持仓

    Args:
        symbol: 交易对
        side: 方向 ("long" or "short")
        size: 数量
        entry: 开仓价

    Returns:
        Position 实例
    """
    return Position(
        symbol=symbol,
        side=side,
        size=size,
        entry=entry,
    )


# =============================================================================
# Domain Services
# =============================================================================


def calculate_position_size(
    balance: float,
    entry_price: float,
    risk_percent: float,
    stop_loss_percent: float,
) -> float:
    """
    计算仓位大小

    Args:
        balance: 账户余额
        entry_price: 入场价格
        risk_percent: 风险比例 (如 0.01 = 1%)
        stop_loss_percent: 止损比例 (如 0.02 = 2%)

    Returns:
        仓位大小
    """
    risk_amount = balance * risk_percent
    price_risk = entry_price * stop_loss_percent
    if price_risk == 0:
        return 0.0
    return risk_amount / price_risk


def calculate_risk_score(
    drawdown: float,
    exposure: float,
    position_count: int,
    max_drawdown: float = 0.2,
    max_exposure: float = 0.8,
    max_positions: int = 5,
) -> float:
    """
    计算综合风险评分

    Args:
        drawdown: 当前回撤
        exposure: 当前暴露率
        position_count: 持仓数量
        max_drawdown: 最大回撤
        max_exposure: 最大暴露率
        max_positions: 最大持仓数

    Returns:
        风险评分 [0, 1]
    """
    # 各维度归一化
    drawdown_score = min(drawdown / max_drawdown, 1.0) if max_drawdown > 0 else 0
    exposure_score = min(exposure / max_exposure, 1.0) if max_exposure > 0 else 0
    position_score = min(position_count / max_positions, 1.0) if max_positions > 0 else 0

    # 加权平均
    return drawdown_score * 0.4 + exposure_score * 0.4 + position_score * 0.2


def determine_risk_level(risk_score: float) -> RiskLevel:
    """
    根据风险评分确定风险等级

    Args:
        risk_score: 风险评分 [0, 1]

    Returns:
        风险等级
    """
    if risk_score < 0.3:
        return RiskLevel.LOW
    elif risk_score < 0.6:
        return RiskLevel.MEDIUM
    elif risk_score < 0.8:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL
