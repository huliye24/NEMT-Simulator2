"""
NEMT 风控层 (Risk Layer)
系统最高优先级保障，保护资金安全
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class RiskMode(Enum):
    """风险模式"""
    NORMAL = "NORMAL"           # 正常运行
    CAUTION = "CAUTION"         # 谨慎模式
    DEFENSE = "DEFENSE"         # 防御模式
    SHUTDOWN = "SHUTDOWN"       # 关机模式


class RiskAction(Enum):
    """风险动作"""
    ALLOW = "ALLOW"             # 允许
    REDUCE = "REDUCE"           # 减少仓位
    REJECT = "REJECT"           # 拒绝
    SHUTDOWN = "SHUTDOWN"       # 关闭所有仓位
    DEFENSE = "DEFENSE"         # 防御模式


@dataclass
class RiskRule:
    """风控规则"""
    name: str
    rule_type: str              # hard, soft, preventive
    threshold: float             # 阈值
    action: RiskAction           # 触发动作
    enabled: bool = True
    last_triggered: Optional[datetime] = None

    def trigger(self) -> bool:
        self.last_triggered = datetime.now()
        return True


@dataclass
class RiskMetrics:
    """风控指标"""
    current_drawdown: float = 0.0     # 当前回撤
    max_drawdown: float = 0.0         # 历史最大回撤
    daily_pnl: float = 0.0           # 当日盈亏
    daily_loss: float = 0.0          # 当日亏损
    equity_peak: float = 0.0          # 权益峰值
    current_equity: float = 0.0      # 当前权益
    exposure: float = 0.0             # 风险敞口

    def update(self, equity: float, daily_pnl: float):
        """更新指标"""
        self.current_equity = equity

        # Update equity peak - only track the high water mark
        if equity > self.equity_peak:
            self.equity_peak = equity

        # Calculate current drawdown from peak
        # This represents how much we've given back from our high
        if self.equity_peak > 0:
            self.current_drawdown = (self.equity_peak - equity) / self.equity_peak * 100

        # Update max drawdown - tracks the worst drawdown from peak
        if self.current_drawdown > self.max_drawdown:
            self.max_drawdown = self.current_drawdown

        # Update daily metrics
        self.daily_pnl = daily_pnl
        if daily_pnl < 0:
            self.daily_loss = abs(daily_pnl)


class RiskLayer:
    """
    风控层

    核心功能：
    1. 规则引擎
    2. 风险模式切换
    3. 仓位检查
    4. 紧急止损
    """

    def __init__(
        self,
        max_drawdown_pct: float = 20.0,
        daily_loss_limit_pct: float = 5.0,
        strategy_exposure_cap: float = 40.0,
        market_exposure_cap: float = 60.0,
        caution_threshold: float = 5.0,
        defense_threshold: float = 10.0,
        shutdown_threshold: float = 15.0
    ):
        # 阈值配置
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.strategy_exposure_cap = strategy_exposure_cap
        self.market_exposure_cap = market_exposure_cap

        # 状态阈值
        self.caution_threshold = caution_threshold
        self.defense_threshold = defense_threshold
        self.shutdown_threshold = shutdown_threshold

        # 状态
        self.current_mode: RiskMode = RiskMode.NORMAL
        self.initial_capital: float = 0.0

        # 规则
        self.rules: Dict[str, RiskRule] = self._init_rules()

        # 指标
        self.metrics = RiskMetrics()

        # 仓位限制
        self.position_multiplier: float = 1.0  # 仓位倍数

        # 统计数据
        self.equity_history: List[float] = []
        self.daily_closes: List[Tuple[datetime, float]] = []

    def _init_rules(self) -> Dict[str, RiskRule]:
        """初始化风控规则"""
        return {
            'max_drawdown': RiskRule(
                name='最大回撤限制',
                rule_type='hard',
                threshold=self.max_drawdown_pct,
                action=RiskAction.SHUTDOWN
            ),
            'daily_loss': RiskRule(
                name='日亏损限制',
                rule_type='hard',
                threshold=self.daily_loss_limit_pct,
                action=RiskAction.DEFENSE
            ),
            'strategy_exposure': RiskRule(
                name='单策略仓位上限',
                rule_type='soft',
                threshold=self.strategy_exposure_cap,
                action=RiskAction.REDUCE
            ),
            'market_exposure': RiskRule(
                name='单市场仓位上限',
                rule_type='soft',
                threshold=self.market_exposure_cap,
                action=RiskAction.REDUCE
            )
        }

    def set_initial_capital(self, capital: float):
        """设置初始资金"""
        self.initial_capital = capital
        # Don't set equity_peak to initial capital immediately
        # Let it update naturally through update_equity
        self.metrics.equity_peak = capital

    def update_equity(self, equity: float, timestamp: datetime = None):
        """更新权益"""
        self.metrics.update(equity, self.metrics.daily_pnl)
        self.equity_history.append(equity)

        # 检查风控状态
        self._check_risk_mode()

    def update_daily_pnl(self, daily_pnl: float, timestamp: datetime = None):
        """更新日盈亏"""
        self.metrics.daily_pnl = daily_pnl
        if daily_pnl < 0:
            self.metrics.daily_loss = abs(daily_pnl)

        # 检查日亏损规则
        self._check_daily_loss_rule()

    def _check_risk_mode(self):
        """检查并更新风险模式"""
        new_mode = self.current_mode

        if self.metrics.current_drawdown >= self.shutdown_threshold:
            new_mode = RiskMode.SHUTDOWN
        elif self.metrics.current_drawdown >= self.defense_threshold:
            new_mode = RiskMode.DEFENSE
        elif self.metrics.current_drawdown >= self.caution_threshold:
            new_mode = RiskMode.CAUTION
        else:
            new_mode = RiskMode.NORMAL

        if new_mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = new_mode
            self._on_mode_change(old_mode, new_mode)

    def _on_mode_change(self, old_mode: RiskMode, new_mode: RiskMode):
        """模式切换回调"""
        print(f"\n[WARNING] Risk mode changed: {old_mode.value} -> {new_mode.value}")
        print(f"   Current drawdown: {self.metrics.current_drawdown:.2f}%")

        # Adjust position multiplier based on mode
        if new_mode == RiskMode.CAUTION:
            self.position_multiplier = 0.5
            print(f"   Position reduced to 50%")
        elif new_mode == RiskMode.DEFENSE:
            self.position_multiplier = 0.2
            print(f"   Position reduced to 20%")
        elif new_mode == RiskMode.SHUTDOWN:
            self.position_multiplier = 0.0
            print(f"   Position: 0% - No new positions allowed!")

    def _check_daily_loss_rule(self):
        """检查日亏损规则"""
        if self.initial_capital <= 0:
            return

        daily_loss_pct = self.metrics.daily_loss / self.initial_capital * 100

        if daily_loss_pct >= self.daily_loss_limit_pct:
            rule = self.rules['daily_loss']
            rule.trigger()
            print(f"\n[CRITICAL] Daily loss limit exceeded: {daily_loss_pct:.2f}% > {self.daily_loss_limit_pct}%")

            if rule.action == RiskAction.DEFENSE:
                self.current_mode = RiskMode.DEFENSE
                self.position_multiplier = 0.2

    def check_order(
        self,
        proposed_position: float,
        strategy_name: str,
        symbol: str = "DEFAULT"
    ) -> Tuple[bool, str]:
        """
        订单提交前风控检查

        Args:
            proposed_position: 建议仓位
            strategy_name: 策略名称
            symbol: 交易品种

        Returns:
            (approved, reason)
        """
        # 关机模式禁止开仓
        if self.current_mode == RiskMode.SHUTDOWN:
            return False, "风控关机中，禁止开仓"

        # 检查最大回撤
        if self.metrics.current_drawdown >= self.max_drawdown_pct:
            return False, f"超过最大回撤限制 {self.max_drawdown_pct}%"

        # 检查日亏损
        if self.initial_capital > 0:
            daily_loss_pct = self.metrics.daily_loss / self.initial_capital * 100
            if daily_loss_pct >= self.daily_loss_limit_pct:
                return False, f"超过日亏损限制 {self.daily_loss_limit_pct}%"

        # 检查仓位比例
        if proposed_position > self.position_multiplier:
            return False, f"风控限制仓位倍数 {self.position_multiplier}"

        return True, "风控检查通过"

    def calculate_position_size(
        self,
        signal_strength: float,
        strategy_weight: float,
        total_capital: float,
        atr: float = 0.0,
        risk_per_trade: float = 0.02
    ) -> float:
        """
        计算仓位大小

        Args:
            signal_strength: 信号强度 (0-100)
            strategy_weight: 策略权重
            total_capital: 总资金
            atr: ATR值
            risk_per_trade: 每笔交易风险比例

        Returns:
            建议仓位大小 (金额)
        """
        # 基础仓位
        base_position = total_capital * risk_per_trade

        # 乘以信号强度
        signal_factor = signal_strength / 100

        # 乘以策略权重
        weight_factor = strategy_weight / 100

        # 乘以风控仓位倍数
        position = base_position * signal_factor * weight_factor * self.position_multiplier

        # 如果有ATR，进行波动率调整
        if atr > 0 and total_capital > 0:
            price = total_capital * 0.1  # 简化：假设持仓约为资金的10%
            atr_ratio = price * 0.01 / atr if atr > 0 else 1  # 1%风险的ATR单位

            # 波动率调整
            if atr_ratio < 1:
                position *= atr_ratio
            elif atr_ratio > 3:
                position *= 1.5

        return max(0, position)

    def get_position_multiplier(self) -> float:
        """获取仓位倍数"""
        return self.position_multiplier

    def get_risk_mode(self) -> RiskMode:
        """获取当前风险模式"""
        return self.current_mode

    def get_metrics(self) -> RiskMetrics:
        """获取风控指标"""
        return self.metrics

    def should_close_all(self) -> bool:
        """是否应该关闭所有仓位"""
        return self.current_mode == RiskMode.SHUTDOWN

    def should_reduce_position(self) -> bool:
        """是否应该减少仓位"""
        return self.current_mode in [RiskMode.CAUTION, RiskMode.DEFENSE]

    def get_risk_report(self) -> Dict:
        """获取风控报告"""
        return {
            'risk_mode': self.current_mode.value,
            'position_multiplier': self.position_multiplier,
            'current_drawdown': self.metrics.current_drawdown,
            'max_drawdown': self.metrics.max_drawdown,
            'daily_pnl': self.metrics.daily_pnl,
            'daily_loss': self.metrics.daily_loss,
            'equity': self.metrics.current_equity,
            'equity_peak': self.metrics.equity_peak,
            'rules_triggered': [
                {
                    'name': r.name,
                    'last_triggered': r.last_triggered
                }
                for r in self.rules.values() if r.last_triggered is not None
            ]
        }

    def reset(self):
        """重置风控层"""
        self.current_mode = RiskMode.NORMAL
        self.position_multiplier = 1.0
        self.metrics = RiskMetrics()
        self.equity_history = []
        self.daily_closes = []

        # 重置规则
        for rule in self.rules.values():
            rule.last_triggered = None


class RiskController:
    """风控控制器 - 更高层次的封装"""

    def __init__(self, risk_layer: RiskLayer, execution_layer):
        self.risk_layer = risk_layer
        self.execution = execution_layer

    def pre_trade_check(
        self,
        signal: float,
        strategy_weight: float,
        strategy_name: str
    ) -> Tuple[bool, str, float]:
        """
        交易前检查

        Returns:
            (approved, reason, adjusted_signal)
        """
        # 风控检查
        approved, reason = self.risk_layer.check_order(
            proposed_position=abs(signal),
            strategy_name=strategy_name
        )

        if not approved:
            return False, reason, 0.0

        # 根据风险模式调整信号
        multiplier = self.risk_layer.get_position_multiplier()
        adjusted_signal = signal * multiplier

        return True, "通过", adjusted_signal

    def post_trade_update(self, current_equity: float):
        """交易后更新风控状态"""
        self.risk_layer.update_equity(current_equity)
