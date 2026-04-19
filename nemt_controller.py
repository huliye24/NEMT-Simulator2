#!/usr/bin/env python3
"""
NEMT 调度器 - 统一控制器
=========================

整合 BrainLayer、ExecutionLayer、RiskLayer 的统一调度器。

功能:
1. 协调各层决策
2. 执行完整交易流程
3. 状态同步
4. 性能监控

使用方法:
    from nemt_controller import NEMTController

    controller = NEMTController(initial_capital=100000)
    decision = controller.make_decision(market_data)
    controller.execute(decision)
"""

import sys
sys.path.insert(0, '.')

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from brain_layer import (
    BrainLayer, Strategy, StrategyStatus, RiskMode,
    StrategyWeights, FundAllocation, StrategyScore
)
from nemt_execution import (
    NEMTExecutionFramework, Prediction, EntrySignal,
    ValidationResult, Position, TradePlan, Direction, CycleLevel
)
from nemt_risk import NEMTRiskManager, RiskStats
from nemt_state_machine import NEMTStateMachine, MarketPhase
from nemt_signals import NEMTSignals, VortexConditions, ResonanceConditions, DCISignal
from nemt_onchain import OnchainHealthScore

logger = logging.getLogger(__name__)


@dataclass
class TradingContext:
    """交易上下文"""
    timestamp: datetime = field(default_factory=datetime.now)
    market_phase: MarketPhase = MarketPhase.PHASE_A_NOISE
    macro_score: float = 5.0  # 宏观流动性评分 0-10
    onchain_score: float = 5.0  # 链上健康度评分 0-10
    current_price: float = 0.0
    signals: Optional[NEMTSignals] = None
    position: Optional[Position] = None
    account_balance: float = 100000.0
    current_drawdown: float = 0.0
    recent_loss: float = 0.0  # 近7天亏损


@dataclass
class ExecutionDecision:
    """执行决策"""
    brain_decision: Dict[str, Any]
    prediction: Optional[Prediction] = None
    entry_signals: List[EntrySignal] = field(default_factory=list)
    validation: Optional[ValidationResult] = None
    recommended_position: float = 0.0
    risk_mode: RiskMode = RiskMode.NORMAL
    position_adjustment: float = 1.0
    action: str = "hold"  # "buy", "sell", "hold", "wait"


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    action: str
    position: Optional[Position] = None
    pnl: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class StrategyAdapter:
    """策略适配器 - 将 BrainLayer Strategy 转换为 ExecutionFramework 可用的格式"""

    @staticmethod
    def to_execution_strategy(strategy: Strategy, weights: Dict[str, float]) -> Dict[str, Any]:
        """将 BrainLayer 策略转换为执行格式"""
        return {
            "id": strategy.id,
            "name": strategy.name,
            "type": strategy.type,
            "enabled": strategy.enabled,
            "status": strategy.status.value,
            "weight": weights.get(strategy.id, 0.0),
            "sharpe_ratio": strategy.sharpe_ratio,
            "win_rate": strategy.win_rate,
            "max_drawdown": strategy.max_drawdown
        }

    @staticmethod
    def from_trade_result(trade: Dict, strategy_id: str) -> Strategy:
        """从交易结果创建策略对象用于评分"""
        return Strategy(
            id=strategy_id,
            name=f"Strategy-{strategy_id}",
            type="derived",
            sharpe_ratio=trade.get("sharpe_ratio", 0.0),
            win_rate=1.0 if trade.get("pnl", 0) > 0 else 0.0,
            max_drawdown=trade.get("max_drawdown", 0.0),
            total_trades=1,
            recent_return=trade.get("pnl_pct", 0.0)
        )


