"""
NEMT四相位状态机模块
实现第二章、第六章中定义的状态机

包含：
1. 状态机核心 - 管理相位转换
2. 相位策略 - 每个相位的交易策略
3. 事件处理 - 相位转换事件
4. 历史记录 - 相位转换历史
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable, Tuple
from datetime import datetime
from enum import Enum
from collections import deque

from nemt_signals import (
    MarketPhase, NEMTSignals, NEMTSignalIndicators,
    DCISignal, VortexConditions, ResonanceConditions
)
from nemt_onchain import OnchainHealthScore, OnchainCalculator


class PhaseTransition(Enum):
    """相位转换类型"""
    NO_CHANGE = "no_change"
    A_TO_B = "a_to_b"
    B_TO_A = "b_to_a"
    B_TO_C = "b_to_c"
    B_TO_D = "b_to_d"
    C_TO_D = "c_to_d"
    C_TO_B = "c_to_b"
    C_TO_A = "c_to_a"
    D_TO_A = "d_to_a"
    D_TO_B = "d_to_b"
    D_TO_C = "d_to_c"


@dataclass
class PhaseHistory:
    """相位历史记录"""
    timestamp: datetime
    phase: MarketPhase
    duration_candles: int
    signals: Optional[Dict] = None
    price: Optional[float] = None


@dataclass
class PhaseTransitionEvent:
    """相位转换事件"""
    timestamp: datetime
    from_phase: MarketPhase
    to_phase: MarketPhase
    transition_type: PhaseTransition
    confidence: float
    trigger_signals: Dict
    price: float


@dataclass
class PhaseStrategy:
    """相位策略配置"""
    phase: MarketPhase
    name: str
    
    # 仓位配置
    max_position: float      # 最大仓位
    single_risk: float      # 单笔风险上限
    leverage_allowed: int   # 允许的杠杆倍数
    
    # 策略描述
    strategy_text: str       # 策略说明
    focus_text: str         # 关注重点
    avoid_text: str         # 避免事项
    
    # 信号阈值
    dci_high: float = 0.70   # DCI高阈值
    dci_low: float = 0.55    # DCI低阈值


@dataclass 
class StateMachineConfig:
    """状态机配置"""
    # 相位检测阈值
    dci_trend_threshold: float = 0.65   # 趋势判定DCI阈值
    dci_noise_threshold: float = 0.55    # 高噪声判定DCI阈值
    
    # 涡旋条件数要求
    vortex_conditions_required: int = 3    # 形成涡旋需要的条件数
    
    # 涡旋成熟度阈值
    vortex_maturity_low: float = 5.0    # 成熟涡旋下限
    vortex_maturity_high: float = 15.0    # 成熟涡旋上限
    
    # 随机共振置信度阈值
    resonance_confidence_threshold: float = 0.6  # 触发随机共振的置信度阈值
    
    # 相位持续时间要求
    min_phase_duration: int = 3  # 相位确认需要的最少K线数
    
    # 历史记录长度
    history_maxlen: int = 100


class NEMTStateMachine:
    """
    NEMT四相位状态机
    
    实现市场状态的自动识别和相位转换管理
    """

    # 相位策略配置
    PHASE_STRATEGIES: Dict[MarketPhase, PhaseStrategy] = {
        MarketPhase.PHASE_A_NOISE: PhaseStrategy(
            phase=MarketPhase.PHASE_A_NOISE,
            name="高噪声混乱期",
            max_position=0.20,
            single_risk=0.01,
            leverage_allowed=0,
            strategy_text="仅持有长期底仓，不做短线交易。等待DCI回升和结构形成。",
            focus_text="DCI何时回升、涡旋条件是否开始形成",
            avoid_text="在混乱期频繁交易、预判方向、追涨杀跌",
            dci_high=0.70,
            dci_low=0.55
        ),
        MarketPhase.PHASE_B_VORTEX: PhaseStrategy(
            phase=MarketPhase.PHASE_B_VORTEX,
            name="涡旋蓄力期",
            max_position=0.50,
            single_risk=0.02,
            leverage_allowed=1,
            strategy_text="识别区间边界，预设突破条件单，不预判方向。双向等待。",
            focus_text="涡旋成熟度、突破时的成交量确认",
            avoid_text="预判突破方向、提前入场、在区间内高抛低吸",
            dci_high=0.70,
            dci_low=0.55
        ),
        MarketPhase.PHASE_C_RESONANCE: PhaseStrategy(
            phase=MarketPhase.PHASE_C_RESONANCE,
            name="临界爆发前夜",
            max_position=0.70,
            single_risk=0.03,
            leverage_allowed=2,
            strategy_text="提高对突破信号的敏感度，敢于追入。初始仓位可提高。",
            focus_text="触发事件是否兑现、突破后量能是否持续",
            avoid_text="犹豫不决、等待更低/更高价位",
            dci_high=0.70,
            dci_low=0.55
        ),
        MarketPhase.PHASE_D_TREND: PhaseStrategy(
            phase=MarketPhase.PHASE_D_TREND,
            name="趋势运行期",
            max_position=1.00,
            single_risk=0.02,
            leverage_allowed=1,
            strategy_text="持仓为主，回调至均线加仓。享受趋势红利。",
            focus_text="DCI是否从高位回落、SNR是否萎缩、趋势是否衰竭",
            avoid_text="过早下车、频繁操作、趋势中做反向",
            dci_high=0.70,
            dci_low=0.55
        )
    }

    def __init__(self, config: Optional[StateMachineConfig] = None):
        self.config = config or StateMachineConfig()
        
        # 当前状态
        self.current_phase: MarketPhase = MarketPhase.PHASE_A_NOISE
        self.phase_duration: int = 0
        self.phase_confidence: float = 0.0
        
        # 历史记录
        self.phase_history: deque = deque(maxlen=self.config.history_maxlen)
        self.transition_history: List[PhaseTransitionEvent] = []
        
        # 信号计算器
        self.signal_indicators = NEMTSignalIndicators()
        self.onchain_calculator = OnchainCalculator()
        
        # 回调函数
        self.on_phase_change: Optional[Callable[[PhaseTransitionEvent], None]] = None
        
        # 统计数据
        self.stats = {
            "total_transitions": 0,
            "phase_a_duration": 0,
            "phase_b_duration": 0,
            "phase_c_duration": 0,
            "phase_d_duration": 0
        }

    def update(self, signals: NEMTSignals, price: float) -> Tuple[MarketPhase, Optional[PhaseTransitionEvent]]:
        """
        更新状态机
        
        Args:
            signals: NEMT信号
            price: 当前价格
            
        Returns:
            (当前相位, 转换事件如有)
        """
        old_phase = self.current_phase
        self.phase_duration += 1
        
        # 更新统计数据
        self._update_stats(old_phase)
        
        # 判断是否需要转换相位
        new_phase, confidence, trigger = self._evaluate_phase_transition(signals)
        
        transition_event = None
        
        if new_phase != old_phase and self.phase_duration >= self.config.min_phase_duration:
            # 记录历史
            self.phase_history.append(PhaseHistory(
                timestamp=datetime.now(),
                phase=old_phase,
                duration_candles=self.phase_duration,
                signals=self._signals_to_dict(signals),
                price=price
            ))
            
            # 创建转换事件
            transition_event = PhaseTransitionEvent(
                timestamp=datetime.now(),
                from_phase=old_phase,
                to_phase=new_phase,
                transition_type=self._get_transition_type(old_phase, new_phase),
                confidence=confidence,
                trigger_signals=trigger,
                price=price
            )
            
            self.transition_history.append(transition_event)
            self.current_phase = new_phase
            self.phase_duration = 0
            self.phase_confidence = confidence
            self.stats["total_transitions"] += 1
            
            # 触发回调
            if self.on_phase_change:
                self.on_phase_change(transition_event)
        
        else:
            self.current_phase = new_phase
            self.phase_confidence = max(self.phase_confidence, confidence)
        
        return self.current_phase, transition_event

    def _evaluate_phase_transition(
        self, 
        signals: NEMTSignals
    ) -> Tuple[MarketPhase, float, Dict]:
        """
        评估相位转换
        
        Returns:
            (新相位, 置信度, 触发信号)
        """
        dci = signals.dci
        vortex = signals.vortex
        resonance = signals.resonance
        
        trigger = {}
        confidence = 0.0
        
        # 优先级1: 随机共振触发 -> 相位C
        if resonance.is_resonance and resonance.confidence >= self.config.resonance_confidence_threshold:
            return MarketPhase.PHASE_C_RESONANCE, resonance.confidence, {
                "type": "resonance",
                "bullish": resonance.bullish,
                "confidence": resonance.confidence
            }
        
        # 优先级2: 涡旋形成 -> 相位B
        if vortex.is_vortex:
            conditions_met = sum([
                vortex.bbw_narrow,
                vortex.volume_uniform,
                vortex.oi_high_flat,
                vortex.funding_neutral
            ])
            
            # 成熟涡旋
            if self.config.vortex_maturity_low <= vortex.maturity_score <= self.config.vortex_maturity_high:
                confidence = 0.8
                return MarketPhase.PHASE_B_VORTEX, confidence, {
                    "type": "mature_vortex",
                    "maturity": vortex.maturity_score,
                    "conditions": conditions_met
                }
            # 幼年涡旋
            elif vortex.maturity_score < self.config.vortex_maturity_low:
                confidence = 0.6
                return MarketPhase.PHASE_B_VORTEX, confidence, {
                    "type": "immature_vortex",
                    "maturity": vortex.maturity_score,
                    "conditions": conditions_met
                }
        
        # 优先级3: 高DCI + 无涡旋 -> 相位D (趋势)
        if dci.value > self.config.dci_trend_threshold and not vortex.is_vortex:
            if dci.direction == "bullish":
                confidence = 0.7
                return MarketPhase.PHASE_D_TREND, confidence, {
                    "type": "trend_bullish",
                    "dci": dci.value
                }
            elif dci.direction == "bearish":
                confidence = 0.7
                return MarketPhase.PHASE_D_TREND, confidence, {
                    "type": "trend_bearish",
                    "dci": dci.value
                }
        
        # 优先级4: 低DCI -> 相位A (高噪声)
        if dci.value < self.config.dci_noise_threshold:
            confidence = 1.0 - (self.config.dci_noise_threshold - dci.value) / 0.1
            confidence = max(0.5, confidence)
            return MarketPhase.PHASE_A_NOISE, confidence, {
                "type": "high_noise",
                "dci": dci.value
            }
        
        # 过渡期 -> 相位A
        return MarketPhase.PHASE_A_NOISE, 0.5, {"type": "transition"}

    def _get_transition_type(
        self, 
        from_phase: MarketPhase, 
        to_phase: MarketPhase
    ) -> PhaseTransition:
        """获取转换类型"""
        transitions = {
            (MarketPhase.PHASE_A_NOISE, MarketPhase.PHASE_B_VORTEX): PhaseTransition.A_TO_B,
            (MarketPhase.PHASE_B_VORTEX, MarketPhase.PHASE_A_NOISE): PhaseTransition.B_TO_A,
            (MarketPhase.PHASE_B_VORTEX, MarketPhase.PHASE_C_RESONANCE): PhaseTransition.B_TO_C,
            (MarketPhase.PHASE_B_VORTEX, MarketPhase.PHASE_D_TREND): PhaseTransition.B_TO_D,
            (MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_D_TREND): PhaseTransition.C_TO_D,
            (MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_B_VORTEX): PhaseTransition.C_TO_B,
            (MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_A_NOISE): PhaseTransition.C_TO_A,
            (MarketPhase.PHASE_D_TREND, MarketPhase.PHASE_A_NOISE): PhaseTransition.D_TO_A,
            (MarketPhase.PHASE_D_TREND, MarketPhase.PHASE_B_VORTEX): PhaseTransition.D_TO_B,
            (MarketPhase.PHASE_D_TREND, MarketPhase.PHASE_C_RESONANCE): PhaseTransition.D_TO_C,
        }
        
        return transitions.get((from_phase, to_phase), PhaseTransition.NO_CHANGE)

    def _update_stats(self, phase: MarketPhase):
        """更新统计数据"""
        phase_counts = {
            MarketPhase.PHASE_A_NOISE: "phase_a_duration",
            MarketPhase.PHASE_B_VORTEX: "phase_b_duration",
            MarketPhase.PHASE_C_RESONANCE: "phase_c_duration",
            MarketPhase.PHASE_D_TREND: "phase_d_duration"
        }
        
        key = phase_counts.get(phase)
        if key:
            self.stats[key] += 1

    def _signals_to_dict(self, signals: NEMTSignals) -> Dict:
        """将信号转换为字典"""
        return {
            "dci_value": signals.dci.value,
            "dci_state": signals.dci.noise_state,
            "vortex_is_form": signals.vortex.is_vortex,
            "vortex_maturity": signals.vortex.maturity_score,
            "resonance_triggered": signals.resonance.is_resonance,
            "resonance_confidence": signals.resonance.confidence,
            "spectral_width": signals.spectral_width
        }

    def get_current_strategy(self) -> PhaseStrategy:
        """获取当前相位的策略"""
        return self.PHASE_STRATEGIES.get(
            self.current_phase,
            self.PHASE_STRATEGIES[MarketPhase.PHASE_A_NOISE]
        )

    def get_phase_distribution(self) -> Dict[str, float]:
        """获取相位分布统计"""
        total = sum([
            self.stats["phase_a_duration"],
            self.stats["phase_b_duration"],
            self.stats["phase_c_duration"],
            self.stats["phase_d_duration"]
        ])
        
        if total == 0:
            return {"A": 0, "B": 0, "C": 0, "D": 0}
        
        return {
            "A": self.stats["phase_a_duration"] / total,
            "B": self.stats["phase_b_duration"] / total,
            "C": self.stats["phase_c_duration"] / total,
            "D": self.stats["phase_d_duration"] / total
        }

    def get_state_summary(self) -> Dict:
        """获取状态摘要"""
        strategy = self.get_current_strategy()
        
        return {
            "current_phase": self.current_phase.value,
            "phase_name": strategy.name,
            "phase_duration": self.phase_duration,
            "phase_confidence": f"{self.phase_confidence:.1%}",
            "total_transitions": self.stats["total_transitions"],
            "phase_distribution": self.get_phase_distribution(),
            "max_position": f"{strategy.max_position:.0%}",
            "single_risk": f"{strategy.single_risk:.1%}",
            "leverage": f"{strategy.leverage_allowed}x",
            "strategy": strategy.strategy_text,
            "focus": strategy.focus_text,
            "avoid": strategy.avoid_text
        }

    def get_recent_transitions(self, n: int = 5) -> List[Dict]:
        """获取最近的N次转换"""
        recent = self.transition_history[-n:] if len(self.transition_history) >= n else self.transition_history
        
        return [
            {
                "timestamp": t.timestamp.isoformat(),
                "from": t.from_phase.value,
                "to": t.to_phase.value,
                "price": t.price,
                "confidence": f"{t.confidence:.1%}"
            }
            for t in reversed(recent)
        ]

    def reset(self):
        """重置状态机"""
        self.current_phase = MarketPhase.PHASE_A_NOISE
        self.phase_duration = 0
        self.phase_confidence = 0.0
        self.phase_history.clear()
        self.transition_history.clear()
        self.stats = {
            "total_transitions": 0,
            "phase_a_duration": 0,
            "phase_b_duration": 0,
            "phase_c_duration": 0,
            "phase_d_duration": 0
        }


class PhaseMonitor:
    """
    相位监控器
    
    用于实时监控和可视化状态机状态
    """

    def __init__(self, state_machine: NEMTStateMachine):
        self.sm = state_machine
        
    def get_dashboard_data(self) -> Dict:
        """获取仪表板数据"""
        summary = self.sm.get_state_summary()
        
        # 添加详细信号信息
        last_phase = self.sm.phase_history[-1] if len(self.sm.phase_history) > 0 else None
        
        return {
            "summary": summary,
            "phase": {
                "current": summary["current_phase"],
                "name": summary["phase_name"],
                "duration": summary["phase_duration"],
                "confidence": summary["phase_confidence"]
            },
            "strategy": {
                "max_position": summary["max_position"],
                "single_risk": summary["single_risk"],
                "leverage": summary["leverage"],
                "action": summary["strategy"],
                "focus": summary["focus"],
                "avoid": summary["avoid"]
            },
            "stats": {
                "total_transitions": summary["total_transitions"],
                "distribution": summary["phase_distribution"]
            },
            "recent_transitions": self.sm.get_recent_transitions(5)
        }

    def print_dashboard(self):
        """打印仪表板"""
        data = self.get_dashboard_data()
        
        print("\n" + "=" * 60)
        print("NEMT 相位监控仪表板")
        print("=" * 60)
        
        print(f"\n当前相位: [{data['phase']['current']}] {data['phase']['name']}")
        print(f"持续时间: {data['phase']['duration']} 根K线")
        print(f"置信度: {data['phase']['confidence']}")
        
        print(f"\n策略配置:")
        print(f"  最大仓位: {data['strategy']['max_position']}")
        print(f"  单笔风险: {data['strategy']['single_risk']}")
        print(f"  允许杠杆: {data['strategy']['leverage']}")
        
        print(f"\n当前策略:")
        print(f"  {data['strategy']['action']}")
        
        print(f"\n关注重点:")
        print(f"  {data['strategy']['focus']}")
        
        print(f"\n避免事项:")
        print(f"  {data['strategy']['avoid']}")
        
        print(f"\n相位统计:")
        print(f"  总转换次数: {data['stats']['total_transitions']}")
        dist = data['stats']['distribution']
        print(f"  相位分布: A={dist['A']:.1%} B={dist['B']:.1%} C={dist['C']:.1%} D={dist['D']:.1%}")
        
        if data['recent_transitions']:
            print(f"\n最近转换:")
            for t in data['recent_transitions'][:3]:
                print(f"  {t['timestamp'][:19]} | {t['from']} -> {t['to']} @ {t['price']:.2f}")
        
        print("=" * 60)


def create_demo_state_machine() -> NEMTStateMachine:
    """创建演示用状态机"""
    config = StateMachineConfig(
        dci_trend_threshold=0.65,
        dci_noise_threshold=0.55,
        vortex_conditions_required=3,
        vortex_maturity_low=5.0,
        vortex_maturity_high=15.0,
        resonance_confidence_threshold=0.6,
        min_phase_duration=3
    )
    
    return NEMTStateMachine(config)
