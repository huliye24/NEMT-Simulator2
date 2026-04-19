# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
增强四相位检测模块 - 支线2信号识别
=====================================
基于NEMT理论的增强版市场四相位识别系统。

相位定义：
- A (高噪声混乱期): 市场无序波动，无明显方向
- B (涡旋蓄力期): 能量聚集，波动率收窄
- C (临界爆发前夜): 临界状态，随时可能突破
- D (趋势运行期): 单边趋势形成并延续

增强特性：
1. 多指标综合判断
2. 动态阈值调整
3. 相位转换预警
4. 置信度量化

作者：NEMT Lab
日期：2026-04-19
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class Phase(Enum):
    """市场相位枚举"""
    NOISE = "A"           # 高噪声混乱期
    VORTEX = "B"          # 涡旋蓄力期
    CRITICAL = "C"         # 临界爆发前夜
    TREND = "D"           # 趋势运行期


@dataclass
class PhaseThresholds:
    """相位判断阈值配置"""
    # DCI阈值
    dci_high: float = 0.70      # 趋势阈值
    dci_low: float = 0.55       # 噪声阈值
    dci_medium: float = 0.65    # 中等阈值
    
    # 谱宽阈值
    spectral_width_low: float = 0.02   # 谱宽低位（涡旋特征）
    spectral_width_high: float = 0.08   # 谱宽高位（混乱特征）
    
    # 涡旋成熟度
    vortex_min_score: float = 5.0
    vortex_mature_score: float = 12.0
    
    # 共振置信度
    resonance_confidence_min: float = 0.5
    
    # 趋势确认
    trend_min_duration: int = 3    # 趋势确认最少K线数


@dataclass
class PhaseConfidence:
    """相位置信度"""
    primary: float = 0.0      # 主置信度
    secondary: float = 0.0   # 辅助置信度
    combined: float = 0.0     # 综合置信度
    
    # 各指标贡献
    dci_contribution: float = 0.0
    spectral_contribution: float = 0.0
    vortex_contribution: float = 0.0
    resonance_contribution: float = 0.0
    momentum_contribution: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'primary': self.primary,
            'secondary': self.secondary,
            'combined': self.combined,
            'dci': self.dci_contribution,
            'spectral': self.spectral_contribution,
            'vortex': self.vortex_contribution,
            'resonance': self.resonance_contribution,
            'momentum': self.momentum_contribution,
        }


@dataclass
class PhaseTransitionWarning:
    """相位转换预警"""
    current_phase: Phase
    likely_next_phase: Phase
    confidence: float
    time_remaining: int  # 预计多少K线后转换
    indicators: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PhaseAnalysisResult:
    """相位分析结果"""
    # 基本信息
    phase: Phase
    phase_name: str
    confidence: PhaseConfidence
    
    # 核心指标
    dci_value: float
    spectral_width: float
    vortex_score: float
    resonance_confidence: float
    
    # 趋势信息
    trend_direction: str  # "bullish", "bearish", "neutral"
    trend_strength: float  # 0-1
    trend_duration: int   # 趋势持续K线数
    
    # 市场特征
    volatility_level: str  # "low", "medium", "high"
    momentum_level: str    # "weak", "moderate", "strong"
    
    # 预警
    transition_warning: Optional[PhaseTransitionWarning] = None
    
    # 策略建议
    position_ratio: float = 0.0
    max_position: float = 0.0
    single_risk: float = 0.0
    leverage: int = 0
    strategy_text: str = ""
    focus_text: str = ""
    avoid_text: str = ""
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    historical_phases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.value,
            'phase_name': self.phase_name,
            'confidence': self.confidence.to_dict(),
            'indicators': {
                'dci': self.dci_value,
                'spectral_width': self.spectral_width,
                'vortex_score': self.vortex_score,
                'resonance_confidence': self.resonance_confidence,
            },
            'trend': {
                'direction': self.trend_direction,
                'strength': self.trend_strength,
                'duration': self.trend_duration,
            },
            'market': {
                'volatility': self.volatility_level,
                'momentum': self.momentum_level,
            },
            'strategy': {
                'position_ratio': self.position_ratio,
                'max_position': self.max_position,
                'single_risk': self.single_risk,
                'leverage': self.leverage,
                'action': self.strategy_text,
                'focus': self.focus_text,
                'avoid': self.avoid_text,
            },
            'transition_warning': self.transition_warning.__dict__ if self.transition_warning else None,
            'timestamp': self.timestamp,
        }