class NEMTController:
    """
    NEMT 统一调度器

    协调 BrainLayer（决策大脑）、ExecutionFramework（执行框架）、
    RiskManager（风险管理）的工作。
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        strategy_ids: List[str] = None,
        config: Optional[Dict] = None
    ):
        """
        初始化控制器

        Args:
            initial_capital: 初始资金
            strategy_ids: 策略ID列表
            config: 配置字典
        """
        self.config = config or {}

        # 核心组件
        self.brain = BrainLayer(
            reserve_ratio=self.config.get("reserve_ratio", 0.10),
            warning_threshold=self.config.get("warning_threshold", 0.05),
            emergency_threshold=self.config.get("emergency_threshold", 0.15)
        )
        self.execution = NEMTExecutionFramework(initial_capital)
        self.risk = NEMTRiskManager(initial_capital)

        # 注册策略
        if strategy_ids:
            for sid in strategy_ids:
                self.brain.register_strategy(Strategy(
                    id=sid,
                    name=f"Strategy-{sid}",
                    type="auto"
                ))

        # 状态
        self.context = TradingContext()
        self.context.account_balance = initial_capital
        self.last_decision: Optional[ExecutionDecision] = None
        self.closed_trades: List[Dict] = []

        logger.info(f"NEMTController 初始化完成，初始资金: ${initial_capital:,.2f}")

    # =========================================================================
    # 决策流程
    # =========================================================================

    def analyze(self, context: TradingContext) -> ExecutionDecision:
        """
        分析市场并做出决策

        完整流程:
        1. BrainLayer 计算权重和风险模式
        2. ExecutionFramework 生成预测和信号
        3. RiskManager 评估仓位和止损
        4. 综合生成执行决策
        """
        self.context = context

        # 1. BrainLayer 综合决策
        brain_decision = self.brain.make_decision(
            total_capital=context.account_balance,
            current_drawdown=context.current_drawdown,
            recent_loss=context.recent_loss
        )

        decision = ExecutionDecision(
            brain_decision=brain_decision,
            risk_mode=RiskMode(brain_decision["risk_mode"]),
            position_adjustment=brain_decision["position_multiplier"]
        )

        # 2. ExecutionFramework 预测
        if context.signals:
            prediction = self.execution.predict(
                macro_score=context.macro_score,
                onchain_score=context.onchain_score
            )
            decision.prediction = prediction

            # 3. 生成入场信号
            if context.signals:
                entry_signals = self.execution.generate_signals(
                    signals=context.signals,
                    prediction=prediction
                )
                decision.entry_signals = entry_signals

                # 4. 验证信号
                if entry_signals:
                    signal = entry_signals[0]
                    validation = self.execution.validate_signal(
                        signal=signal,
                        current_price=context.current_price,
                        volume=self.config.get("volume", 0),
                        avg_volume=self.config.get("avg_volume", 0),
                        oi_change=self.config.get("oi_change", 0),
                        oi_change_pct=self.config.get("oi_change_pct", 0)
                    )
                    decision.validation = validation

        # 5. 计算推荐仓位
        recommended_position = self._calculate_position(decision)
        decision.recommended_position = recommended_position

        # 6. 确定行动
        decision.action = self._determine_action(decision)

        self.last_decision = decision
        return decision

    def _calculate_position(self, decision: ExecutionDecision) -> float:
        """计算推荐仓位"""
        if not decision.prediction:
            return 0.0

        # 基础仓位
        base_position = decision.prediction.confidence * 0.5

        # 风险模式调整
        mode_multiplier = decision.position_adjustment

        # 最终仓位
        position = base_position * mode_multiplier

        # 不能超过风险限制
        phase_config = self.risk.get_position_size(self.context.market_phase)
        position = min(position, phase_config.max_position)

        return max(0.0, min(1.0, position))

    def _determine_action(self, decision: ExecutionDecision) -> str:
        """确定行动"""
        # 无信号
        if not decision.prediction:
            return "hold"

        # 中性预测
        if decision.prediction.direction == Direction.NEUTRAL:
            return "wait"

        # 验证未通过
        if decision.validation and not decision.validation.passed:
            return "wait"

        # 仓位为0
        if decision.recommended_position <= 0:
            return "hold"

        # 风险模式限制
        if decision.risk_mode == RiskMode.EMERGENCY:
            return "hold"
        elif decision.risk_mode == RiskMode.WARNING:
            if decision.recommended_position < 0.1:
                return "hold"

        # 冷静期
        can_trade, reason = self.risk.should_trade()
        if not can_trade:
            logger.info(f"风控限制: {reason}")
            return "hold"

        # 决定行动
        if decision.prediction.direction == Direction.BULLISH:
            return "buy"
        elif decision.prediction.direction == Direction.BEARISH:
            return "sell"

        return "hold"

    # =========================================================================
    # 执行流程
    # =========================================================================

    def execute(self, decision: ExecutionDecision) -> ExecutionResult:
        """
        执行决策

        Args:
            decision: 执行决策

        Returns:
            ExecutionResult
        """
        action = decision.action

        if action == "hold" or action == "wait":
            return ExecutionResult(
                success=True,
                action=action,
                message="保持观望"
            )

        if action == "buy":
            return self._execute_buy(decision)
        elif action == "sell":
            return self._execute_sell(decision)

        return ExecutionResult(
            success=False,
            action=action,
            message="未知行动"
        )

    def _execute_buy(self, decision: ExecutionDecision) -> ExecutionResult:
        """执行买入"""
        if not decision.entry_signals or not decision.validation:
            return ExecutionResult(
                success=False,
                action="buy",
                message="缺少有效信号"
            )

        try:
            # 执行入场
            position = self.execution.execute_signal(
                signal=decision.entry_signals[0],
                validation=decision.validation,
                current_price=self.context.current_price,
                position_size=decision.recommended_position,
                stop_loss_pct=self.config.get("stop_loss_pct", 0.06)
            )

            self.context.position = position

            return ExecutionResult(
                success=True,
                action="buy",
                position=position,
                message=f"买入成功，入场价 ${position.entry_price:,.2f}"
            )

        except Exception as e:
            logger.error(f"买入执行失败: {e}")
            return ExecutionResult(
                success=False,
                action="buy",
                message=f"执行失败: {str(e)}"
            )

    def _execute_sell(self, decision: ExecutionDecision) -> ExecutionResult:
        """执行卖出"""
        if not self.context.position:
            return ExecutionResult(
                success=True,
                action="sell",
                message="无持仓，无需卖出"
            )

        try:
            # 平仓
            close_price = self.context.current_price
            is_win = close_price > self.context.position.entry_price

            trade = self.execution.close_position(
                position=self.context.position,
                close_price=close_price,
                reason=f"手动平仓",
                is_win=is_win
            )

            # 更新策略评分
            self._update_strategy_score(trade)

            self.closed_trades.append(trade)
            self.context.position = None

            return ExecutionResult(
                success=True,
                action="sell",
                position=self.context.position,
                pnl=trade["pnl"],
                message=f"卖出成功，{'盈利' if is_win else '亏损'} ${abs(trade['pnl']):,.2f}"
            )

        except Exception as e:
            logger.error(f"卖出执行失败: {e}")
            return ExecutionResult(
                success=False,
                action="sell",
                message=f"执行失败: {str(e)}"
            )

    def _update_strategy_score(self, trade: Dict):
        """更新策略评分"""
        if not trade:
            return

        for strategy in self.brain.strategies.values():
            if strategy.status == StrategyStatus.ACTIVE:
                # 简单更新：基于交易结果
                if trade.get("pnl", 0) > 0:
                    strategy.total_trades += 1
                    strategy.recent_return = trade.get("pnl_pct", 0)
                else:
                    strategy.total_trades += 1
                    strategy.recent_return = trade.get("pnl_pct", 0)

    # =========================================================================
    # 持仓管理
    # =========================================================================

    def check_exit_conditions(self) -> Tuple[bool, str]:
        """
        检查离场条件

        Returns:
            (是否离场, 原因)
        """
        if not self.context.position:
            return False, ""

        position = self.context.position

        # 更新持仓盈亏
        position.current_price = self.context.current_price
        position.unrealized_pnl = (
            (position.current_price - position.entry_price) * position.quantity
        )
        position.unrealized_pnl_pct = (
            (position.current_price - position.entry_price) / position.entry_price
        )

        # 止损检查
        should_stop, _ = self.execution.should_stop_loss(
            position=position,
            current_price=self.context.current_price
        )

        if should_stop:
            return True, "触发止损"

        # 止盈检查
        if self.context.signals:
            should_tp, _, reason = self.execution.should_take_profit(
                position=position,
                signals=self.context.signals,
                mvrv_score=self.context.onchain_score,
                nupl=0.5,  # 简化处理
                exchange_balance_trend="decreasing"
            )

            if should_tp:
                return True, reason

        # 相位变化检查
        if self.context.market_phase == MarketPhase.PHASE_A_NOISE:
            return True, "进入相位A（高噪声）"

        return False, ""

    def update_position(self) -> Optional[ExecutionResult]:
        """更新持仓状态"""
        if not self.context.position:
            return None

        # 检查离场
        should_exit, reason = self.check_exit_conditions()
        if should_exit:
            # 执行卖出
            decision = ExecutionDecision(
                brain_decision={},
                action="sell"
            )
            return self.execute(decision)

        # 更新移动止损
        new_stop = self.execution.update_stop_loss(
            position=self.context.position,
            current_price=self.context.current_price
        )
        self.context.position.stop_loss = new_stop

        return None

    # =========================================================================
    # 状态和报告
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        execution_summary = self.execution.get_framework_summary()
        risk_report = self.risk.get_risk_report()
        brain_health = self.brain.health_check()

        return {
            "timestamp": datetime.now().isoformat(),
            "capital": {
                "balance": self.context.account_balance,
                "in_position": self.context.position.unrealized_pnl if self.context.position else 0,
                "total": self.context.account_balance + (
                    self.context.position.unrealized_pnl if self.context.position else 0
                )
            },
            "position": {
                "has_position": self.context.position is not None,
                "entry_price": self.context.position.entry_price if self.context.position else None,
                "current_price": self.context.current_price,
                "unrealized_pnl": self.context.position.unrealized_pnl if self.context.position else 0,
                "stop_loss": self.context.position.stop_loss if self.context.position else None
            },
            "risk": risk_report,
            "execution": execution_summary,
            "brain": brain_health,
            "market": {
                "phase": self.context.market_phase.value,
                "macro_score": self.context.macro_score,
                "onchain_score": self.context.onchain_score
            }
        }

    def print_status(self):
        """打印状态报告"""
        status = self.get_status()

        print("\n" + "=" * 70)
        print("NEMT 调度器状态")
        print("=" * 70)

        print(f"\n时间: {status['timestamp']}")
        print(f"市场相位: {status['market']['phase']}")
        print(f"宏观评分: {status['market']['macro_score']}/10")
        print(f"链上评分: {status['market']['onchain_score']}/10")

        print(f"\n资金:")
        print(f"  余额: ${status['capital']['balance']:,.2f}")
        print(f"  持仓盈亏: ${status['capital']['in_position']:,.2f}")
        print(f"  总计: ${status['capital']['total']:,.2f}")

        print(f"\n持仓状态:")
        if status['position']['has_position']:
            print(f"  入场价: ${status['position']['entry_price']:,.2f}")
            print(f"  当前价: ${status['position']['current_price']:,.2f}")
            print(f"  浮亏: ${status['position']['unrealized_pnl']:,.2f}")
            print(f"  止损价: ${status['position']['stop_loss']:,.2f}")
        else:
            print("  无持仓")

        print(f"\n风控:")
        print(f"  风险等级: {status['risk']['risk_level']}")
        print(f"  行动: {status['risk']['risk_action']}")
        print(f"  回撤: {status['risk']['balance']['drawdown_pct']}")

        print(f"\n大脑层:")
        print(f"  风险模式: {status['brain']['current_mode']}")
        print(f"  仓位调整: {status['brain']['position_multiplier']:.0%}")
        print(f"  活跃策略: {status['brain']['active_strategies']}")

        print(f"\n执行统计:")
        stats = status['execution']['stats']
        print(f"  总交易: {stats['total_trades']}")
        print(f"  胜率: {stats['win_rate']}")
        print(f"  总盈亏: {stats['total_pnl']}")

        print("=" * 70)


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("NEMT Controller 单元测试")
    print("=" * 70)

    # 1. 初始化控制器
    print("\n1. 初始化控制器...")
    controller = NEMTController(
        initial_capital=100000,
        strategy_ids=["s1", "s2", "s3"]
    )
    print(f"   初始化完成")

    # 2. 创建模拟上下文
    print("\n2. 创建模拟上下文...")
    context = TradingContext(
        market_phase=MarketPhase.PHASE_C_RESONANCE,
        macro_score=7.0,
        onchain_score=6.0,
        current_price=50000.0,
        account_balance=100000,
        current_drawdown=0.02,
        recent_loss=0.01
    )

    # 创建模拟信号
    signals = NEMTSignals(
        phase=MarketPhase.PHASE_C_RESONANCE,
        dci=DCISignal(value=0.7, direction="bullish", trend="strengthening", noise_state="low"),
        vortex=VortexConditions(
            is_vortex=True,
            bbw_narrow=True,
            volume_uniform=True,
            oi_high_flat=True,
            funding_neutral=True,
            maturity_score=25
        ),
        resonance=ResonanceConditions(
            is_resonance=True,
            long_term_critical=True,
            short_term_noise=True,
            trigger_factor=True,
            confidence=0.75,
            bullish=True
        ),
        spectral_width=0.25
    )
    context.signals = signals
    controller.context = context

    print(f"   市场相位: {context.market_phase.value}")
    print(f"   宏观评分: {context.macro_score}")
    print(f"   当前价格: ${context.current_price:,.2f}")

    # 3. 分析决策
    print("\n3. 执行分析...")
    decision = controller.analyze(context)

    print(f"   行动: {decision.action}")
    print(f"   风险模式: {decision.risk_mode.value}")
    print(f"   仓位调整: {decision.position_adjustment:.0%}")
    print(f"   推荐仓位: {decision.recommended_position:.1%}")

    if decision.prediction:
        print(f"   预测方向: {decision.prediction.direction.value}")
        print(f"   置信度: {decision.prediction.confidence:.0%}")

    if decision.entry_signals:
        print(f"   入场信号: {len(decision.entry_signals)} 个")

    # 4. 执行
    print("\n4. 执行决策...")
    result = controller.execute(decision)
    print(f"   结果: {result.message}")

    # 5. 持仓管理
    print("\n5. 检查持仓...")
    controller.context.current_price = 50500.0  # 价格上涨
    exit_result = controller.update_position()
    if exit_result:
        print(f"   离场: {exit_result.message}")
    else:
        print(f"   持仓中，继续持有")

    # 6. 状态报告
    print("\n6. 状态报告...")
    controller.print_status()

    print("\n" + "=" * 70)
    print("✅ 所有测试通过")
    print("=" * 70)
