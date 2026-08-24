"""
PhaseStateMachineCapsule - 市场阶段状态机胶囊

管理市场阶段转换:
- 开盘/收盘检测
- 交易时段管理
- 阶段事件发布
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import datetime
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["PhaseStateMachineCapsule", "MarketPhase"]


class MarketPhase(Enum):
    """市场阶段"""

    PRE_MARKET = "pre_market"  # 盘前
    OPEN = "open"  # 开盘
    TRADING = "trading"  # 交易中
    CLOSE = "close"  # 收盘
    AFTER_HOURS = "after_hours"  # 盘后
    UNKNOWN = "unknown"  # 未知


class PhaseStateMachineCapsule(ModuleCapsule):
    """
    市场阶段状态机胶囊

    订阅事件:
    - market.bar: K线数据
    - market.phase_change: 外部阶段切换

    发布事件:
    - nemt.phase_changed: 阶段切换
    - nemt.phase_enter: 进入新阶段
    - nemt.phase_exit: 离开阶段
    """

    def __init__(self):
        super().__init__("phase")

        # 当前阶段
        self._current_phase = MarketPhase.UNKNOWN
        self._previous_phase = MarketPhase.UNKNOWN

        # 阶段配置 (简化: 24小时制)
        self._phase_config: Dict[MarketPhase, tuple[int, int]] = {
            MarketPhase.PRE_MARKET: (0, 9),  # 00:00 - 09:00
            MarketPhase.OPEN: (9, 9, 30),  # 09:00 - 09:30
            MarketPhase.TRADING: (9, 30, 16),  # 09:30 - 16:00
            MarketPhase.CLOSE: (16, 16, 30),  # 16:00 - 16:30
            MarketPhase.AFTER_HOURS: (16, 30, 24),  # 16:30 - 24:00
        }

        # 阶段处理器
        self._phase_handlers: Dict[MarketPhase, List[Callable]] = {}
        self._enter_handlers: Dict[MarketPhase, List[Callable]] = {}
        self._exit_handlers: Dict[MarketPhase, List[Callable]] = {}

        # 阶段统计
        self._phase_count: Dict[MarketPhase, int] = {}
        self._phase_duration: Dict[MarketPhase, float] = {}
        self._last_phase_change: float = 0

        # 外部控制
        self._auto_detect: bool = True

    def init(self) -> None:
        """初始化"""
        self.subscribe("market.bar", self._on_bar)
        self._last_phase_change = self._get_time()

        # 初始化所有阶段的统计
        for phase in MarketPhase:
            self._phase_count[phase] = 0
            self._phase_duration[phase] = 0.0

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回状态机状态

        Returns:
            状态机状态字典
        """
        current_duration = (
            self._get_time() - self._last_phase_change if self._current_phase != MarketPhase.UNKNOWN else 0
        )

        return {
            "current_phase": self._current_phase.value,
            "previous_phase": self._previous_phase.value,
            "phase_counts": {str(p.value): c for p, c in self._phase_count.items()},
            "phase_durations": {str(p.value): d for p, d in self._phase_duration.items()},
            "current_duration": current_duration,
            "last_change": self._last_phase_change,
            "auto_detect": self._auto_detect,
        }

    def _on_bar(self, event: Event) -> None:
        """处理 K线数据"""
        bar = event.data
        if not bar:
            return

        timestamp = bar.get("timestamp", 0)
        if not isinstance(timestamp, (int, float)):
            return

        # 自动检测阶段
        if self._auto_detect:
            new_phase = self._determine_phase(timestamp)

            if new_phase != self._current_phase:
                self._transition_to(new_phase)

    def _determine_phase(self, timestamp: float) -> MarketPhase:
        """
        根据时间戳确定阶段

        Args:
            timestamp: Unix 时间戳

        Returns:
            市场阶段
        """
        dt = datetime.datetime.fromtimestamp(timestamp)
        hour = dt.hour
        minute = dt.minute
        total_minutes = hour * 60 + minute

        # 简化判断
        if total_minutes < 9 * 60:  # < 09:00
            return MarketPhase.PRE_MARKET
        elif total_minutes < 9 * 60 + 30:  # < 09:30
            return MarketPhase.OPEN
        elif total_minutes < 16 * 60:  # < 16:00
            return MarketPhase.TRADING
        elif total_minutes < 16 * 60 + 30:  # < 16:30
            return MarketPhase.CLOSE
        else:
            return MarketPhase.AFTER_HOURS

    def _transition_to(self, new_phase: MarketPhase) -> None:
        """
        切换到新阶段

        Args:
            new_phase: 新阶段
        """
        if new_phase == self._current_phase:
            return

        old_phase = self._current_phase

        # 计算旧阶段持续时间
        if old_phase != MarketPhase.UNKNOWN:
            duration = self._get_time() - self._last_phase_change
            self._phase_duration[old_phase] += duration

            # 执行退出处理器
            self._execute_handlers(self._exit_handlers.get(old_phase, []))

            # 发布退出事件
            self.publish(
                "nemt.phase_exit",
                {
                    "phase": old_phase.value,
                    "duration": duration,
                },
            )

        # 更新状态
        self._previous_phase = old_phase
        self._current_phase = new_phase
        self._last_phase_change = self._get_time()

        # 自动初始化阶段计数
        if new_phase not in self._phase_count:
            self._phase_count[new_phase] = 0
        self._phase_count[new_phase] += 1

        # 执行进入处理器
        self._execute_handlers(self._enter_handlers.get(new_phase, []))

        # 发布阶段切换事件
        self.publish(
            "nemt.phase_changed",
            {
                "from": old_phase.value,
                "to": new_phase.value,
            },
        )

        # 发布进入事件
        self.publish(
            "nemt.phase_enter",
            {
                "phase": new_phase.value,
                "timestamp": self._last_phase_change,
            },
        )

    def _execute_handlers(self, handlers: List[Callable]) -> None:
        """执行处理器"""
        for handler in handlers:
            try:
                handler()
            except Exception as e:
                self._logger.error(f"Phase handler error: {e}")

    def register_phase_handler(self, phase: MarketPhase, handler: Callable) -> None:
        """注册阶段处理器 (阶段内持续执行)"""
        if phase not in self._phase_handlers:
            self._phase_handlers[phase] = []
        self._phase_handlers[phase].append(handler)

    def register_enter_handler(self, phase: MarketPhase, handler: Callable) -> None:
        """注册进入处理器"""
        if phase not in self._enter_handlers:
            self._enter_handlers[phase] = []
        self._enter_handlers[phase].append(handler)

    def register_exit_handler(self, phase: MarketPhase, handler: Callable) -> None:
        """注册退出处理器"""
        if phase not in self._exit_handlers:
            self._exit_handlers[phase] = []
        self._exit_handlers[phase].append(handler)

    def set_phase(self, phase: MarketPhase) -> None:
        """手动设置阶段"""
        self._transition_to(phase)

    def set_phase_by_name(self, phase_name: str) -> bool:
        """
        通过名称设置阶段

        Args:
            phase_name: 阶段名称

        Returns:
            是否成功
        """
        try:
            phase = MarketPhase(phase_name)
            self.set_phase(phase)
            return True
        except ValueError:
            return False

    def is_trading_phase(self) -> bool:
        """是否在交易时段"""
        return self._current_phase == MarketPhase.TRADING

    def is_market_open(self) -> bool:
        """市场是否开盘"""
        return self._current_phase in [MarketPhase.OPEN, MarketPhase.TRADING, MarketPhase.CLOSE]

    def get_phase_duration(self, phase: MarketPhase) -> float:
        """获取阶段总持续时间"""
        return self._phase_duration.get(phase, 0.0)

    def get_average_duration(self, phase: MarketPhase) -> float:
        """获取阶段平均持续时间"""
        count = self._phase_count.get(phase, 0)
        if count == 0:
            return 0.0
        return self._phase_duration.get(phase, 0.0) / count

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("market.bar", self._on_bar)

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        import time

        return time.time()
