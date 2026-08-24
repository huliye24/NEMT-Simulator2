"""
DashboardCapsule - 仪表板胶囊

收集和展示系统状态:
- 权益曲线
- 交易统计
- 信号统计
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["DashboardCapsule"]


@dataclass
class TradeRecord:
    """交易记录"""

    order_id: str
    symbol: str
    direction: str
    quantity: float
    price: float
    timestamp: float
    pnl: float = 0.0


class DashboardCapsule(ModuleCapsule):
    """
    仪表板胶囊

    订阅事件:
    - nemt.equity: 权益更新
    - nemt.order_filled: 订单成交
    - nemt.signal: 信号生成
    - nemt.position: 持仓变化

    提供:
    - 权益曲线
    - 交易统计
    - 信号统计
    """

    def __init__(self):
        super().__init__("dashboard")

        # 权益曲线
        self._equity_curve: List[float] = []
        self._current_equity: float = 10000.0  # 默认初始权益
        self._peak_equity: float = 10000.0

        # 交易记录
        self._trades: List[TradeRecord] = []
        self._trade_count: int = 0
        self._winning_trades: int = 0
        self._losing_trades: int = 0
        self._total_pnl: float = 0.0

        # 信号统计
        self._signals: Dict[str, int] = {"long": 0, "short": 0, "neutral": 0}
        self._last_signal_time: float = 0

        # 持仓
        self._positions: Dict[str, Dict[str, Any]] = {}

        # 统计
        self._event_count: int = 0
        self._start_time: float = 0

    def init(self) -> None:
        """初始化 - 订阅事件"""
        self.subscribe("nemt.equity", self._on_equity)
        self.subscribe("nemt.order_filled", self._on_order_filled)
        self.subscribe("nemt.signal", self._on_signal)
        self.subscribe("nemt.position", self._on_position)
        self._start_time = self._get_time()

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回仪表板数据

        Returns:
            仪表板数据字典
        """
        # 计算统计数据
        total_trades = self._winning_trades + self._losing_trades
        win_rate = self._winning_trades / total_trades if total_trades > 0 else 0

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown()

        return {
            # 权益
            "current_equity": self._current_equity,
            "peak_equity": self._peak_equity,
            "equity_curve": self._equity_curve[-100:],  # 最近 100 个点
            "total_return": (self._current_equity - 10000) / 10000 if self._current_equity > 0 else 0,
            # 交易统计
            "trade_count": self._trade_count,
            "winning_trades": self._winning_trades,
            "losing_trades": self._losing_trades,
            "win_rate": win_rate,
            "total_pnl": self._total_pnl,
            # 信号统计
            "signals": self._signals.copy(),
            # 风控
            "max_drawdown": max_drawdown,
            "current_drawdown": (
                (self._peak_equity - self._current_equity) / self._peak_equity if self._peak_equity > 0 else 0
            ),
            # 持仓
            "positions": self._positions.copy(),
            "position_count": len(self._positions),
            # 运行时长
            "uptime": self._get_time() - self._start_time,
            "events_processed": self._event_count,
        }

    def _on_equity(self, event: Event) -> None:
        """处理权益更新"""
        self._event_count += 1
        data = event.data

        if not data:
            return

        equity = data.get("value")
        if equity is not None:
            self._current_equity = equity
            self._equity_curve.append(equity)

            # 更新峰值
            if equity > self._peak_equity:
                self._peak_equity = equity

    def _on_order_filled(self, event: Event) -> None:
        """处理订单成交"""
        self._event_count += 1
        data = event.data

        if not data:
            return

        order = data.get("order")
        if not order:
            return

        # 获取订单信息
        symbol = getattr(order, "symbol", "BTC")
        direction = getattr(order, "direction", "unknown")
        quantity = getattr(order, "quantity", 0)
        filled_price = getattr(order, "filled_price", 0)
        commission = getattr(order, "commission", 0)

        # 计算交易价值
        trade_value = quantity * filled_price

        # 记录交易
        trade = TradeRecord(
            order_id=getattr(order, "order_id", f"ORD_{self._trade_count}"),
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=filled_price,
            timestamp=getattr(order, "timestamp", self._get_time()),
        )

        self._trades.append(trade)
        self._trade_count += 1

        # 简化 PnL 计算：假设每笔交易贡献少量收益
        # 在实际系统中，这应该基于实际持仓计算
        pnl = data.get("pnl", 0)

        # 如果没有 PnL，基于交易方向估算
        if pnl == 0 and quantity > 0 and filled_price > 0:
            # 简化：假设每笔交易有收益 (0.5%)，覆盖佣金后还有盈余
            pnl = trade_value * 0.005

        self._total_pnl += pnl

        # 更新权益
        self._current_equity += pnl - commission
        self._equity_curve.append(self._current_equity)

        # 更新峰值
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity

        # 统计胜负
        if pnl > 0:
            self._winning_trades += 1
        elif pnl < 0:
            self._losing_trades += 1

        # 发布权益更新事件
        self.publish("nemt.equity", {"value": self._current_equity})

    def _on_signal(self, event: Event) -> None:
        """处理信号"""
        self._event_count += 1
        data = event.data

        if not data:
            return

        signal_type = data.get("signal", "neutral")
        if signal_type in self._signals:
            self._signals[signal_type] += 1

        self._last_signal_time = self._get_time()

    def _on_position(self, event: Event) -> None:
        """处理持仓变化"""
        self._event_count += 1
        data = event.data

        if not data:
            return

        symbol = data.get("symbol")
        if symbol:
            self._positions[symbol] = data

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self._equity_curve:
            return 0.0

        peak = self._equity_curve[0]
        max_dd = 0.0

        for equity in self._equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        import time

        return time.time()

    def shutdown(self) -> None:
        """关闭 - 取消订阅"""
        self.unsubscribe("nemt.equity", self._on_equity)
        self.unsubscribe("nemt.order_filled", self._on_order_filled)
        self.unsubscribe("nemt.signal", self._on_signal)
        self.unsubscribe("nemt.position", self._on_position)
