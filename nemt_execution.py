"""
NEMT执行框架模块
实现第七章中定义的完整交易流程

包含：
1. 预测系统 - 方向假设和周期级别
2. 信号系统 - 三类入场信号
3. 验证系统 - 信号验证清单
4. 加仓系统 - 加仓时机和规则
5. 止盈止损系统 - 完整的离场规则
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum
from collections import deque

from nemt_signals import MarketPhase, NEMTSignals
from nemt_onchain import OnchainHealthScore, CycleIndicators
from nemt_state_machine import NEMTStateMachine, PhaseStrategy


class Direction(Enum):
    """方向假设"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class CycleLevel(Enum):
    """预期周期级别"""
    INTRADAY = "intraday"    # 日内级别
    SWING = "swing"           # 波段级别 (周线)
    TREND = "trend"           # 趋势级别 (月线)


class SignalType(Enum):
    """入场信号类型"""
    VORTEX_BREAKOUT = "vortex_breakout"    # 涡旋突破信号
    RESONANCE_TRIGGER = "resonance_trigger"   # 随机共振触发信号
    TREND_CALLBACK = "trend_callback"          # 趋势回调信号
    MACRO_ONCHAIN = "macro_onchain"          # 宏观链上共振信号


class SignalStatus(Enum):
    """信号状态"""
    WAITING = "waiting"      # 等待中
    TRIGGERED = "triggered"   # 已触发
    CONFIRMED = "confirmed"    # 已确认
    FAILED = "failed"        # 失败


@dataclass
class Prediction:
    """预测结果"""
    direction: Direction
    cycle_level: CycleLevel
    confidence: float  # 0-1
    reasoning: str
    hunting_mode: bool  # 是否开启狩猎模式


@dataclass
class EntrySignal:
    """入场信号"""
    signal_type: SignalType
    status: SignalStatus
    triggered_at: Optional[float] = None
    entry_price: Optional[float] = None
    confidence: float = 0.0
    conditions_met: List[str] = field(default_factory=list)
    conditions_failed: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    passed_count: int
    required_count: int
    checks: Dict[str, bool]
    recommendation: str


@dataclass
class Position:
    """持仓"""
    entry_price: float
    quantity: float
    stop_loss: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    opened_at: datetime
    phase_at_entry: MarketPhase


@dataclass
class TradePlan:
    """交易计划"""
    prediction: Prediction
    entry_signals: List[EntrySignal]
    planned_position_size: float  # 计划仓位
    initial_position_size: float  # 初始仓位
    add_position_size: float     # 加仓仓位
    stop_loss: float
    take_profit_targets: List[float]
    risk_reward_ratio: float


@dataclass
class ExecutionFramework:
    """执行框架状态"""
    in_hunting_mode: bool = False
    current_prediction: Optional[Prediction] = None
    current_plan: Optional[TradePlan] = None
    active_signals: List[EntrySignal] = field(default_factory=list)
    position: Optional[Position] = None
    
    # 概率追踪
    p_trend: float = 0.5  # 趋势概率
    
    # 统计数据
    trades_count: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0


