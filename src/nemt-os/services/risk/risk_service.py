"""
NEMT Platform - Risk Service
风控服务

职责：
- 订阅信号
- 仓位管理
- 止损/止盈检查
- 回撤控制
- 风险评分
"""

import asyncio
from dataclasses import dataclass, field

from ..base import BaseService
from ..common.types import EventTypes


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


class RiskService(BaseService):
    """
    Risk Service

    订阅事件：
    - signal.generated: 新信号

    发布事件：
    - risk.approved: 风控通过
    - risk.rejected: 风控拒绝
    - risk.alert: 风控警告
    """

    def __init__(self):
        super().__init__("risk", port=8003)

        # 风控参数
        self._max_position_size = 1.0
        self._max_drawdown = 0.2
        self._max_daily_loss = 0.05
        self._stop_loss_pct = 0.02
        self._take_profit_pct = 0.04

        # 账户状态
        self._initial_balance = 100000.0
        self._current_balance = 100000.0
        self._peak_balance = 100000.0
        self._daily_pnl = 0.0

        # 持仓
        self._positions: dict[str, dict] = {}

        # 风控日志
        self._risk_logs: list[dict] = []

    async def on_init(self):
        """初始化"""
        self.logger.info("Risk Service 初始化中...")

        # 设置参数
        self._max_position_size = 1.0
        self._max_drawdown = 0.2
        self._max_daily_loss = 0.05
        self._stop_loss_pct = 0.02
        self._take_profit_pct = 0.04

        self.logger.info("Risk Service 初始化完成")

    async def on_start(self):
        """启动"""
        self.logger.info("Risk Service 启动中...")

        # 订阅信号
        self.subscribe(EventTypes.SIGNAL_GENERATED, self._on_signal)

        self.logger.info("Risk Service 启动完成")

    async def _on_signal(self, data: dict):
        """处理信号"""
        await self.check_signal(data)

    async def check_signal(self, signal: dict) -> RiskCheckResult:
        """
        检查信号

        Args:
            signal: 信号数据

        Returns:
            风控结果
        """
        reasons = []
        risk_score = 0.0

        # 基础检查
        if self._current_balance <= 0:
            result = RiskCheckResult(
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
            await self._publish_result(result)
            return result

        # 回撤检查
        if self._peak_balance > 0:
            drawdown = (self._peak_balance - self._current_balance) / self._peak_balance
            if drawdown >= self._max_drawdown:
                result = RiskCheckResult(
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
                await self._publish_result(result)
                return result
            risk_score += drawdown

        # 日亏损检查
        if self._daily_pnl < -self._initial_balance * self._max_daily_loss:
            result = RiskCheckResult(
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
            await self._publish_result(result)
            return result

        # 仓位计算
        entry = signal.get("entry_price", signal.get("price", 0))
        sl = signal.get("stop_loss", entry * (1 - self._stop_loss_pct))
        tp = signal.get("take_profit", entry * (1 + self._take_profit_pct))
        confidence = signal.get("confidence", 0.5)

        # 风险回报比
        risk_amount = abs(entry - sl) if entry and sl else 0
        reward_amount = abs(tp - entry) if entry and tp else 0
        if risk_amount > 0:
            rr_ratio = reward_amount / risk_amount
            if rr_ratio < 1.5:
                reasons.append(f"风险回报比不足: {rr_ratio:.2f}")
                risk_score += 0.2

        # 头寸限制
        position_size = min(
            self._current_balance * self._max_position_size / entry if entry else 0,
            self._current_balance * 0.1 / entry if entry else 0,
        )

        # 调整止损/止盈
        adjusted_sl = sl if sl and sl > 0 else entry * (1 - self._stop_loss_pct) if entry else 0
        adjusted_tp = tp if tp and tp > 0 else entry * (1 + self._take_profit_pct) if entry else 0

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

        await self._publish_result(result)
        return result

    async def _publish_result(self, result: RiskCheckResult):
        """发布结果"""
        if result.approved:
            await self.publish(
                EventTypes.RISK_APPROVED,
                {
                    "signal_id": result.signal_id,
                    "symbol": result.symbol,
                    "position_size": result.position_size,
                    "adjusted_entry": result.adjusted_entry,
                    "adjusted_stop_loss": result.adjusted_stop_loss,
                    "adjusted_take_profit": result.adjusted_take_profit,
                    "reasons": result.reasons,
                    "risk_score": result.risk_score,
                },
            )
        else:
            await self.publish(
                EventTypes.RISK_REJECTED,
                {
                    "signal_id": result.signal_id,
                    "symbol": result.symbol,
                    "reasons": result.reasons,
                    "risk_score": result.risk_score,
                },
            )

    async def update_balance(self, balance: float):
        """更新余额"""
        if self._initial_balance == 0:
            self._initial_balance = balance
        self._current_balance = balance
        if balance > self._peak_balance:
            self._peak_balance = balance

    async def get_metrics(self) -> dict:
        """获取风控指标"""
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
        }


async def main():
    """入口"""
    service = RiskService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
