"""
PositionCapsule - 仓位管理胶囊

提供智能仓位管理功能:
- 动态风险等级计算
- 多种仓位算法支持
- 实时仓位监控
- 历史仓位记录
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event
from nemt.core.position_calculator import (
    AlgoMode,
    PositionCalculator,
    PositionResult,
    RiskTier,
)

__all__ = ["PositionCapsule", "PositionOrder", "PositionHistory"]


@dataclass
class PositionOrder:
    """
    仓位订单

    Attributes:
        order_id: 订单ID
        symbol: 交易品种
        side: 方向 (long/short)
        position_value: 仓位金额
        position_pct: 仓位百分比
        entry_price: 入场价格
        current_price: 当前价格
        unrealized_pnl: 未实现盈亏
        unrealized_pnl_pct: 未实现盈亏百分比
        stop_loss: 止损价格
        take_profit: 止盈价格
        risk_amount: 风险金额
        confidence: 信心度
        timestamp: 创建时间
        status: 状态 (pending/active/closed)
    """

    order_id: str
    symbol: str
    side: str
    position_value: float
    position_pct: float
    entry_price: float
    current_price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_amount: float = 0.0
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"

    @property
    def unrealized_pnl(self) -> float:
        """计算未实现盈亏"""
        if self.side == "long":
            return (self.current_price - self.entry_price) * self.position_value / self.entry_price
        else:
            return (self.entry_price - self.current_price) * self.position_value / self.entry_price

    @property
    def unrealized_pnl_pct(self) -> float:
        """计算未实现盈亏百分比"""
        if self.position_value == 0:
            return 0.0
        return self.unrealized_pnl / self.position_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "position_value": self.position_value,
            "position_pct": self.position_pct,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_amount": self.risk_amount,
            "confidence": self.confidence,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "timestamp": self.timestamp,
            "status": self.status,
        }


@dataclass
class PositionHistory:
    """
    仓位历史记录

    Attributes:
        history_id: 记录ID
        symbol: 交易品种
        side: 方向
        position_pct: 仓位百分比
        entry_price: 入场价格
        exit_price: 出场价格
        pnl: 盈亏
        pnl_pct: 盈亏百分比
        risk_amount: 风险金额
        exit_reason: 出场原因 (stop_loss/take_profit/manual)
        exit_time: 出场时间
        holding_period: 持仓时长(秒)
        algo_mode: 算法模式
    """

    history_id: str
    symbol: str
    side: str
    position_pct: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    risk_amount: float
    exit_reason: str
    exit_time: float
    holding_period: float
    algo_mode: str
    risk_tier: str


class PositionCapsule(ModuleCapsule):
    """
    仓位管理胶囊

    订阅事件:
    - market.bar: K线数据 (更新当前价格)
    - nemt.signal: 交易信号 (计算仓位)
    - account.equity_update: 资金更新

    发布事件:
    - position.calculated: 仓位计算完成
    - position.recommended: 推荐仓位
    - position.order_created: 订单创建
    - position.order_closed: 订单关闭
    - position.risk_warning: 风险警告
    - position.tier_changed: 风险等级变化
    """

    def __init__(
        self,
        initial_equity: float = 10000.0,
        default_algo_mode: AlgoMode = AlgoMode.SIMPLE,
    ):
        """
        初始化仓位管理胶囊

        Args:
            initial_equity: 初始权益
            default_algo_mode: 默认算法模式
        """
        super().__init__("position")

        # 核心组件
        self._calculator = PositionCalculator(algo_mode=default_algo_mode)
        self._logger = logging.getLogger("PositionCapsule")

        # 账户状态
        self._equity = initial_equity
        self._initial_equity = initial_equity
        self._available_margin = initial_equity

        # 持仓管理
        self._orders: Dict[str, PositionOrder] = {}
        self._history: List[PositionHistory] = []
        self._max_history = 100

        # 风险状态
        self._current_tier = self._calculator._dynamic_calc.get_risk_tier(initial_equity)
        self._daily_loss = 0.0
        self._max_drawdown = 0.0

        # 当前信号
        self._current_signal: Optional[Dict[str, Any]] = None

        # 事件回调
        self._on_position_calculated: Optional[Callable] = None
        self._on_risk_warning: Optional[Callable] = None

        # 统计
        self._calc_count = 0
        self._order_count = 0
        self._win_count = 0
        self._loss_count = 0

    # ========================================================================
    # ICapsule 接口实现
    # ========================================================================

    def init(self) -> None:
        """初始化胶囊"""
        self._logger.info("PositionCapsule 初始化中...")

        # 订阅事件
        self.subscribe("market.bar", self._on_market_bar)
        self.subscribe("nemt.signal", self._on_signal)
        self.subscribe("account.equity_update", self._on_equity_update)

        self._logger.info(f"PositionCapsule 初始化完成，初始权益: {self._equity}")

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回仓位状态

        Returns:
            仓位状态字典
        """
        return {
            "equity": self._equity,
            "position_value": self.total_position_value,
            "position_pct": self.position_pct,
            "available_margin": self._available_margin,
            "risk_tier": self._current_tier.value,
            "open_orders": len(self._orders),
            "calc_count": self._calc_count,
        }

    def shutdown(self) -> None:
        """关闭胶囊"""
        self.unsubscribe("market.bar", self._on_market_bar)
        self.unsubscribe("nemt.signal", self._on_signal)
        self.unsubscribe("account.equity_update", self._on_equity_update)
        self._logger.info("PositionCapsule 已关闭")

    # ========================================================================
    # 核心方法
    # ========================================================================

    def calculate_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss_pct: float = 0.02,
        signal_confidence: float = 1.0,
        atr: float = 0.0,
        historical_win_rate: float = 0.55,
        reward_ratio: float = 1.5,
    ) -> PositionResult:
        """
        计算推荐仓位

        Args:
            symbol: 交易品种
            side: 方向 (long/short)
            entry_price: 入场价格
            stop_loss_pct: 止损百分比
            signal_confidence: 信号信心度
            atr: ATR 值 (hybrid 模式需要)
            historical_win_rate: 历史胜率
            reward_ratio: 盈亏比

        Returns:
            PositionResult 仓位计算结果
        """
        self._calc_count += 1

        # 计算仓位
        result = self._calculator.calculate(
            equity=self._equity,
            entry_price=entry_price,
            stop_loss_pct=stop_loss_pct,
            signal_confidence=signal_confidence,
            atr=atr,
            historical_win_rate=historical_win_rate,
            reward_ratio=reward_ratio,
        )

        # 发布事件
        self.publish(
            "position.calculated",
            {
                "symbol": symbol,
                "side": side,
                "result": result.to_dict(),
                "timestamp": time.time(),
            },
        )

        return result

    def create_order(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        position_value: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        confidence: float = 1.0,
    ) -> PositionOrder:
        """
        创建仓位订单

        Args:
            symbol: 交易品种
            side: 方向
            entry_price: 入场价格
            position_value: 仓位金额
            stop_loss: 止损价格
            take_profit: 止盈价格
            confidence: 信心度

        Returns:
            PositionOrder 订单
        """
        self._order_count += 1

        # 计算仓位百分比
        position_pct = position_value / self._equity if self._equity > 0 else 0

        # 计算风险金额
        if stop_loss > 0 and entry_price > 0:
            if side == "long":
                risk_per_unit = entry_price - stop_loss
            else:
                risk_per_unit = stop_loss - entry_price
            risk_amount = risk_per_unit * position_value / entry_price
        else:
            risk_amount = position_value * 0.02  # 默认2%风险

        # 创建订单
        order = PositionOrder(
            order_id=f"POS_{self._order_count:06d}_{symbol}_{int(time.time())}",
            symbol=symbol,
            side=side,
            position_value=position_value,
            position_pct=position_pct,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            confidence=confidence,
            status="active",
        )

        # 更新状态
        self._orders[order.order_id] = order
        self._equity -= position_value  # 占用保证金
        self._available_margin = self._equity - sum(o.position_value for o in self._orders.values())

        # 检查风险
        self._check_risk_limits(order)

        # 发布事件
        self.publish(
            "position.order_created",
            {
                "order": order.to_dict(),
                "equity_after": self._equity,
                "position_pct_after": self.total_position_pct,
            },
        )

        self._logger.info(
            f"创建仓位订单: {order.order_id}, {side} {symbol}, "
            f"仓位: {position_value:.2f} ({position_pct:.1%})"
        )

        return order

    def close_order(
        self,
        order_id: str,
        exit_price: float,
        exit_reason: str = "manual",
    ) -> PositionHistory:
        """
        关闭仓位订单

        Args:
            order_id: 订单ID
            exit_price: 出场价格
            exit_reason: 出场原因

        Returns:
            PositionHistory 历史记录
        """
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")

        order = self._orders[order_id]

        # 计算盈亏
        if order.side == "long":
            pnl = (exit_price - order.entry_price) * order.position_value / order.entry_price
        else:
            pnl = (order.entry_price - exit_price) * order.position_value / order.entry_price

        pnl_pct = pnl / order.position_value if order.position_value > 0 else 0

        # 更新统计
        if pnl > 0:
            self._win_count += 1
        else:
            self._loss_count += 1

        # 更新权益
        self._equity += order.position_value + pnl
        self._available_margin = self._equity

        # 创建历史记录
        holding_period = time.time() - order.timestamp

        history = PositionHistory(
            history_id=f"HIST_{order_id}",
            symbol=order.symbol,
            side=order.side,
            position_pct=order.position_pct,
            entry_price=order.entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            risk_amount=order.risk_amount,
            exit_reason=exit_reason,
            exit_time=time.time(),
            holding_period=holding_period,
            algo_mode=self._calculator.get_algo_mode().value,
            risk_tier=self._current_tier.value,
        )

        self._history.append(history)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # 删除订单
        del self._orders[order_id]

        # 更新风险状态
        if pnl < 0:
            self._daily_loss += abs(pnl)
        self._update_max_drawdown()

        # 发布事件
        self.publish(
            "position.order_closed",
            {
                "order_id": order_id,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": exit_reason,
                "equity_after": self._equity,
            },
        )

        self._logger.info(
            f"关闭仓位订单: {order_id}, 盈亏: {pnl:.2f} ({pnl_pct:.2%}), "
            f"出场原因: {exit_reason}"
        )

        return history

    def adjust_position(
        self,
        order_id: str,
        target_pct: float,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        调整仓位

        Args:
            order_id: 订单ID
            target_pct: 目标仓位百分比
            current_price: 当前价格

        Returns:
            调整结果
        """
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")

        order = self._orders[order_id]
        current_pct = order.position_pct

        if target_pct > current_pct:
            # 加仓
            additional_value = (target_pct - current_pct) * self._equity
            new_position_value = order.position_value + additional_value
            action = "increase"
        elif target_pct < current_pct:
            # 减仓
            reduce_value = (current_pct - target_pct) * self._equity
            new_position_value = order.position_value - reduce_value
            action = "decrease"
            # 退出部分仓位
            self._equity += reduce_value
        else:
            return {"action": "unchanged", "order_id": order_id}

        order.position_value = new_position_value
        order.position_pct = new_position_value / self._equity if self._equity > 0 else 0

        return {
            "action": action,
            "order_id": order_id,
            "previous_pct": current_pct,
            "new_pct": target_pct,
            "new_position_value": new_position_value,
        }

    # ========================================================================
    # 风险控制
    # ========================================================================

    def _check_risk_limits(self, order: PositionOrder) -> None:
        """检查风险限制"""
        tier_config = self._calculator._dynamic_calc.get_tier_config(self._current_tier)

        # 检查单笔风险
        if order.risk_amount > self._equity * tier_config["risk_per_trade"]:
            self._publish_risk_warning(
                "单笔风险超限",
                {
                    "order_risk": order.risk_amount,
                    "max_allowed": self._equity * tier_config["risk_per_trade"],
                    "risk_tier": self._current_tier.value,
                },
            )

        # 检查总仓位
        total_pct = self.total_position_pct
        if total_pct > tier_config["max_position_pct"]:
            self._publish_risk_warning(
                "总仓位超限",
                {
                    "total_pct": total_pct,
                    "max_allowed": tier_config["max_position_pct"],
                },
            )

        # 检查日亏损
        if self._daily_loss > self._equity * tier_config["max_daily_loss"]:
            self._publish_risk_warning(
                "日亏损超限",
                {
                    "daily_loss": self._daily_loss,
                    "max_allowed": self._equity * tier_config["max_daily_loss"],
                    "action": "建议暂停交易",
                },
            )

    def _publish_risk_warning(self, message: str, details: Dict[str, Any]) -> None:
        """发布风险警告"""
        self._logger.warning(f"风险警告: {message}, 详情: {details}")

        self.publish(
            "position.risk_warning",
            {
                "message": message,
                "details": details,
                "timestamp": time.time(),
            },
        )

        if self._on_risk_warning:
            self._on_risk_warning(message, details)

    def _update_max_drawdown(self) -> None:
        """更新最大回撤"""
        if self._equity < self._initial_equity:
            drawdown = (self._initial_equity - self._equity) / self._initial_equity
            self._max_drawdown = max(self._max_drawdown, drawdown)

    # ========================================================================
    # 事件处理
    # ========================================================================

    def _on_market_bar(self, event: Event) -> None:
        """处理 K线数据，更新订单当前价格"""
        bar = event.data
        if not bar:
            return

        symbol = bar.get("symbol")
        close_price = bar.get("close")

        if not symbol or not close_price:
            return

        # 更新相关订单的价格
        for order in self._orders.values():
            if order.symbol == symbol:
                order.current_price = close_price

                # 检查止损/止盈
                if order.stop_loss > 0:
                    if (order.side == "long" and close_price <= order.stop_loss) or (
                        order.side == "short" and close_price >= order.stop_loss
                    ):
                        self.close_order(order.order_id, close_price, "stop_loss")

                if order.take_profit > 0:
                    if (order.side == "long" and close_price >= order.take_profit) or (
                        order.side == "short" and close_price <= order.take_profit
                    ):
                        self.close_order(order.order_id, close_price, "take_profit")

    def _on_signal(self, event: Event) -> None:
        """处理交易信号"""
        signal_data = event.data
        if not signal_data:
            return

        self._current_signal = signal_data

        # 发布推荐仓位
        symbol = signal_data.get("symbol", "BTC")
        side = signal_data.get("signal", "long")
        confidence = signal_data.get("confidence", 1.0)
        atr = signal_data.get("indicators", {}).get("atr", 0.0)

        # 使用当前市场价格作为示例 (实际应从市场胶囊获取)
        entry_price = signal_data.get("current_price", 50000.0)

        result = self.calculate_position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            stop_loss_pct=0.02,
            signal_confidence=confidence,
            atr=atr,
        )

        self.publish(
            "position.recommended",
            {
                "symbol": symbol,
                "side": side,
                "recommended_position": result.position_value,
                "position_pct": result.position_pct,
                "risk_amount": result.risk_amount,
                "confidence": confidence,
            },
        )

    def _on_equity_update(self, event: Event) -> None:
        """处理资金更新"""
        data = event.data
        if not data:
            return

        new_equity = data.get("equity")
        if new_equity and new_equity != self._equity:
            old_tier = self._current_tier
            self._equity = new_equity
            self._current_tier = self._calculator._dynamic_calc.get_risk_tier(new_equity)

            # 风险等级变化通知
            if old_tier != self._current_tier:
                self.publish(
                    "position.tier_changed",
                    {
                        "old_tier": old_tier.value,
                        "new_tier": self._current_tier.value,
                        "equity": new_equity,
                    },
                )

    # ========================================================================
    # 属性
    # ========================================================================

    @property
    def equity(self) -> float:
        """当前权益"""
        return self._equity

    @property
    def available_margin(self) -> float:
        """可用保证金"""
        return self._available_margin

    @property
    def total_position_value(self) -> float:
        """总持仓金额"""
        return sum(o.position_value for o in self._orders.values())

    @property
    def total_position_pct(self) -> float:
        """总持仓百分比"""
        if self._equity == 0:
            return 0.0
        return self.total_position_value / self._equity

    @property
    def position_pct(self) -> float:
        """别名: 总持仓百分比"""
        return self.total_position_pct

    @property
    def risk_tier(self) -> RiskTier:
        """当前风险等级"""
        return self._current_tier

    @property
    def orders(self) -> Dict[str, PositionOrder]:
        """当前订单列表"""
        return self._orders.copy()

    @property
    def history(self) -> List[PositionHistory]:
        """历史记录"""
        return self._history.copy()

    @property
    def win_rate(self) -> float:
        """胜率"""
        total = self._win_count + self._loss_count
        if total == 0:
            return 0.0
        return self._win_count / total

    # ========================================================================
    # 配置方法
    # ========================================================================

    def set_algo_mode(self, mode: AlgoMode) -> None:
        """设置算法模式"""
        self._calculator.set_algo_mode(mode)
        self._logger.info(f"算法模式切换为: {mode.value}")

    def get_algo_mode(self) -> AlgoMode:
        """获取算法模式"""
        return self._calculator.get_algo_mode()

    def get_risk_profile(self) -> Dict[str, Any]:
        """获取风险配置画像"""
        profile = self._calculator.get_risk_profile(self._equity)
        profile.update(
            {
                "equity": self._equity,
                "initial_equity": self._initial_equity,
                "daily_loss": self._daily_loss,
                "max_drawdown": self._max_drawdown,
                "open_orders": len(self._orders),
                "total_position_pct": self.total_position_pct,
                "win_rate": self.win_rate,
                "win_count": self._win_count,
                "loss_count": self._loss_count,
            }
        )
        return profile

    def set_on_position_calculated(self, callback: Callable) -> None:
        """设置仓位计算回调"""
        self._on_position_calculated = callback

    def set_on_risk_warning(self, callback: Callable) -> None:
        """设置风险警告回调"""
        self._on_risk_warning = callback

    def reset_daily_loss(self) -> None:
        """重置日亏损计数 (每天开盘时调用)"""
        self._daily_loss = 0.0
        self._logger.info("日亏损计数已重置")

    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "equity": self._equity,
            "equity_change_pct": (self._equity - self._initial_equity) / self._initial_equity,
            "position_value": self.total_position_value,
            "position_pct": self.total_position_pct,
            "available_margin": self._available_margin,
            "risk_tier": self._current_tier.value,
            "open_orders": len(self._orders),
            "daily_loss": self._daily_loss,
            "max_drawdown": self._max_drawdown,
            "win_rate": self.win_rate,
            "total_trades": self._win_count + self._loss_count,
        }
