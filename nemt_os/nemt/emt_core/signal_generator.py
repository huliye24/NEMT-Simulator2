"""
交易信号生成器 (Signal Generator)
基于 NEMT 分析结果生成可交易的信号
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SignalType(Enum):
    """信号类型"""
    VORTEX_BREAKOUT = "vortex_breakout"      # 涡旋突破
    RESONANCE_TRIGGER = "resonance_trigger"   # 共振触发
    TREND_CALLBACK = "trend_callback"         # 趋势回调
    PHASE_TRANSITION = "phase_transition"     # 相位转换
    NOISE_SIGNAL = "noise_signal"             # 噪声信号


class SignalDirection(Enum):
    """信号方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TradingSignal:
    """交易信号"""
    signal_id: str
    signal_type: SignalType
    direction: SignalDirection
    confidence: float  # 0-1
    strength: float   # 0-100
    reason: str
    price: float
    phase: str
    metadata: Dict[str, Any]
    timestamp: str
    
    @classmethod
    def create(
        cls,
        signal_type: SignalType,
        direction: SignalDirection,
        confidence: float,
        reason: str,
        price: float,
        phase: str,
        strength: float = 50.0,
        metadata: Dict[str, Any] = None
    ) -> 'TradingSignal':
        return cls(
            signal_id=str(uuid.uuid4())[:8],
            signal_type=signal_type,
            direction=direction,
            confidence=confidence,
            strength=strength,
            reason=reason,
            price=price,
            phase=phase,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'signal_type': self.signal_type.value,
            'direction': self.direction.value,
            'confidence': self.confidence,
            'strength': self.strength,
            'reason': self.reason,
            'price': self.price,
            'phase': self.phase,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class SignalGenerator:
    """
    信号生成器
    
    基于 NEMT 分析结果生成交易信号
    """
    
    def __init__(self):
        self.signal_history: List[TradingSignal] = []
    
    def generate_vortex_breakout(
        self,
        phase: str,
        spectral_width: float,
        coherence: float,
        price: float,
        prev_price: float
    ) -> Optional[TradingSignal]:
        """
        生成涡旋突破信号
        
        当市场从高谱宽向低谱宽转变时触发
        """
        if phase != "PHASE_B_VORTEX":
            return None
        
        # 检测突破方向
        if price > prev_price * 1.005:  # 5% 涨幅
            direction = SignalDirection.BULLISH
            reason = f"涡旋突破: 价格上涨 {((price - prev_price) / prev_price * 100):.2f}%, 谱宽 {spectral_width:.4f}"
        elif price < prev_price * 0.995:  # 5% 跌幅
            direction = SignalDirection.BEARISH
            reason = f"涡旋突破: 价格下跌 {((prev_price - price) / prev_price * 100):.2f}%, 谱宽 {spectral_width:.4f}"
        else:
            return None
        
        # 计算置信度
        confidence = min(0.9, 0.5 + coherence * 0.3 + (1 - spectral_width / 0.03) * 0.2)
        
        return TradingSignal.create(
            signal_type=SignalType.VORTEX_BREAKOUT,
            direction=direction,
            confidence=confidence,
            reason=reason,
            price=price,
            phase=phase,
            strength=60 + confidence * 40,
            metadata={
                'spectral_width': spectral_width,
                'coherence': coherence
            }
        )
    
    def generate_resonance_trigger(
        self,
        phase: str,
        resonance_peaks: int,
        spectral_width: float,
        price: float
    ) -> Optional[TradingSignal]:
        """
        生成共振触发信号
        
        当检测到多个共振峰且谱宽较低时触发
        """
        if phase != "PHASE_C_RESONANCE":
            return None
        
        if resonance_peaks < 2:
            return None
        
        # spectral width lower -> stronger signal
        # when sw=0.015, factor=0; when sw=0, factor=1
        strength_factor = max(0, min(1, 1 - spectral_width / 0.02))
        
        if strength_factor > 0.2:
            direction = SignalDirection.BULLISH  # 默认看涨
            reason = f"共振触发: 检测到 {resonance_peaks} 个共振峰, 谱宽 {spectral_width:.4f}"
            
            confidence = min(0.95, 0.6 + resonance_peaks * 0.1 + strength_factor * 0.2)
            
            return TradingSignal.create(
                signal_type=SignalType.RESONANCE_TRIGGER,
                direction=direction,
                confidence=confidence,
                reason=reason,
                price=price,
                phase=phase,
                strength=70 + confidence * 30,
                metadata={
                    'resonance_peaks': resonance_peaks,
                    'spectral_width': spectral_width
                }
            )
        
        return None
    
    def generate_trend_callback(
        self,
        phase: str,
        spectral_width: float,
        coherence: float,
        price: float,
        trend_price: float
    ) -> Optional[TradingSignal]:
        """
        生成趋势回调信号
        
        在趋势稳定期(Phase D)，价格偏离趋势时触发
        """
        if phase != "PHASE_D_TREND":
            return None
        
        # 价格偏离趋势
        deviation = (price - trend_price) / trend_price
        
        if abs(deviation) < 0.02:  # 偏离小于2%
            return None
        
        if deviation < -0.02:  # 价格低于趋势，看涨回调
            direction = SignalDirection.BULLISH
            reason = f"趋势回调: 价格低于趋势 {abs(deviation) * 100:.2f}%, 相干性 {coherence:.2f}"
        else:  # 价格高于趋势，看跌回调
            direction = SignalDirection.BEARISH
            reason = f"趋势回调: 价格高于趋势 {deviation * 100:.2f}%, 相干性 {coherence:.2f}"
        
        confidence = min(0.9, coherence * 0.7 + (1 - abs(deviation)) * 0.3)
        
        return TradingSignal.create(
            signal_type=SignalType.TREND_CALLBACK,
            direction=direction,
            confidence=confidence,
            reason=reason,
            price=price,
            phase=phase,
            strength=50 + confidence * 50,
            metadata={
                'spectral_width': spectral_width,
                'coherence': coherence,
                'deviation': deviation
            }
        )
    
    def generate_phase_transition(
        self,
        prev_phase: str,
        current_phase: str,
        confidence: float,
        price: float
    ) -> Optional[TradingSignal]:
        """
        生成相位转换信号
        
        当市场从一个相位转换到另一个相位时触发
        """
        if prev_phase == current_phase:
            return None
        
        # 相位转换的信号强度
        phase_signal_strength = {
            ('PHASE_A_NOISE', 'PHASE_B_VORTEX'): (SignalDirection.NEUTRAL, 40),
            ('PHASE_B_VORTEX', 'PHASE_C_RESONANCE'): (SignalDirection.BULLISH, 70),
            ('PHASE_C_RESONANCE', 'PHASE_D_TREND'): (SignalDirection.BULLISH, 80),
            ('PHASE_D_TREND', 'PHASE_C_RESONANCE'): (SignalDirection.NEUTRAL, 50),
            ('PHASE_C_RESONANCE', 'PHASE_B_VORTEX'): (SignalDirection.NEUTRAL, 40),
            ('PHASE_B_VORTEX', 'PHASE_A_NOISE'): (SignalDirection.NEUTRAL, 30),
        }
        
        key = (prev_phase, current_phase)
        if key in phase_signal_strength:
            direction, base_strength = phase_signal_strength[key]
            reason = f"相位转换: {prev_phase} -> {current_phase}"
            
            return TradingSignal.create(
                signal_type=SignalType.PHASE_TRANSITION,
                direction=direction,
                confidence=confidence,
                reason=reason,
                price=price,
                phase=current_phase,
                strength=base_strength + confidence * 20,
                metadata={
                    'prev_phase': prev_phase,
                    'current_phase': current_phase
                }
            )
        
        return None
    
    def generate_noise_signal(
        self,
        phase: str,
        spectral_width: float,
        price: float
    ) -> Optional[TradingSignal]:
        """
        生成噪声信号
        
        在高谱宽期发出警告信号
        """
        if phase != "PHASE_A_NOISE":
            return None
        
        if spectral_width > 0.03:
            return TradingSignal.create(
                signal_type=SignalType.NOISE_SIGNAL,
                direction=SignalDirection.NEUTRAL,
                confidence=0.9,
                reason=f"高噪声警告: 谱宽 {spectral_width:.4f}, 建议观望",
                price=price,
                phase=phase,
                strength=20,
                metadata={'spectral_width': spectral_width}
            )
        
        return None
    
    def generate_all_signals(
        self,
        phase: str,
        prev_phase: str,
        spectral_width: float,
        coherence: float,
        resonance_peaks: int,
        price: float,
        prev_price: float,
        trend_price: float,
        confidence: float
    ) -> List[TradingSignal]:
        """
        生成所有适用的信号
        
        Returns:
            List[TradingSignal]: 信号列表
        """
        signals = []
        
        # 涡旋突破信号
        vortex_signal = self.generate_vortex_breakout(
            phase, spectral_width, coherence, price, prev_price
        )
        if vortex_signal:
            signals.append(vortex_signal)
        
        # 共振触发信号
        resonance_signal = self.generate_resonance_trigger(
            phase, resonance_peaks, spectral_width, price
        )
        if resonance_signal:
            signals.append(resonance_signal)
        
        # 趋势回调信号
        trend_signal = self.generate_trend_callback(
            phase, spectral_width, coherence, price, trend_price
        )
        if trend_signal:
            signals.append(trend_signal)
        
        # 相位转换信号
        transition_signal = self.generate_phase_transition(
            prev_phase, phase, confidence, price
        )
        if transition_signal:
            signals.append(transition_signal)
        
        # 噪声信号
        noise_signal = self.generate_noise_signal(phase, spectral_width, price)
        if noise_signal:
            signals.append(noise_signal)
        
        # 更新历史
        self.signal_history.extend(signals)
        
        # 只保留最近100个信号
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
        
        return signals
    
    def get_latest_signals(self, n: int = 10) -> List[TradingSignal]:
        """获取最近的信号"""
        return self.signal_history[-n:]
    
    def get_signals_by_type(self, signal_type: SignalType) -> List[TradingSignal]:
        """获取指定类型的信号"""
        return [s for s in self.signal_history if s.signal_type == signal_type]
    
    def get_signals_by_direction(self, direction: SignalDirection) -> List[TradingSignal]:
        """获取指定方向的信号"""
        return [s for s in self.signal_history if s.direction == direction]
