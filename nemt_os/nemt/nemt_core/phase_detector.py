"""
四相位检测器 (Phase Detector)
检测市场的四个相位: Noise, Vortex, Resonance, Trend
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


class MarketPhase(Enum):
    """市场相位枚举"""
    PHASE_A_NOISE = "PHASE_A_NOISE"      # 噪声期
    PHASE_B_VORTEX = "PHASE_B_VORTEX"     # 涡旋期
    PHASE_C_RESONANCE = "PHASE_C_RESONANCE"  # 共振期
    PHASE_D_TREND = "PHASE_D_TREND"        # 趋势期


@dataclass
class PhaseResult:
    """相位检测结果"""
    phase: MarketPhase
    confidence: float  # 0-1
    indicators: dict
    description: str


@dataclass
class PhaseStrategy:
    """相位策略配置"""
    name: str
    strategy_text: str
    max_position: float  # 最大仓位
    leverage_allowed: int  # 允许的杠杆
    focus_text: str  # 关注点
    avoid_text: str  # 避免点


# 四相位策略配置
PHASE_STRATEGIES = {
    MarketPhase.PHASE_A_NOISE: PhaseStrategy(
        name="噪声期 (Phase A)",
        strategy_text="低波动观望",
        max_position=0.1,
        leverage_allowed=1,
        focus_text="休息和观察",
        avoid_text="追涨杀跌"
    ),
    MarketPhase.PHASE_B_VORTEX: PhaseStrategy(
        name="涡旋期 (Phase B)",
        strategy_text="区间震荡操作",
        max_position=0.3,
        leverage_allowed=2,
        focus_text="支撑阻力位",
        avoid_text="突破追单"
    ),
    MarketPhase.PHASE_C_RESONANCE: PhaseStrategy(
        name="共振期 (Phase C)",
        strategy_text="趋势确认做单",
        max_position=0.6,
        leverage_allowed=3,
        focus_text="趋势方向",
        avoid_text="逆势操作"
    ),
    MarketPhase.PHASE_D_TREND: PhaseStrategy(
        name="趋势期 (Phase D)",
        strategy_text="趋势持有",
        max_position=1.0,
        leverage_allowed=5,
        focus_text="移动止损",
        avoid_text="过早止盈"
    )
}


class PhaseDetector:
    """
    四相位检测器
    
    基于 NEMT 理论，检测市场的四个相位：
    1. Phase A (Noise): 高谱宽，低相干性，混沌状态
    2. Phase B (Vortex): 中等谱宽，开始有序化
    3. Phase C (Resonance): 低谱宽，高相干性，周期信号
    4. Phase D (Trend): 极低谱宽，趋势稳定
    """
    
    def __init__(
        self,
        noise_threshold: float = 0.025,
        vortex_threshold: float = 0.020,
        resonance_threshold: float = 0.015
    ):
        """
        Args:
            noise_threshold: 噪声期阈值 (谱宽 > 此值为噪声)
            vortex_threshold: 涡旋期阈值
            resonance_threshold: 共振期阈值 (谱宽 < 此值为趋势)
        """
        self.noise_threshold = noise_threshold
        self.vortex_threshold = vortex_threshold
        self.resonance_threshold = resonance_threshold
    
    def detect(
        self,
        spectral_width: float,
        resonance_peaks: int = 0,
        volatility: float = 0.0,
        trend_strength: float = 0.0
    ) -> PhaseResult:
        """
        检测当前相位
        
        Args:
            spectral_width: 谱宽值
            resonance_peaks: 共振峰数量
            volatility: 波动率
            trend_strength: 趋势强度 (-1 到 1)
            
        Returns:
            PhaseResult: 检测结果
        """
        indicators = {
            'spectral_width': spectral_width,
            'resonance_peaks': resonance_peaks,
            'volatility': volatility,
            'trend_strength': trend_strength
        }
        
        # 根据谱宽判断相位
        if spectral_width > self.noise_threshold:
            # Phase A: 噪声期
            phase = MarketPhase.PHASE_A_NOISE
            confidence = min(1.0, (spectral_width - self.noise_threshold) / 0.01 + 0.5)
            description = f"高谱宽 {spectral_width:.4f}，市场处于混沌状态"
        
        elif spectral_width > self.vortex_threshold:
            # Phase B: 涡旋期
            phase = MarketPhase.PHASE_B_VORTEX
            confidence = min(1.0, 0.6 + (spectral_width - self.vortex_threshold) / 0.005)
            description = f"中等谱宽 {spectral_width:.4f}，市场开始有序化"
        
        elif spectral_width > self.resonance_threshold:
            # Phase C: 共振期
            phase = MarketPhase.PHASE_C_RESONANCE
            confidence = min(1.0, 0.7 + resonance_peaks * 0.05)
            description = f"低谱宽 {spectral_width:.4f}，共振峰 {resonance_peaks} 个，趋势形成中"
        
        else:
            # Phase D: 趋势期
            phase = MarketPhase.PHASE_D_TREND
            confidence = min(1.0, 0.8 + abs(trend_strength) * 0.2)
            description = f"极低谱宽 {spectral_width:.4f}，趋势稳定"
        
        # 根据共振峰数量调整置信度
        if resonance_peaks > 3:
            confidence = min(1.0, confidence + 0.1)
        
        return PhaseResult(
            phase=phase,
            confidence=float(confidence),
            indicators=indicators,
            description=description
        )
    
    def detect_from_experiment(self, experiment_result: dict) -> PhaseResult:
        """
        从实验结果检测相位
        
        Args:
            experiment_result: NLS 实验结果
            
        Returns:
            PhaseResult: 检测结果
        """
        spectral_width = experiment_result.get('spectral_width', 0.02)
        resonance = experiment_result.get('resonance', {})
        resonance_peaks = resonance.get('num_peaks', 0)
        
        return self.detect(
            spectral_width=spectral_width,
            resonance_peaks=resonance_peaks,
            volatility=experiment_result.get('volatility', 0.0),
            trend_strength=experiment_result.get('trend_strength', 0.0)
        )
    
    def get_phase_strategy(self, phase: MarketPhase) -> PhaseStrategy:
        """获取相位对应的策略配置"""
        return PHASE_STRATEGIES.get(phase, PHASE_STRATEGIES[MarketPhase.PHASE_A_NOISE])
    
    def get_recommended_position(
        self,
        phase: MarketPhase,
        base_position: float = 0.5
    ) -> float:
        """
        根据相位获取建议仓位
        
        Args:
            phase: 市场相位
            base_position: 基础仓位
            
        Returns:
            float: 建议仓位 (0-1)
        """
        strategy = self.get_phase_strategy(phase)
        return strategy.max_position * base_position
    
    def get_recommended_leverage(self, phase: MarketPhase) -> int:
        """获取建议杠杆"""
        strategy = self.get_phase_strategy(phase)
        return strategy.leverage_allowed
