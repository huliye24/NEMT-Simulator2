"""
NEMT 交易业务约束实现

基于 docs/mirror-mapping/invariants.md 中定义的业务不变式，
实现具体的约束验证逻辑。

约束覆盖:
- INV-M*: 市场数据约束
- INV-S*: 信号生成约束
- INV-R*: 风控约束
- INV-B*: 策略大脑约束
- INV-E*: 执行约束
- INV-MN*: 监控约束
"""

from __future__ import annotations

import logging

from nemt.evolution.constraint.constraint import (
    Constraint,
    ConstraintType,
    ConstraintValidator,
    Severity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 市场数据约束 (INV-M*)
# =============================================================================


class MarketConstraints:
    """市场数据约束"""

    @staticmethod
    def create_cache_consistency() -> Constraint:
        """
        INV-M001: 缓存一致性
        条件: prices.length == volumes.length == timestamps.length
        """
        return Constraint(
            id="inv_m001_cache_consistency",
            name="市场数据缓存一致性",
            description="价格、成交量、时间戳序列必须同步长度",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=lambda x: (len(x.get("prices", [])) == len(x.get("volumes", [])) == len(x.get("timestamps", []))),
        )

    @staticmethod
    def create_time_increasing() -> Constraint:
        """
        INV-M002: 时间递增
        条件: ∀i > 0: timestamps[i] > timestamps[i-1]
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            timestamps = x.get("timestamps", [])
            for i in range(1, len(timestamps)):
                if timestamps[i] <= timestamps[i - 1]:
                    return False, f"时间戳序列在索引 {i} 处不递增"
            return True, None

        return Constraint(
            id="inv_m002_time_increasing",
            name="时间戳递增",
            description="时间戳序列必须严格递增",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_cache_capacity() -> Constraint:
        """
        INV-M003: 缓存容量限制
        条件: len(prices) <= max_size
        """
        return Constraint(
            id="inv_m003_cache_capacity",
            name="缓存容量限制",
            description="价格序列不能超过最大缓存容量",
            type=ConstraintType.BUSINESS,
            severity=Severity.MEDIUM,
            validator=lambda x: len(x.get("prices", [])) <= x.get("max_size", float("inf")),
        )

    @staticmethod
    def create_ohlc_validity() -> Constraint:
        """
        INV-M004: 价格有效性
        条件: high >= close >= low, high >= open >= low
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            required = ["high", "low", "open", "close"]
            if not all(k in x for k in required):
                return True, None  # 允许缺失字段

            h, l, o, c = x["high"], x["low"], x["open"], x["close"]

            if not (h >= c >= l):
                return False, f"High ({h}) >= Close ({c}) >= Low ({l}) 不满足"
            if not (h >= o >= l):
                return False, f"High ({h}) >= Open ({o}) >= Low ({l}) 不满足"

            return True, None

        return Constraint(
            id="inv_m004_ohlc_validity",
            name="K线OHLC有效性",
            description="K线数据的OHLC必须满足 high >= open/close >= low",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @classmethod
    def get_all(cls) -> list[Constraint]:
        """获取所有市场约束"""
        return [
            cls.create_cache_consistency(),
            cls.create_time_increasing(),
            cls.create_cache_capacity(),
            cls.create_ohlc_validity(),
        ]


# =============================================================================
# 信号生成约束 (INV-S*)
# =============================================================================


class SignalConstraints:
    """信号生成约束"""

    @staticmethod
    def create_confidence_range() -> Constraint:
        """
        INV-S001: 置信度范围
        条件: 0 <= confidence <= 1
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            confidence = x.get("confidence")
            if confidence is None:
                return True, None

            if not (0 <= confidence <= 1):
                return False, f"置信度 {confidence} 不在 [0, 1] 范围内"
            return True, None

        return Constraint(
            id="inv_s001_confidence_range",
            name="置信度范围",
            description="置信度必须在 [0, 1] 范围内",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_stop_loss_validity() -> Constraint:
        """
        INV-S002: 止损止盈有效性
        多头: entry_price > stop_loss, take_profit > entry_price
        空头: entry_price < stop_loss, take_profit < entry_price
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            signal_type = x.get("signal_type")
            entry = x.get("entry_price")
            sl = x.get("stop_loss")
            tp = x.get("take_profit")

            if entry is None or sl is None or tp is None:
                return True, None

            if signal_type == "LONG":
                if not (entry > sl):
                    return False, f"多头: 入场价 ({entry}) 必须大于止损 ({sl})"
                if not (tp > entry):
                    return False, f"多头: 止盈 ({tp}) 必须大于入场价 ({entry})"
            elif signal_type == "SHORT":
                if not (entry < sl):
                    return False, f"空头: 入场价 ({entry}) 必须小于止损 ({sl})"
                if not (tp < entry):
                    return False, f"空头: 止盈 ({tp}) 必须小于入场价 ({entry})"

            return True, None

        return Constraint(
            id="inv_s002_stop_loss_validity",
            name="止损止盈有效性",
            description="多头止损必须低于入场，止盈高于入场；空头相反",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_risk_reward_ratio() -> Constraint:
        """
        INV-S003: 风险回报比
        条件: (tp - entry) / (entry - sl) >= 1.5
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            entry = x.get("entry_price")
            sl = x.get("stop_loss")
            tp = x.get("take_profit")
            min_ratio = x.get("min_risk_reward_ratio", 1.5)

            if entry is None or sl is None or tp is None:
                return True, None

            risk = abs(entry - sl)
            reward = abs(tp - entry)

            if risk == 0:
                return False, "风险为零，无法计算风险回报比"

            ratio = reward / risk
            if ratio < min_ratio:
                return False, f"风险回报比 {ratio:.2f} < {min_ratio}"

            return True, None

        return Constraint(
            id="inv_s003_risk_reward_ratio",
            name="风险回报比",
            description="风险回报比必须至少 1:1.5",
            type=ConstraintType.BUSINESS,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @staticmethod
    def create_signal_uniqueness() -> Constraint:
        """
        INV-S004: 信号唯一性
        条件: 同类型信号在同一时刻只能有 1 个有效
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            symbol = x.get("symbol")
            signal_type = x.get("signal_type")
            signals = x.get("active_signals", [])

            if not signals:
                return True, None

            # 检查是否已有同类型信号
            for sig in signals:
                if sig.get("symbol") == symbol and sig.get("type") == signal_type:
                    if sig.get("status") == "ACTIVE":
                        return False, f"已存在活跃的 {signal_type} 信号于 {symbol}"

            return True, None

        return Constraint(
            id="inv_s004_signal_uniqueness",
            name="信号唯一性",
            description="每个交易对同时最多 1 个 LONG 或 1 个 SHORT 信号",
            type=ConstraintType.BUSINESS,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @classmethod
    def get_all(cls) -> list[Constraint]:
        """获取所有信号约束"""
        return [
            cls.create_confidence_range(),
            cls.create_stop_loss_validity(),
            cls.create_risk_reward_ratio(),
            cls.create_signal_uniqueness(),
        ]


# =============================================================================
# 风控约束 (INV-R*)
# =============================================================================


class RiskConstraints:
    """风控约束"""

    @staticmethod
    def create_balance_positive() -> Constraint:
        """
        INV-R001: 账户余额非负
        条件: current_balance >= 0
        """
        return Constraint(
            id="inv_r001_balance_positive",
            name="账户余额非负",
            description="账户余额永远不能为负",
            type=ConstraintType.BUSINESS,
            severity=Severity.CRITICAL,
            validator=lambda x: x.get("current_balance", 0) >= 0,
        )

    @staticmethod
    def create_max_drawdown(max_drawdown: float = 0.2) -> Constraint:
        """
        INV-R002: 回撤上限
        条件: current_balance >= peak_balance * (1 - max_drawdown)
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            current = x.get("current_balance", 0)
            peak = x.get("peak_balance", current)
            max_dd = x.get("max_drawdown", max_drawdown)

            min_balance = peak * (1 - max_dd)
            if current < min_balance:
                return False, f"当前余额 ({current}) 低于回撤限制 ({min_balance:.2f})"
            return True, None

        return Constraint(
            id="inv_r002_max_drawdown",
            name="回撤上限",
            description=f"当前余额不能低于峰值减去{max_drawdown*100}%",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_daily_loss_limit(max_daily_loss: float = 0.05) -> Constraint:
        """
        INV-R003: 日亏损上限
        条件: daily_pnl >= -initial_balance * max_daily_loss
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            daily_pnl = x.get("daily_pnl", 0)
            initial = x.get("initial_balance", 1)
            max_loss = x.get("max_daily_loss", max_daily_loss)

            min_pnl = -initial * max_loss
            if daily_pnl < min_pnl:
                return False, f"日亏损 ({daily_pnl}) 超过限制 ({min_pnl:.2f})"
            return True, None

        return Constraint(
            id="inv_r003_daily_loss_limit",
            name="日亏损上限",
            description="日亏损不能超过初始余额的5%",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_position_limit(max_position: float = 0.3) -> Constraint:
        """
        INV-R004: 仓位上限
        条件: position_size <= current_balance * max_position
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            position = x.get("position_size", 0)
            balance = x.get("current_balance", 1)
            max_pos = x.get("max_position_size", max_position)

            max_position_value = balance * max_pos
            if position > max_position_value:
                return False, f"仓位 ({position}) 超过限制 ({max_position_value:.2f})"
            return True, None

        return Constraint(
            id="inv_r004_position_limit",
            name="仓位上限",
            description=f"仓位不能超过账户余额的{max_position*100}%",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_risk_reject_zero_position() -> Constraint:
        """
        INV-R005: 风控拒绝后无仓位
        条件: approved == False -> position_size == 0
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            approved = x.get("approved", True)
            position = x.get("position_size", 0)

            if not approved and position != 0:
                return False, f"风控拒绝时仓位必须为 0，当前为 {position}"
            return True, None

        return Constraint(
            id="inv_r005_risk_reject_zero_position",
            name="风控拒绝零仓位",
            description="风控拒绝时仓位必须为 0",
            type=ConstraintType.BUSINESS,
            severity=Severity.CRITICAL,
            validator=validator,
        )

    @classmethod
    def get_all(cls, max_drawdown: float = 0.2, max_daily_loss: float = 0.05) -> list[Constraint]:
        """获取所有风控约束"""
        return [
            cls.create_balance_positive(),
            cls.create_max_drawdown(max_drawdown),
            cls.create_daily_loss_limit(max_daily_loss),
            cls.create_position_limit(),
            cls.create_risk_reject_zero_position(),
        ]


# =============================================================================
# 策略大脑约束 (INV-B*)
# =============================================================================


class BrainConstraints:
    """策略大脑约束"""

    @staticmethod
    def create_weights_sum_to_one() -> Constraint:
        """
        INV-B001: 策略权重和为1
        条件: sum(weights) == 1.0
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            weights = x.get("weights", [])
            if not weights:
                return True, None

            total = sum(weights)
            if abs(total - 1.0) > 0.001:
                return False, f"策略权重和 ({total:.4f}) 不等于 1.0"
            return True, None

        return Constraint(
            id="inv_b001_weights_sum_to_one",
            name="策略权重和为1",
            description="所有启用策略的权重和必须等于 1",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_weight_range() -> Constraint:
        """
        INV-B002: 权重范围
        条件: ∀w: 0 <= w <= 1
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            weights = x.get("weights", [])
            for i, w in enumerate(weights):
                if not (0 <= w <= 1):
                    return False, f"策略 {i} 权重 ({w}) 不在 [0, 1] 范围内"
            return True, None

        return Constraint(
            id="inv_b002_weight_range",
            name="权重范围",
            description="单个策略权重必须在 [0, 1] 范围内",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_max_strategies(limit: int = 5) -> Constraint:
        """
        INV-B003: 策略数量上限
        条件: len(strategies) <= limit
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            strategies = x.get("strategies", [])
            max_count = x.get("max_strategy_count", limit)

            if len(strategies) > max_count:
                return False, f"策略数量 ({len(strategies)}) 超过限制 ({max_count})"
            return True, None

        return Constraint(
            id="inv_b003_max_strategies",
            name="策略数量上限",
            description=f"最多同时运行 {limit} 个策略",
            type=ConstraintType.BUSINESS,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @classmethod
    def get_all(cls, max_strategies: int = 5) -> list[Constraint]:
        """获取所有大脑约束"""
        return [
            cls.create_weights_sum_to_one(),
            cls.create_weight_range(),
            cls.create_max_strategies(max_strategies),
        ]


# =============================================================================
# 执行约束 (INV-E*)
# =============================================================================


class ExecutionConstraints:
    """执行约束"""

    @staticmethod
    def create_order_state_transition() -> Constraint:
        """
        INV-E001: 订单状态流转
        条件: 状态只能按允许的顺序流转
        """
        # 合法的状态流转
        VALID_TRANSITIONS = {
            "PENDING": ["SUBMITTED", "CANCELLED", "REJECTED"],
            "SUBMITTED": ["PARTIAL_FILLED", "FILLED", "CANCELLED", "REJECTED"],
            "PARTIAL_FILLED": ["FILLED", "CANCELLED"],
            "FILLED": [],  # 终态
            "CANCELLED": [],  # 终态
            "REJECTED": [],  # 终态
        }

        def validator(x: dict) -> tuple[bool, str | None]:
            old_state = x.get("previous_state")
            new_state = x.get("current_state")

            if old_state is None or new_state is None:
                return True, None

            if old_state not in VALID_TRANSITIONS:
                return False, f"未知的状态: {old_state}"

            if new_state not in VALID_TRANSITIONS[old_state]:
                return False, f"非法状态流转: {old_state} -> {new_state}"

            return True, None

        return Constraint(
            id="inv_e001_order_state_transition",
            name="订单状态流转",
            description="订单状态机必须严格遵守",
            type=ConstraintType.BUSINESS,
            severity=Severity.CRITICAL,
            validator=validator,
        )

    @staticmethod
    def create_filled_quantity_limit() -> Constraint:
        """
        INV-E002: 订单数量一致性
        条件: filled_quantity <= quantity
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            filled = x.get("filled_quantity", 0)
            total = x.get("quantity", filled)

            if filled > total:
                return False, f"已成交数量 ({filled}) 超过委托数量 ({total})"
            return True, None

        return Constraint(
            id="inv_e002_filled_quantity_limit",
            name="成交数量上限",
            description="已成交数量不能超过委托数量",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_balance_deduction() -> Constraint:
        """
        INV-E003: 余额扣减
        买单: Balance -= (filled * price + commission)
        卖单: Balance += (filled * price - commission)
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            old_balance = x.get("previous_balance")
            new_balance = x.get("current_balance")
            filled = x.get("filled_quantity", 0)
            price = x.get("price", 0)
            commission = x.get("commission", 0)
            side = x.get("side", "BUY")

            if old_balance is None or new_balance is None:
                return True, None

            expected_change = filled * price + commission
            if side == "BUY":
                expected_balance = old_balance - expected_change
            else:
                expected_balance = old_balance + expected_change - commission * 2

            if abs(new_balance - expected_balance) > 0.01:
                return False, f"余额变更不正确: 期望 {expected_balance:.2f}, 实际 {new_balance:.2f}"

            return True, None

        return Constraint(
            id="inv_e003_balance_deduction",
            name="余额变更一致性",
            description="余额变化必须与成交精确匹配",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_position_update() -> Constraint:
        """
        INV-E004: 持仓更新
        买入: Position.size += filled_quantity
        卖出: Position.size -= filled_quantity
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            old_size = x.get("previous_position_size", 0)
            new_size = x.get("current_position_size", 0)
            filled = x.get("filled_quantity", 0)
            side = x.get("side", "BUY")

            expected_size = old_size + filled if side == "BUY" else old_size - filled

            if abs(new_size - expected_size) > 0.0001:
                return False, f"持仓变更不正确: 期望 {expected_size:.4f}, 实际 {new_size:.4f}"

            return True, None

        return Constraint(
            id="inv_e004_position_update",
            name="持仓变更一致性",
            description="持仓变化必须与卖出数量精确匹配",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=validator,
        )

    @staticmethod
    def create_zero_position_cleanup() -> Constraint:
        """
        INV-E005: 平仓后无持仓
        条件: size == 0 -> Position 应被删除
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            size = x.get("position_size", 0)
            should_exist = x.get("should_exist", size > 0)

            if size == 0 and should_exist:
                return False, "零持仓的 Position 应被清理"

            return True, None

        return Constraint(
            id="inv_e005_zero_position_cleanup",
            name="零持仓清理",
            description="零持仓的 Position 应被清理",
            type=ConstraintType.BUSINESS,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @classmethod
    def get_all(cls) -> list[Constraint]:
        """获取所有执行约束"""
        return [
            cls.create_order_state_transition(),
            cls.create_filled_quantity_limit(),
            cls.create_balance_deduction(),
            cls.create_position_update(),
            cls.create_zero_position_cleanup(),
        ]


# =============================================================================
# 监控约束 (INV-MN*)
# =============================================================================


class MonitorConstraints:
    """监控约束"""

    @staticmethod
    def create_metric_freshness(max_age_seconds: int = 120) -> Constraint:
        """
        INV-MN001: 健康指标采集时间
        条件: timestamp 必须是过去 max_age_seconds 内
        """
        import time

        def validator(x: dict) -> tuple[bool, str | None]:
            timestamp = x.get("timestamp")
            if timestamp is None:
                return True, None

            # 支持 datetime 或 unix timestamp
            if isinstance(timestamp, (int, float)):
                age = time.time() - timestamp
            else:
                from datetime import datetime

                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                age = (datetime.now() - timestamp).total_seconds()

            max_age = x.get("max_age_seconds", max_age_seconds)
            if age > max_age:
                return False, f"指标过于陈旧: {age:.0f}秒 > {max_age}秒"

            return True, None

        return Constraint(
            id="inv_mn001_metric_freshness",
            name="指标新鲜度",
            description="健康指标不能过于陈旧",
            type=ConstraintType.SYSTEM,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @staticmethod
    def create_alert_history_limit(limit: int = 100) -> Constraint:
        """
        INV-MN002: 告警历史上限
        条件: len(alert_history) <= limit
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            history = x.get("alert_history", [])
            max_count = x.get("max_history_size", limit)

            if len(history) > max_count:
                return False, f"告警历史 ({len(history)}) 超过限制 ({max_count})"
            return True, None

        return Constraint(
            id="inv_mn002_alert_history_limit",
            name="告警历史限制",
            description=f"告警历史最多保留 {limit} 条",
            type=ConstraintType.SYSTEM,
            severity=Severity.LOW,
            validator=validator,
        )

    @staticmethod
    def create_positive_threshold() -> Constraint:
        """
        INV-MN003: 阈值必须为正
        条件: thresholds[key] > 0
        """

        def validator(x: dict) -> tuple[bool, str | None]:
            thresholds = x.get("alert_thresholds", {})

            for key, value in thresholds.items():
                if value <= 0:
                    return False, f"告警阈值 {key} ({value}) 必须为正数"
            return True, None

        return Constraint(
            id="inv_mn003_positive_threshold",
            name="阈值正数",
            description="所有告警阈值必须为正数",
            type=ConstraintType.SYSTEM,
            severity=Severity.MEDIUM,
            validator=validator,
        )

    @classmethod
    def get_all(cls, max_history: int = 100) -> list[Constraint]:
        """获取所有监控约束"""
        return [
            cls.create_metric_freshness(),
            cls.create_alert_history_limit(max_history),
            cls.create_positive_threshold(),
        ]


# =============================================================================
# 约束注册器
# =============================================================================


class ConstraintRegistry:
    """约束注册器 - 统一管理所有业务约束"""

    def __init__(self):
        self._validator = ConstraintValidator()
        self._constraints_by_category = {
            "market": MarketConstraints.get_all(),
            "signal": SignalConstraints.get_all(),
            "risk": RiskConstraints.get_all(),
            "brain": BrainConstraints.get_all(),
            "execution": ExecutionConstraints.get_all(),
            "monitor": MonitorConstraints.get_all(),
        }

        # 注册所有约束
        self._register_all()

    def _register_all(self):
        """注册所有约束"""
        for category, constraints in self._constraints_by_category.items():
            for constraint in constraints:
                self._validator.add_constraint(constraint)
                logger.debug(f"Registered {category} constraint: {constraint.id}")

    def get_validator(self) -> ConstraintValidator:
        """获取验证器"""
        return self._validator

    def validate_category(self, category: str, data: dict) -> ConstraintResult:
        """验证指定类别"""
        constraints = self._constraints_by_category.get(category, [])
        constraint_ids = [c.id for c in constraints]
        return self._validator.validate(data, constraint_ids=constraint_ids)

    def validate_all(self, data: dict, categories: list[str] | None = None) -> ConstraintResult:
        """验证所有或指定类别"""
        if categories:
            constraint_ids = []
            for cat in categories:
                constraint_ids.extend([c.id for c in self._constraints_by_category.get(cat, [])])
            return self._validator.validate(data, constraint_ids=constraint_ids)
        return self._validator.validate(data)

    def get_constraints_summary(self) -> dict[str, list[str]]:
        """获取约束摘要"""
        return {
            category: [c.id for c in constraints] for category, constraints in self._constraints_by_category.items()
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "MarketConstraints",
    "SignalConstraints",
    "RiskConstraints",
    "BrainConstraints",
    "ExecutionConstraints",
    "MonitorConstraints",
    "ConstraintRegistry",
]
