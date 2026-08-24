"""
RiskCapsule - 风控胶囊

管理交易风险:
- 仓位限制
- 止损管理
- 最大回撤控制
- 风险事件监控
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["RiskCapsule"]


@dataclass
class RiskLimit:
    """风险限制"""

    name: str
    value: float
    current: float = 0.0
    enabled: bool = True


class RiskCapsule(ModuleCapsule):
    """
    风控胶囊

    订阅事件:
    - nemt.order_filled: 订单成交
    - nemt.position: 持仓变化
    - nemt.equity: 权益更新

    发布事件:
    - nemt.risk_warning: 风险警告
    - nemt.risk_violation: 风险违规
    - nemt.position_closed: 强制平仓
    """

    def __init__(self):
        super().__init__("risk")

        # 风控参数
        self._max_position_size: float = 0.2  # 最大仓位比例
        self._max_drawdown: float = 0.2  # 最大回撤
        self._stop_loss: float = 0.05  # 止损比例
        self._daily_loss_limit: float = 0.1  # 日内亏损限制
        self._max_leverage: float = 3.0  # 最大杠杆

        # 当前状态
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._equity: float = 10000.0
        self._peak_equity: float = 10000.0
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0

        # 风险事件记录
        self._risk_events: List[Dict[str, Any]] = []
        self._violations: List[Dict[str, Any]] = []

        # 状态
        self._is_defensive: bool = False
        self._last_warning_time: float = 0

    def init(self) -> None:
        """初始化 - 订阅事件"""
        # 从配置加载风控参数
        self._max_position_size = self.get_config("risk.max_position_size", 0.2)
        self._max_drawdown = self.get_config("risk.max_drawdown", 0.2)
        self._stop_loss = self.get_config("risk.stop_loss", 0.05)
        self._daily_loss_limit = self.get_config("risk.daily_loss_limit", 0.1)
        self._max_leverage = self.get_config("risk.max_leverage", 3.0)

        # 订阅事件
        self.subscribe("nemt.order_filled", self._on_order_filled)
        self.subscribe("nemt.position", self._on_position)
        self.subscribe("nemt.equity", self._on_equity)

        self._peak_equity = self._equity

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回风控状态

        Returns:
            风控状态字典
        """
        current_drawdown = self._calculate_drawdown()
        risk_level = self._calculate_risk_level(current_drawdown)

        return {
            # 风控状态
            "risk_level": risk_level,
            "is_defensive": self._is_defensive,
            # 当前风险
            "current_drawdown": current_drawdown,
            "max_drawdown": self._max_drawdown,
            "positions": len(self._positions),
            "daily_pnl": self._daily_pnl,
            "daily_trades": self._daily_trades,
            # 事件统计
            "risk_events_count": len(self._risk_events),
            "violations_count": len(self._violations),
            # 配置
            "max_position_size": self._max_position_size,
            "stop_loss": self._stop_loss,
            "max_leverage": self._max_leverage,
        }

    def check_order(self, order: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        检查订单是否合规

        Args:
            order: 订单信息

        Returns:
            (是否合规, 拒绝原因)
        """
        symbol = order.get("symbol", "BTC")
        quantity = order.get("quantity", 0)
        direction = order.get("direction", "long")

        # 检查仓位限制
        current_position = self._positions.get(symbol, {}).get("quantity", 0)
        new_position = current_position + quantity if direction == "long" else current_position - quantity

        if abs(new_position) > self._max_position_size * self._equity:
            reason = f"仓位超过限制: {abs(new_position)} > {self._max_position_size * self._equity}"
            self._record_violation("position_limit", order, reason)
            return False, reason

        # 检查杠杆
        leverage = self._calculate_leverage(symbol)
        if leverage > self._max_leverage:
            reason = f"杠杆超过限制: {leverage} > {self._max_leverage}"
            self._record_violation("leverage_limit", order, reason)
            return False, reason

        # 检查日内亏损
        if self._daily_pnl < -self._daily_loss_limit * self._equity:
            reason = f"日内亏损超限: {self._daily_pnl} < {-self._daily_loss_limit * self._equity}"
            self._record_violation("daily_loss_limit", order, reason)
            return False, reason

        return True, None

    def check_stop_loss(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        检查是否触发止损

        Args:
            symbol: 交易品种

        Returns:
            (是否止损, 原因)
        """
        position = self._positions.get(symbol)
        if not position:
            return False, None

        entry_price = position.get("entry_price", 0)
        current_price = position.get("current_price", entry_price)
        direction = position.get("direction", "long")
        quantity = position.get("quantity", 0)

        if entry_price == 0 or quantity == 0:
            return False, None

        # 计算亏损
        if direction == "long":
            loss_ratio = (entry_price - current_price) / entry_price
        else:
            loss_ratio = (current_price - entry_price) / entry_price

        if loss_ratio >= self._stop_loss:
            reason = f"触发止损: 亏损 {loss_ratio:.2%} >= {self._stop_loss:.2%}"
            self.publish("nemt.risk_warning", {"type": "stop_loss", "symbol": symbol, "loss_ratio": loss_ratio})
            return True, reason

        return False, None

    def _calculate_leverage(self, symbol: str) -> float:
        """
        计算持仓杠杆

        Args:
            symbol: 交易品种

        Returns:
            杠杆倍数
        """
        position = self._positions.get(symbol)
        if not position:
            return 1.0  # 无持仓默认为 1x

        quantity = position.get("quantity", 0)
        entry_price = position.get("entry_price", 0)

        if quantity == 0 or entry_price == 0:
            return 1.0

        # 简化计算：持仓价值 / 权益
        position_value = quantity * entry_price
        if self._equity > 0:
            return position_value / self._equity

        return 1.0

    def _on_order_filled(self, event: Event) -> None:
        """处理订单成交"""
        data = event.data
        if not data:
            return

        order = data.get("order")
        if not order:
            return

        # 更新持仓
        symbol = getattr(order, "symbol", "BTC")
        quantity = getattr(order, "quantity", 0)
        direction = getattr(order, "direction", "long")
        price = getattr(order, "price", 0)

        if symbol not in self._positions:
            self._positions[symbol] = {
                "quantity": 0,
                "direction": direction,
                "entry_price": price,
                "current_price": price,
                "pnl": 0,
            }

        pos = self._positions[symbol]
        if direction == "long":
            pos["quantity"] += quantity
        else:
            pos["quantity"] -= quantity
            if pos["quantity"] < 0:
                pos["quantity"] = 0

        # 更新统计数据
        self._daily_trades += 1

        pnl = data.get("pnl", 0)
        self._daily_pnl += pnl

    def _on_position(self, event: Event) -> None:
        """处理持仓变化"""
        data = event.data
        if not data:
            return

        symbol = data.get("symbol")
        if symbol:
            self._positions[symbol] = data

    def _on_equity(self, event: Event) -> None:
        """处理权益更新"""
        data = event.data
        if not data:
            return

        equity = data.get("value")
        if equity is not None:
            self._equity = equity

            # 更新峰值
            if equity > self._peak_equity:
                self._peak_equity = equity
                # 重置日内统计
                self._daily_pnl = 0
                self._daily_trades = 0

            # 检查回撤
            drawdown = self._calculate_drawdown()
            if drawdown >= self._max_drawdown:
                self._trigger_defensive_mode()

    def _calculate_drawdown(self) -> float:
        """计算当前回撤"""
        if self._peak_equity == 0:
            return 0.0
        return (self._peak_equity - self._equity) / self._peak_equity

    def _calculate_risk_level(self, drawdown: float) -> str:
        """计算风险等级"""
        drawdown_ratio = drawdown / self._max_drawdown if self._max_drawdown > 0 else 0

        if drawdown_ratio >= 0.8:
            return "critical"
        elif drawdown_ratio >= 0.5:
            return "high"
        elif drawdown_ratio >= 0.3:
            return "medium"
        elif drawdown_ratio >= 0.1:
            return "low"
        else:
            return "safe"

    def _trigger_defensive_mode(self) -> None:
        """触发防御模式"""
        if self._is_defensive:
            return

        self._is_defensive = True

        self.publish(
            "nemt.risk_warning",
            {"type": "defensive_mode", "drawdown": self._calculate_drawdown(), "message": "触发防御模式，回撤超限"},
        )

        # 记录事件
        self._risk_events.append(
            {"type": "defensive_mode", "time": self._get_time(), "drawdown": self._calculate_drawdown()}
        )

    def _record_violation(self, violation_type: str, order: Any, reason: str) -> None:
        """记录违规"""
        violation = {"type": violation_type, "reason": reason, "time": self._get_time(), "order": str(order)}

        self._violations.append(violation)

        self.publish("nemt.risk_violation", violation)

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        import time

        return time.time()

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("nemt.order_filled", self._on_order_filled)
        self.unsubscribe("nemt.position", self._on_position)
        self.unsubscribe("nemt.equity", self._on_equity)