class NEMTExecutionFramework:
    """
    NEMT执行框架
    
    实现第七章定义的: 预测 → 信号 → 验证 → 加仓 四步流程
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.capital = initial_capital
        self.framework_state = ExecutionFramework()
        
        # 子系统
        self.state_machine = None  # 由外部注入
        
        # 历史记录
        self.trade_history: List[Dict] = []
        self.closed_trades: List[Dict] = []

    def set_state_machine(self, sm: NEMTStateMachine):
        """设置状态机"""
        self.state_machine = sm

    # =====================
    # 第一步: 预测
    # =====================
    
    def predict(
        self,
        macro_score: float,  # 宏观流动性评分 0-10
        onchain_score: float,  # 链上健康度评分 0-10
        cycle: Optional[CycleIndicators] = None,
        rti: Optional[float] = None  # 角色倾向指数
    ) -> Prediction:
        """
        预测步骤: 建立方向假设和预期周期级别
        
        Args:
            macro_score: 宏观流动性评分
            onchain_score: 链上健康度评分
            cycle: 周期定位
            rti: 角色倾向指数
            
        Returns:
            Prediction对象
        """
        # 方向判断
        if macro_score >= 7 and onchain_score >= 7:
            direction = Direction.BULLISH
            confidence = 0.85
            reasoning = "宏观和链上双重支持"
        elif macro_score >= 7 and onchain_score >= 4:
            direction = Direction.BULLISH
            confidence = 0.65
            reasoning = "宏观支持，链上中性"
        elif macro_score >= 4 and macro_score <= 6 and onchain_score >= 7:
            direction = Direction.BULLISH
            confidence = 0.60
            reasoning = "链上领先，偏多"
        elif macro_score <= 3 and onchain_score <= 3:
            direction = Direction.BEARISH
            confidence = 0.80
            reasoning = "宏观和链上双弱"
        elif macro_score >= 7 and onchain_score <= 3:
            direction = Direction.NEUTRAL
            confidence = 0.5
            reasoning = "宏观与链上背离，等待明确"
        else:
            direction = Direction.NEUTRAL
            confidence = 0.5
            reasoning = "条件不满足，保持中性"
        
        # RTI修正
        if rti is not None:
            if rti >= 5:  # 黄金模式
                if direction == Direction.BULLISH:
                    confidence = min(0.95, confidence + 0.1)
                    reasoning += "，黄金模式增强"
            elif rti <= -5:  # 科技股模式
                confidence = confidence * 0.9
                reasoning += "，科技股模式削弱"
        
        # 周期级别判断
        if macro_score >= 7 and onchain_score >= 7:
            cycle_level = CycleLevel.TREND
        elif macro_score >= 4 and onchain_score >= 4:
            cycle_level = CycleLevel.SWING
        else:
            cycle_level = CycleLevel.INTRADAY
        
        # 狩猎模式
        hunting_mode = direction != Direction.NEUTRAL and cycle_level in [CycleLevel.SWING, CycleLevel.TREND]
        
        prediction = Prediction(
            direction=direction,
            cycle_level=cycle_level,
            confidence=confidence,
            reasoning=reasoning,
            hunting_mode=hunting_mode
        )
        
        self.framework_state.current_prediction = prediction
        self.framework_state.in_hunting_mode = hunting_mode
        
        return prediction

    # =====================
    # 第二步: 信号
    # =====================
    
    def generate_signals(
        self,
        signals: NEMTSignals,
        prediction: Prediction
    ) -> List[EntrySignal]:
        """
        信号步骤: 识别入场信号
        
        Args:
            signals: NEMT信号
            prediction: 预测结果
            
        Returns:
            入场信号列表
        """
        entry_signals = []
        
        # 信号类型1: 涡旋突破
        if signals.vortex.is_vortex:
            # 检查方向
            direction = self._infer_breakout_direction(signals)
            signal = EntrySignal(
                signal_type=SignalType.VORTEX_BREAKOUT,
                status=SignalStatus.WAITING,
                confidence=min(0.8, 0.5 + signals.vortex.maturity_score / 30),
                conditions_met=["涡旋已形成"],
                conditions_failed=[]
            )
            entry_signals.append(signal)
        
        # 信号类型2: 随机共振触发
        if signals.resonance.is_resonance:
            bullish = signals.resonance.bullish
            direction_match = (
                (prediction.direction == Direction.BULLISH and bullish) or
                (prediction.direction == Direction.BEARISH and not bullish) or
                prediction.direction == Direction.NEUTRAL
            )
            
            if direction_match:
                signal = EntrySignal(
                    signal_type=SignalType.RESONANCE_TRIGGER,
                    status=SignalStatus.WAITING,
                    confidence=signals.resonance.confidence,
                    conditions_met=["随机共振触发", f"方向:{'看涨' if bullish else '看跌'}"],
                    conditions_failed=[]
                )
                entry_signals.append(signal)
        
        # 信号类型3: 趋势回调结束
        if signals.phase == MarketPhase.PHASE_D_TREND:
            if signals.dci.trend == "weakening":
                signal = EntrySignal(
                    signal_type=SignalType.TREND_CALLBACK,
                    status=SignalStatus.WAITING,
                    confidence=0.6,
                    conditions_met=["趋势运行期", "DCI从高位回落"],
                    conditions_failed=[]
                )
                entry_signals.append(signal)
        
        # 信号类型4: 宏观链上共振
        if (signals.dci.value > 0.65 and 
            signals.spectral_width is not None and 
            signals.spectral_width < 0.3):
            signal = EntrySignal(
                signal_type=SignalType.MACRO_ONCHAIN,
                status=SignalStatus.WAITING,
                confidence=0.7,
                conditions_met=["DCI>0.65", "谱宽<0.3"],
                conditions_failed=[]
            )
            entry_signals.append(signal)
        
        self.framework_state.active_signals = entry_signals
        return entry_signals

    def _infer_breakout_direction(self, signals: NEMTSignals) -> str:
        """推断突破方向"""
        if signals.dci.direction == "bullish":
            return "bullish"
        elif signals.dci.direction == "bearish":
            return "bearish"
        return "unknown"

    # =====================
    # 第三步: 验证
    # =====================
    
    def validate_signal(
        self,
        signal: EntrySignal,
        current_price: float,
        volume: float,
        avg_volume: float,
        oi_change: float,
        oi_change_pct: float,
        time_confirmed: int = 2,  # 突破后保持的K线数
        funding_rate: Optional[float] = None,
        exchange_flow: Optional[float] = None,
        on_btc: Optional[float] = None  # 交易所BTC净流出为正
    ) -> ValidationResult:
        """
        验证步骤: 确认信号真伪
        
        Args:
            signal: 待验证信号
            current_price: 当前价格
            volume: 当前成交量
            avg_volume: 平均成交量
            oi_change: OI变化
            oi_change_pct: OI变化百分比
            time_confirmed: 突破后保持的K线数
            funding_rate: 资金费率
            exchange_flow: 交易所BTC净流量
            on_btc: 链上BTC净流出
            
        Returns:
            ValidationResult对象
        """
        checks = {}
        
        if signal.signal_type == SignalType.VORTEX_BREAKOUT:
            # 涡旋突破验证清单
            checks["volume_confirmed"] = volume >= avg_volume * 1.5
            checks["oi_increasing"] = oi_change > 0 or oi_change_pct > 0.02
            checks["time_confirmed"] = time_confirmed >= 1
            checks["funding_confirmed"] = (
                funding_rate is None or 
                abs(funding_rate) < 0.0005 or 
                (funding_rate > 0 and signal.conditions_met[0])
            )
            checks["onchain_confirmed"] = exchange_flow is None or on_btc is None or on_btc > 0
            
            required_count = 4 if exchange_flow is not None else 3
            
        elif signal.signal_type == SignalType.RESONANCE_TRIGGER:
            # 随机共振验证清单
            checks["critical_sustained"] = time_confirmed >= 1
            checks["dci_vol_stable"] = True  # 已在共振检测中确认
            checks["price_no_reverse"] = abs(oi_change_pct) < 0.03  # 价格未大幅反向
            
            required_count = 3
            
        else:
            checks["volume_confirmed"] = volume >= avg_volume * 1.3
            checks["direction_confirmed"] = True
            required_count = 1
        
        passed_count = sum(checks.values())
        passed = passed_count >= required_count
        
        if passed_count >= required_count + 1:
            recommendation = "执行入场，仓位可适当放大"
        elif passed_count == required_count:
            recommendation = "谨慎通过，入场仓位减半"
        else:
            recommendation = "验证失败，放弃本次信号"
        
        return ValidationResult(
            passed=passed,
            passed_count=passed_count,
            required_count=required_count,
            checks=checks,
            recommendation=recommendation
        )

    # =====================
    # 第四步: 加仓
    # =====================
    
    def should_add_position(
        self,
        position: Position,
        current_price: float,
        atr: float,
        p_trend_updated: float,
        signals: NEMTSignals,
        add_trigger: str = "callback"  # "callback", "breakout", "probability"
    ) -> Tuple[bool, float]:
        """
        判断是否加仓
        
        Args:
            position: 当前持仓
            current_price: 当前价格
            atr: ATR值
            p_trend_updated: 更新后的趋势概率
            signals: 当前信号
            add_trigger: 加仓触发类型
            
        Returns:
            (是否加仓, 加仓比例)
        """
        # 基础条件: 持仓盈利
        if position.unrealized_pnl <= 0:
            return False, 0.0
        
        add_ratio = 0.0
        
        if add_trigger == "callback":
            # 回踩确认加仓
            callback_depth = (position.entry_price - current_price) / position.entry_price
            if callback_depth > 0.02 and callback_depth < 0.08:  # 回调2-8%
                if signals.dci.value > 0.60:
                    add_ratio = 0.30  # 现有仓位的30%
                    
        elif add_trigger == "breakout":
            # 突破确认加仓
            breakout_threshold = position.entry_price * 1.02  # 突破2%
            if current_price > breakout_threshold:
                add_ratio = 0.50  # 剩余计划仓位
        
        elif add_trigger == "probability":
            # 概率提升加仓
            p_increase = p_trend_updated - self.framework_state.p_trend
            if p_increase >= 0.10:
                add_ratio = min(0.50, p_increase * 2)
        
        return add_ratio > 0, add_ratio

    # =====================
    # 止盈止损
    # =====================
    
    def should_take_profit(
        self,
        position: Position,
        signals: NEMTSignals,
        mvrv_score: float,
        nupl: float,
        exchange_balance_trend: str  # "increasing", "decreasing"
    ) -> Tuple[bool, float, str]:
        """
        判断是否止盈
        
        Returns:
            (是否止盈, 止盈比例, 原因)
        """
        profit_pct = position.unrealized_pnl_pct
        
        # 第一批: MVRV > 5
        if mvrv_score > 5:
            return True, 0.30, f"MVRV过热({mvrv_score:.1f})，止盈30%"
        
        # 第二批: NUPL > 0.75
        if nupl > 0.75:
            return True, 0.30, f"NUPL贪婪({nupl:.2f})，止盈30%"
        
        # 第三批: 交易所余额由降转升
        if exchange_balance_trend == "increasing":
            return True, 0.30, "交易所余额上升(派发)，止盈30%"
        
        # 第四批: DCI从高位跌破
        if signals.dci.value < 0.55 and signals.dci.trend == "weakening":
            return True, 0.30, f"DCI破位({signals.dci.value:.2f})，止盈30%"
        
        return False, 0.0, ""

    def should_stop_loss(
        self,
        position: Position,
        current_price: float,
        stop_type: str = "atr"  # "atr", "fixed", "trailing"
    ) -> Tuple[bool, float]:
        """
        判断是否触发止损
        
        Returns:
            (是否止损, 止损价格)
        """
        if stop_type == "atr":
            # ATR止损需要atr值，这里简化处理
            stop_price = position.stop_loss
        else:
            stop_price = position.stop_loss
        
        return current_price <= stop_price, stop_price

    def update_stop_loss(
        self,
        position: Position,
        current_price: float,
        profit_threshold: float = 0.10
    ) -> float:
        """
        更新止损价(移动止损)
        
        Args:
            position: 持仓
            current_price: 当前价格
            profit_threshold: 启动移动止损的利润阈值
            
        Returns:
            新的止损价
        """
        current_profit = (current_price - position.entry_price) / position.entry_price
        
        if current_profit > profit_threshold:
            # 保本止损
            new_stop = position.entry_price * 1.005  # 成本价+0.5%
            return max(new_stop, position.stop_loss)
        
        return position.stop_loss

    # =====================
    # 完整交易流程
    # =====================
    
    def execute_signal(
        self,
        signal: EntrySignal,
        validation: ValidationResult,
        current_price: float,
        position_size: float,  # 0-1, 仓位比例
        stop_loss_pct: float = 0.06  # 6%初始止损
    ) -> Position:
        """
        执行入场
        
        Args:
            signal: 已验证信号
            validation: 验证结果
            current_price: 入场价格
            position_size: 仓位大小
            stop_loss_pct: 止损比例
            
        Returns:
            Position对象
        """
        if not validation.passed:
            raise ValueError("验证未通过，无法执行入场")
        
        # 计算持仓量
        position_value = self.capital * position_size
        quantity = position_value / current_price
        
        # 计算止损价
        if signal.signal_type == SignalType.VORTEX_BREAKOUT:
            stop_loss = current_price * (1 - stop_loss_pct)
        elif signal.signal_type == SignalType.RESONANCE_TRIGGER:
            stop_loss = current_price * (1 - stop_loss_pct * 1.3)  # 更宽松
        else:
            stop_loss = current_price * (1 - stop_loss_pct)
        
        position = Position(
            entry_price=current_price,
            quantity=quantity,
            stop_loss=stop_loss,
            current_price=current_price,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            opened_at=datetime.now(),
            phase_at_entry=self.state_machine.current_phase if self.state_machine else MarketPhase.PHASE_A_NOISE
        )
        
        self.framework_state.position = position
        self.framework_state.active_signals = []
        self.framework_state.trades_count += 1
        
        return position

    def close_position(
        self,
        position: Position,
        close_price: float,
        reason: str,
        is_win: bool
    ) -> Dict:
        """
        平仓
        
        Returns:
            交易记录字典
        """
        closed_trade = {
            "entry_price": position.entry_price,
            "exit_price": close_price,
            "quantity": position.quantity,
            "pnl": (close_price - position.entry_price) * position.quantity,
            "pnl_pct": (close_price - position.entry_price) / position.entry_price,
            "opened_at": position.opened_at,
            "closed_at": datetime.now(),
            "reason": reason,
            "phase": position.phase_at_entry.value,
            "is_win": is_win
        }
        
        # 更新统计
        if is_win:
            self.framework_state.wins += 1
        else:
            self.framework_state.losses += 1
        
        self.framework_state.total_pnl += closed_trade["pnl"]
        self.closed_trades.append(closed_trade)
        self.framework_state.position = None
        
        return closed_trade

    # =====================
    # 概率更新
    # =====================
    
    def update_probability(
        self,
        evidence_type: str,
        positive: bool
    ) -> float:
        """
        更新趋势概率 (贝叶斯简化版)
        
        Args:
            evidence_type: 证据类型
            positive: 是否正向证据
            
        Returns:
            更新后的概率
        """
        # 似然比
        likelihood_ratios = {
            "volume_breakout": 5.33 if positive else 0.17,
            "oi_increasing": 3.0 if positive else 0.33,
            "dci_cross": 2.33 if positive else 0.43,
            "funding_tilt": 1.86 if positive else 0.54,
            "exchange_outflow": 6.0 if positive else 0.17,
            "fake_breakout": 0.17 if positive else 1.0,
            "volume_fade": 0.17 if positive else 1.0,
        }
        
        lr = likelihood_ratios.get(evidence_type, 1.0)
        current_p = self.framework_state.p_trend
        
        # 简化贝叶斯更新
        new_p = (lr * current_p) / (lr * current_p + (1 - current_p))
        
        self.framework_state.p_trend = new_p
        return new_p

    def get_framework_summary(self) -> Dict:
        """获取框架状态摘要"""
        state = self.framework_state
        
        win_rate = state.wins / state.trades_count if state.trades_count > 0 else 0
        
        return {
            "in_hunting_mode": state.in_hunting_mode,
            "has_position": state.position is not None,
            "active_signals_count": len(state.active_signals),
            "p_trend": f"{state.p_trend:.1%}",
            "stats": {
                "total_trades": state.trades_count,
                "wins": state.wins,
                "losses": state.losses,
                "win_rate": f"{win_rate:.1%}",
                "total_pnl": f"{state.total_pnl:.2f}"
            },
            "prediction": {
                "direction": state.current_prediction.direction.value if state.current_prediction else None,
                "confidence": f"{state.current_prediction.confidence:.1%}" if state.current_prediction else None,
                "cycle_level": state.current_prediction.cycle_level.value if state.current_prediction else None,
                "hunting_mode": state.current_prediction.hunting_mode if state.current_prediction else None
            } if state.current_prediction else None
        }


def create_execution_framework(initial_capital: float = 100000.0) -> NEMTExecutionFramework:
    """创建执行框架"""
    return NEMTExecutionFramework(initial_capital)
