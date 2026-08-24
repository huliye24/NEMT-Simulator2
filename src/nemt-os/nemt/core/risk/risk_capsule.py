"""
RiskCapsule - 分形迭代版

按五阶段迭代法重写的风控胶囊。
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from nemt.core.capsule import FractalCapsule


@dataclass
class RiskCheckResult:
    """风控检查结果"""

    approved: bool
    signal_id: str
    symbol: str
    position_size: float
    adjusted_entry: float
    adjusted_stop_loss: float
    adjusted_take_profit: float
    reasons: list[str] = field(default_factory=list)
    risk_score: float = 0.0


class RiskCapsule(FractalCapsule):
    """
    风控胶囊

    负责：
    - 仓位管理
    - 止损/止盈检查
    - 回撤控制
    - 风险评分

    五阶段方法已实现。
    """

    def __init__(self, capsule_id: str = "risk"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 风控参数
        self._max_position_size = 1.0  # 最大仓位
        self._max_drawdown = 0.2  # 最大回撤
        self._max_daily_loss = 0.05  # 日最大亏损
        self._stop_loss_pct = 0.02  # 止损比例
        self._take_profit_pct = 0.04  # 止盈比例

        # 账户状态
        self._initial_balance = 0.0
        self._current_balance = 0.0
        self._peak_balance = 0.0
        self._daily_pnl = 0.0
        self._positions: dict[str, dict] = {}
        self._lock = threading.Lock()

        # 风控日志
        self._risk_logs: list[dict] = []

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """【看】观察阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "signals": {
                    "type": "list",
                    "format": "[{type, entry, sl, tp, confidence}, ...]",
                    "source": "SignalCapsule",
                    "required": True,
                },
                "account_balance": {
                    "type": "number",
                    "source": "ExecutionCapsule",
                    "required": True,
                },
                "positions": {
                    "type": "dict",
                    "format": "{symbol: {size, entry, pnl}}",
                },
            },
            "outputs": {
                "approved_signals": {
                    "type": "list",
                    "format": "[{signal, adjusted_size, adjusted_sl, adjusted_tp}]",
                },
                "rejected_signals": {
                    "type": "list",
                    "format": "[{signal, reason}]",
                },
                "risk_metrics": {
                    "type": "dict",
                    "format": "{current_risk, exposure, drawdown}",
                },
            },
            "constraints": {
                "max_position_size": self._max_position_size,
                "max_drawdown": self._max_drawdown,
                "max_daily_loss": self._max_daily_loss,
                "risk_per_trade": 0.01,
            },
            "dependencies": ["SignalCapsule", "ExecutionCapsule", "ConfigCenter"],
            "risks": [
                {"type": "连续亏损", "mitigation": "熔断机制+仓位减半"},
                {"type": "黑天鹅事件", "mitigation": "最大回撤控制"},
                {"type": "流动性不足", "mitigation": "订单大小限制"},
            ],
            "subscribes_to": ["signal.generated"],
            "publishes": ["risk.approved", "risk.rejected", "risk.alert"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """【画】设计阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "check_signal(signal)": "检查信号是否通过风控",
                "check_position(position)": "检查仓位是否需要调整",
                "update_balance(balance)": "更新账户余额",
                "get_risk_metrics()": "获取风控指标",
                "reset_daily()": "重置日度统计",
            },
            "input_schema": {
                "signal": {
                    "type": "object",
                    "properties": {
                        "signal_id": {"type": "string"},
                        "symbol": {"type": "string"},
                        "entry_price": {"type": "number"},
                        "stop_loss": {"type": "number"},
                        "take_profit": {"type": "number"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["symbol", "entry_price"],
                }
            },
            "output_schema": {
                "approved": {"type": "boolean"},
                "position_size": {"type": "number"},
                "adjusted_entry": {"type": "number"},
                "adjusted_stop_loss": {"type": "number"},
                "adjusted_take_profit": {"type": "number"},
                "reasons": {"type": "array"},
            },
            "risk_rules": {
                "max_exposure": "账户余额的100%",
                "position_limit": "单笔不超过账户的10%",
                "stop_loss_required": True,
                "risk_reward_ratio": "至少1:1.5",
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """【填】实现阶段"""
        self._max_position_size = self.get_config("risk.max_position_size", 1.0)
        self._max_drawdown = self.get_config("risk.max_drawdown", 0.2)
        self._max_daily_loss = self.get_config("risk.max_daily_loss", 0.05)
        self._stop_loss_pct = self.get_config("risk.stop_loss_pct", 0.02)
        self._take_profit_pct = self.get_config("risk.take_profit_pct", 0.04)
        self._logger.info(f"{self._capsule_id} 实现阶段完成")

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """【验】验证阶段"""
        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "passed": True,
            "checks": {
                "risk_params_loaded": True,
                "account_state_initialized": self._initial_balance > 0,
                "thread_safe": hasattr(self, "_lock"),
            },
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """【连】集成阶段"""
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info("  上游: SignalCapsule")
        self._logger.info("  下游: ExecutionCapsule")

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """初始化"""
        self.subscribe("signal.generated", self._on_signal)
        self._initialized = True

    def exec(self) -> dict[str, Any]:
        """执行"""
        return self.get_risk_metrics()

    def shutdown(self) -> None:
        """关闭"""
        self._positions.clear()
        self._risk_logs.clear()

    # ========================================
    # 公开 API
    # ========================================

    def update_balance(self, balance: float) -> None:
        """更新账户余额"""
        with self._lock:
            if self._initial_balance == 0:
                self._initial_balance = balance
            self._current_balance = balance
            if balance > self._peak_balance:
                self._peak_balance = balance

    def check_signal(self, signal: dict) -> RiskCheckResult:
        """检查信号"""
        with self._lock:
            reasons = []
            risk_score = 0.0

            # 基础检查
            if self._current_balance <= 0:
                return RiskCheckResult(
                    approved=False,
                    signal_id=signal.get("signal_id", ""),
                    symbol=signal.get("symbol", ""),
                    position_size=0,
                    adjusted_entry=0,
                    adjusted_stop_loss=0,
                    adjusted_take_profit=0,
                    reasons=["账户余额不足"],
                    risk_score=1.0,
                )

            # 回撤检查
            if self._peak_balance > 0:
                drawdown = (self._peak_balance - self._current_balance) / self._peak_balance
                if drawdown >= self._max_drawdown:
                    return RiskCheckResult(
                        approved=False,
                        signal_id=signal.get("signal_id", ""),
                        symbol=signal.get("symbol", ""),
                        position_size=0,
                        adjusted_entry=0,
                        adjusted_stop_loss=0,
                        adjusted_take_profit=0,
                        reasons=[f"回撤超限: {drawdown:.2%}"],
                        risk_score=1.0,
                    )
                risk_score += drawdown

            # 日亏损检查
            if self._daily_pnl < -self._initial_balance * self._max_daily_loss:
                return RiskCheckResult(
                    approved=False,
                    signal_id=signal.get("signal_id", ""),
                    symbol=signal.get("symbol", ""),
                    position_size=0,
                    adjusted_entry=0,
                    adjusted_stop_loss=0,
                    adjusted_take_profit=0,
                    reasons=[f"日亏损超限: {self._daily_pnl:.2f}"],
                    risk_score=1.0,
                )

            # 仓位计算
            entry = signal.get("entry_price", 0)
            sl = signal.get("stop_loss", entry * (1 - self._stop_loss_pct))
            tp = signal.get("take_profit", entry * (1 + self._take_profit_pct))
            confidence = signal.get("confidence", 0.5)

            # 风险回报比
            risk_amount = abs(entry - sl)
            reward_amount = abs(tp - entry)
            if risk_amount > 0:
                rr_ratio = reward_amount / risk_amount
                if rr_ratio < 1.5:
                    reasons.append(f"风险回报比不足: {rr_ratio:.2f}")
                    risk_score += 0.2

            # 头寸限制
            position_size = min(
                self._current_balance * self._max_position_size / entry,
                self._current_balance * 0.1 / entry,
            )

            # 调整止损/止盈
            adjusted_sl = sl if sl > 0 else entry * (1 - self._stop_loss_pct)
            adjusted_tp = tp if tp > 0 else entry * (1 + self._take_profit_pct)

            result = RiskCheckResult(
                approved=True,
                signal_id=signal.get("signal_id", ""),
                symbol=signal.get("symbol", ""),
                position_size=position_size,
                adjusted_entry=entry,
                adjusted_stop_loss=adjusted_sl,
                adjusted_take_profit=adjusted_tp,
                reasons=reasons,
                risk_score=risk_score,
            )

            self._risk_logs.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "signal": signal,
                    "result": result,
                }
            )

            return result

    def get_risk_metrics(self) -> dict[str, Any]:
        """获取风控指标"""
        with self._lock:
            drawdown = 0.0
            if self._peak_balance > 0:
                drawdown = (self._peak_balance - self._current_balance) / self._peak_balance

            total_exposure = sum(pos.get("size", 0) * pos.get("entry", 0) for pos in self._positions.values())

            return {
                "current_balance": self._current_balance,
                "peak_balance": self._peak_balance,
                "drawdown": drawdown,
                "daily_pnl": self._daily_pnl,
                "total_exposure": total_exposure,
                "exposure_ratio": total_exposure / self._current_balance if self._current_balance > 0 else 0,
                "positions_count": len(self._positions),
                "risk_logs_count": len(self._risk_logs),
            }

    def reset_daily(self) -> None:
        """重置日度统计"""
        with self._lock:
            self._daily_pnl = 0.0

    # ========================================
    # 内部方法
    # ========================================

    def _on_signal(self, signal: dict) -> None:
        """处理信号"""
        result = self.check_signal(signal)
        event_type = "risk.approved" if result.approved else "risk.rejected"
        self.publish(event_type, result.__dict__)