class EnhancedPhaseDetector:
    """
    增强版四相位检测器
    
    综合多指标判断市场相位，提供置信度和预警
    """
    
    # 相位名称映射
    PHASE_NAMES = {
        Phase.NOISE: "高噪声混乱期",
        Phase.VORTEX: "涡旋蓄力期",
        Phase.CRITICAL: "临界爆发前夜",
        Phase.TREND: "趋势运行期",
    }
    
    # 相位策略配置
    PHASE_STRATEGIES = {
        Phase.NOISE: {
            'position_ratio': 0.20,
            'max_position': 0.20,
            'single_risk': 0.01,
            'leverage': 0,
            'action': "仅持有长期底仓，不做短线交易。等待DCI回升和结构形成。",
            'focus': "DCI何时回升、涡旋条件是否开始形成",
            'avoid': "在混乱期频繁交易、预判方向、追涨杀跌",
        },
        Phase.VORTEX: {
            'position_ratio': 0.35,
            'max_position': 0.50,
            'single_risk': 0.02,
            'leverage': 1,
            'action': "识别区间边界，预设突破条件单，不预判方向。双向等待。",
            'focus': "涡旋成熟度、突破时的成交量确认",
            'avoid': "预判突破方向、提前入场、在区间内高抛低吸",
        },
        Phase.CRITICAL: {
            'position_ratio': 0.60,
            'max_position': 0.70,
            'single_risk': 0.03,
            'leverage': 2,
            'action': "提高对突破信号的敏感度，敢于追入。初始仓位可提高。",
            'focus': "触发事件是否兑现、突破后量能是否持续",
            'avoid': "犹豫不决、等待更低/更高价位",
        },
        Phase.TREND: {
            'position_ratio': 0.85,
            'max_position': 1.00,
            'single_risk': 0.02,
            'leverage': 1,
            'action': "持仓为主，回调至均线加仓。享受趋势红利。",
            'focus': "DCI是否从高位回落、SNR是否萎缩、趋势是否衰竭",
            'avoid': "过早下车、频繁操作、趋势中做反向",
        },
    }
    
    def __init__(self, thresholds: Optional[PhaseThresholds] = None):
        self.thresholds = thresholds or PhaseThresholds()
        
        # 历史记录
        self.phase_history: List[Phase] = []
        self.phase_timestamps: List[str] = []
        self.current_trend_duration: int = 0
        
        # 统计
        self.phase_counts = {p: 0 for p in Phase}
    
    def analyze(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        dci: Optional[float] = None,
        spectral_width: Optional[float] = None,
        vortex_score: Optional[float] = None,
        resonance_confidence: Optional[float] = None,
        momentum: Optional[float] = None,
    ) -> PhaseAnalysisResult:
        """
        综合分析市场相位
        
        Args:
            prices: 价格序列
            volumes: 成交量序列（可选）
            dci: DCI值（可选，自动计算）
            spectral_width: 谱宽（可选）
            vortex_score: 涡旋成熟度（可选）
            resonance_confidence: 共振置信度（可选）
            momentum: 动量指标（可选）
            
        Returns:
            PhaseAnalysisResult
        """
        # 计算缺失的指标
        if dci is None:
            dci = self._compute_dci(prices)
        
        if spectral_width is None:
            spectral_width = self._compute_spectral_width(prices)
        
        # 趋势方向和强度
        trend_direction, trend_strength = self._analyze_trend(prices)
        
        # 波动率水平
        volatility_level = self._analyze_volatility(prices)
        
        # 动量水平
        momentum_level = self._analyze_momentum(momentum or prices)
        
        # 综合判断相位
        phase, confidence = self._determine_phase(
            dci, spectral_width, vortex_score, resonance_confidence,
            trend_direction, trend_strength, momentum_level
        )
        
        # 获取策略配置
        strategy = self.PHASE_STRATEGIES[phase]
        
        # 更新历史
        self._update_history(phase)
        
        # 检测相位转换预警
        warning = self._detect_transition_warning(phase, confidence)
        
        # 构建结果
        result = PhaseAnalysisResult(
            phase=phase,
            phase_name=self.PHASE_NAMES[phase],
            confidence=confidence,
            dci_value=dci,
            spectral_width=spectral_width or 0.0,
            vortex_score=vortex_score or 0.0,
            resonance_confidence=resonance_confidence or 0.0,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_duration=self.current_trend_duration if phase == Phase.TREND else 0,
            volatility_level=volatility_level,
            momentum_level=momentum_level,
            transition_warning=warning,
            position_ratio=strategy['position_ratio'],
            max_position=strategy['max_position'],
            single_risk=strategy['single_risk'],
            leverage=strategy['leverage'],
            strategy_text=strategy['action'],
            focus_text=strategy['focus'],
            avoid_text=strategy['avoid'],
            historical_phases=[p.value for p in self.phase_history[-10:]]
        )
        
        return result
    
    def _compute_dci(self, prices: np.ndarray) -> float:
        """计算DCI"""
        if len(prices) < 2:
            return 0.5
        
        returns = np.diff(prices)
        up_count = np.sum(returns > 0)
        down_count = np.sum(returns < 0)
        n = len(returns)
        
        if n == 0:
            return 0.5
        
        return max(up_count, down_count) / n
    
    def _compute_spectral_width(self, prices: np.ndarray) -> float:
        """计算谱宽"""
        if len(prices) < 10:
            return 0.05
        
        # 简化的谱宽计算
        returns = np.diff(prices)
        fft_result = np.fft.fft(returns - np.mean(returns))
        spectrum_power = np.abs(fft_result) ** 2
        
        # 归一化
        spectrum_power = spectrum_power / (np.max(spectrum_power) + 1e-10)
        
        # 计算"谱宽"作为波动率代理
        return float(np.std(spectrum_power))
    
    def _analyze_trend(self, prices: np.ndarray) -> Tuple[str, float]:
        """分析趋势"""
        if len(prices) < 20:
            return "neutral", 0.0
        
        # 简单趋势判断
        ma_short = np.mean(prices[-10:])
        ma_long = np.mean(prices[-20:])
        
        if ma_short > ma_long * 1.02:
            direction = "bullish"
        elif ma_short < ma_long * 0.98:
            direction = "bearish"
        else:
            direction = "neutral"
        
        # 趋势强度
        recent_volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
        price_change = (prices[-1] - prices[-20]) / prices[-20]
        strength = min(abs(price_change) / recent_volatility, 1.0) if recent_volatility > 0 else 0.0
        
        return direction, strength
    
    def _analyze_volatility(self, prices: np.ndarray) -> str:
        """分析波动率水平"""
        if len(prices) < 20:
            return "medium"
        
        returns = np.diff(np.log(prices))
        volatility = np.std(returns[-20:]) * np.sqrt(252)  # 年化波动率
        
        if volatility < 0.3:
            return "low"
        elif volatility < 0.8:
            return "medium"
        else:
            return "high"
    
    def _analyze_momentum(self, prices: np.ndarray) -> str:
        """分析动量"""
        if len(prices) < 20:
            return "moderate"
        
        # RSI-like计算
        returns = np.diff(prices)
        gains = np.sum(returns[returns > 0])
        losses = abs(np.sum(returns[returns < 0]))
        
        if losses == 0:
            return "strong"
        
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        
        if rsi < 30:
            return "weak"
        elif rsi < 70:
            return "moderate"
        else:
            return "strong"
    
    def _determine_phase(
        self,
        dci: float,
        spectral_width: float,
        vortex_score: Optional[float],
        resonance_confidence: Optional[float],
        trend_direction: str,
        trend_strength: float,
        momentum_level: str
    ) -> Tuple[Phase, PhaseConfidence]:
        """
        综合判断相位
        
        优先级：
        1. 随机共振触发 -> C
        2. 涡旋成熟 -> B
        3. 强趋势 -> D
        4. 高噪声 -> A
        """
        confidence = PhaseConfidence()
        
        # 计算各指标贡献
        # DCI贡献
        if dci > self.thresholds.dci_high:
            confidence.dci_contribution = min(1.0, (dci - self.thresholds.dci_high) / 0.15 + 0.5)
        elif dci < self.thresholds.dci_low:
            confidence.dci_contribution = max(0.0, 1.0 - (self.thresholds.dci_low - dci) / 0.1)
        else:
            confidence.dci_contribution = 0.5
        
        # 谱宽贡献
        if spectral_width < self.thresholds.spectral_width_low:
            confidence.spectral_contribution = 0.8  # 低谱宽有利于涡旋
        elif spectral_width > self.thresholds.spectral_width_high:
            confidence.spectral_contribution = 0.9  # 高谱宽表示混乱
        else:
            confidence.spectral_contribution = 0.5
        
        # 涡旋贡献
        if vortex_score is not None:
            if vortex_score >= self.thresholds.vortex_mature_score:
                confidence.vortex_contribution = 1.0
            elif vortex_score >= self.thresholds.vortex_min_score:
                confidence.vortex_contribution = 0.7
            else:
                confidence.vortex_contribution = 0.2
        else:
            confidence.vortex_contribution = 0.3
        
        # 共振贡献
        if resonance_confidence is not None:
            confidence.resonance_contribution = resonance_confidence
        else:
            confidence.resonance_contribution = 0.2
        
        # 动量贡献
        momentum_map = {"weak": 0.2, "moderate": 0.5, "strong": 0.8}
        confidence.momentum_contribution = momentum_map.get(momentum_level, 0.5)
        
        # 相位判断
        phase_scores = {
            Phase.NOISE: 0.0,
            Phase.VORTEX: 0.0,
            Phase.CRITICAL: 0.0,
            Phase.TREND: 0.0,
        }
        
        # 随机共振 -> C
        if resonance_confidence and resonance_confidence >= self.thresholds.resonance_confidence_min:
            phase_scores[Phase.CRITICAL] += confidence.resonance_contribution * 1.5
            confidence.primary = resonance_confidence
        
        # 涡旋成熟 -> B
        if vortex_score and vortex_score >= self.thresholds.vortex_min_score:
            phase_scores[Phase.VORTEX] += confidence.vortex_contribution * 1.2
            if confidence.primary == 0:
                confidence.primary = confidence.vortex_contribution
        
        # 谱宽高 -> A
        if spectral_width > self.thresholds.spectral_width_high:
            phase_scores[Phase.NOISE] += confidence.spectral_contribution * 1.0
        
        # DCI高 + 趋势 -> D
        if dci > self.thresholds.dci_high and trend_direction != "neutral":
            phase_scores[Phase.TREND] += confidence.dci_contribution * trend_strength * 1.3
            if confidence.primary == 0:
                confidence.primary = confidence.dci_contribution * trend_strength
        
        # 低DCI -> A
        if dci < self.thresholds.dci_low:
            phase_scores[Phase.NOISE] += confidence.dci_contribution * 1.0
        
        # 中等DCI + 低谱宽 -> B
        if self.thresholds.dci_low <= dci <= self.thresholds.dci_high:
            if spectral_width < self.thresholds.spectral_width_low:
                phase_scores[Phase.VORTEX] += 0.5
        
        # 选择得分最高的相位
        best_phase = max(phase_scores, key=phase_scores.get)
        confidence.secondary = max(phase_scores.values())
        confidence.combined = (confidence.primary + confidence.secondary) / 2
        
        # 特殊处理：涡旋成熟直接到B
        if vortex_score and vortex_score >= self.thresholds.vortex_mature_score:
            best_phase = Phase.VORTEX
        
        return best_phase, confidence
    
    def _update_history(self, phase: Phase):
        """更新历史记录"""
        self.phase_history.append(phase)
        self.phase_timestamps.append(datetime.now().isoformat())
        self.phase_counts[phase] += 1
        
        # 保持历史长度
        if len(self.phase_history) > 100:
            self.phase_history = self.phase_history[-100:]
            self.phase_timestamps = self.phase_timestamps[-100:]
        
        # 更新趋势持续时间
        if phase == Phase.TREND:
            self.current_trend_duration += 1
        else:
            self.current_trend_duration = 0
    
    def _detect_transition_warning(
        self,
        current_phase: Phase,
        confidence: PhaseConfidence
    ) -> Optional[PhaseTransitionWarning]:
        """检测相位转换预警"""
        if confidence.combined < 0.6:
            return None
        
        # 相位转换映射
        next_phases = {
            Phase.NOISE: Phase.VORTEX,      # 混乱后可能进入涡旋
            Phase.VORTEX: Phase.CRITICAL,   # 涡旋成熟进入临界
            Phase.CRITICAL: Phase.TREND,    # 临界后突破
            Phase.TREND: Phase.NOISE,        # 趋势结束回归混乱
        }
        
        likely_next = next_phases[current_phase]
        
        # 估算转换时间
        if confidence.combined > 0.8:
            time_remaining = 5  # 高置信度，转换可能很快
        elif confidence.combined > 0.6:
            time_remaining = 15
        else:
            time_remaining = 30
        
        # 构建预警
        warning = PhaseTransitionWarning(
            current_phase=current_phase,
            likely_next_phase=likely_next,
            confidence=confidence.combined,
            time_remaining=time_remaining,
            indicators={
                'dci': confidence.dci_contribution,
                'spectral': confidence.spectral_contribution,
                'vortex': confidence.vortex_contribution,
                'resonance': confidence.resonance_contribution,
            }
        )
        
        return warning
    
    def get_phase_distribution(self) -> Dict[str, float]:
        """获取相位分布"""
        total = sum(self.phase_counts.values())
        if total == 0:
            return {p.value: 0.0 for p in Phase}
        
        return {p.value: self.phase_counts[p] / total for p in Phase}
    
    def get_recent_phases(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最近的相位历史"""
        result = []
        for i, (phase, timestamp) in enumerate(zip(
            self.phase_history[-n:],
            self.phase_timestamps[-n:]
        )):
            result.append({
                'index': len(self.phase_history) - n + i,
                'phase': phase.value,
                'phase_name': self.PHASE_NAMES[phase],
                'timestamp': timestamp,
            })
        return result
    
    def reset(self):
        """重置检测器"""
        self.phase_history.clear()
        self.phase_timestamps.clear()
        self.phase_counts = {p: 0 for p in Phase}
        self.current_trend_duration = 0


# ============================================================================
# 便捷函数
# ============================================================================

def detect_phase(
    prices: List[float],
    volumes: Optional[List[float]] = None,
    dci: Optional[float] = None,
    spectral_width: Optional[float] = None,
    vortex_score: Optional[float] = None,
    resonance_confidence: Optional[float] = None,
) -> PhaseAnalysisResult:
    """
    便捷函数：检测市场相位
    
    Args:
        prices: 价格序列
        volumes: 成交量序列
        dci: DCI值
        spectral_width: 谱宽
        vortex_score: 涡旋成熟度
        resonance_confidence: 共振置信度
        
    Returns:
        PhaseAnalysisResult
    """
    detector = EnhancedPhaseDetector()
    return detector.analyze(
        np.array(prices),
        np.array(volumes) if volumes else None,
        dci, spectral_width, vortex_score, resonance_confidence
    )


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("=" * 60)
    print("增强四相位检测器 - 测试")
    print("=" * 60)
    
    # 生成测试数据
    np.random.seed(42)
    
    # 相位A：混乱
    prices_a = 50000 + 1000 * np.random.randn(200)
    
    # 相位B：涡旋（低波动）
    t = np.linspace(0, 10, 200)
    prices_b = 50000 + 500 * np.sin(0.3 * t) + 100 * np.random.randn(200)
    
    # 相位C：临界（收敛）
    prices_c = 50000 + 200 * np.linspace(-1, 1, 200) + 50 * np.random.randn(200)
    
    # 相位D：趋势
    prices_d = 50000 + np.cumsum(100 + 50 * np.random.randn(200))
    
    detector = EnhancedPhaseDetector()
    
    test_cases = [
        ("相位A - 混乱", prices_a),
        ("相位B - 涡旋", prices_b),
        ("相位C - 临界", prices_c),
        ("相位D - 趋势", prices_d),
    ]
    
    print("\n[1] 相位检测测试")
    print("-" * 60)
    
    for name, prices in test_cases:
        result = detector.analyze(prices)
        print(f"\n{name}:")
        print(f"  检测结果: [{result.phase.value}] {result.phase_name}")
        print(f"  置信度: {result.confidence.combined:.1%}")
        print(f"  DCI: {result.dci_value:.3f}")
        print(f"  谱宽: {result.spectral_width:.6f}")
        print(f"  策略: {result.strategy_text[:30]}...")
    
    print("\n[2] 相位分布统计")
    print("-" * 60)
    dist = detector.get_phase_distribution()
    for phase, ratio in dist.items():
        print(f"  {phase}: {ratio:.1%}")
    
    print("\n[3] 综合市场分析")
    print("-" * 60)
    
    # 模拟综合分析
    mixed_prices = np.concatenate([
        prices_a[:50],
        prices_b[50:100],
        prices_c[100:150],
        prices_d[150:]
    ])
    
    result = detector.analyze(mixed_prices)
    print(f"综合分析:")
    print(f"  相位: [{result.phase.value}] {result.phase_name}")
    print(f"  置信度: {result.confidence.combined:.1%}")
    print(f"  趋势: {result.trend_direction} (强度: {result.trend_strength:.1%})")
    print(f"  波动率: {result.volatility_level}")
    print(f"  动量: {result.momentum_level}")
    print(f"  仓位上限: {result.max_position:.0%}")
    print(f"  策略: {result.strategy_text}")
    
    if result.transition_warning:
        print(f"\n  预警:")
        print(f"    可能转换: {result.transition_warning.likely_next_phase.value}")
        print(f"    置信度: {result.transition_warning.confidence:.1%}")
        print(f"    预计时间: {result.transition_warning.time_remaining}根K线")
    
    print("\n✅ 测试完成")
    print("=" * 60)
