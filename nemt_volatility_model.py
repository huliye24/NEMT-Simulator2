"""
NEMT 第十一章：波动性建模
噪声驱动孤子与涡旋-随机共振模型

包含：
1. 孤子模型 - 趋势脉冲的形成和传播
2. 涡旋-随机共振模型 - 相变过程
3. 信号强度评分（SSS）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import math


# =====================
# 波动结构类型
# =====================

class VolatilityStructure(Enum):
    """波动结构类型"""
    NOISE_DOMINATED = "noise_dominated"      # 噪声主导
    VORTEX_FORMING = "vortex_forming"       # 涡旋形成中
    VORTEX_MATURE = "vortex_mature"         # 涡旋成熟
    RESONANCE_TRIGGER = "resonance_trigger"  # 随机共振触发
    SOLITON_TREND = "soliton_trend"          # 孤子趋势
    TREND_EXHAUSTING = "trend_exhausting"    # 趋势耗尽


# =====================
# 孤子模型
# =====================

@dataclass
class SolitonIndicators:
    """孤子指标"""
    max_retracement_pct: float       # 最大回调百分比
    retracement_volume_ratio: float   # 回调成交量/上涨成交量
    oi_change_pct: float              # OI变化百分比
    oi_retracement_pct: float         # OI回落比例
    dci_sustained_days: int           # DCI持续天数
    dci_min_value: float              # DCI最低值
    is_soliton: bool                  # 是否为孤子结构
    confidence: float                  # 置信度 0-1


@dataclass
class SolitonDecaySignal:
    """孤子衰减信号"""
    is_decaying: bool
    decay_stage: str  # "healthy", "warning", "critical"
    indicators: List[str]
    recommended_action: str


class SolitonModel:
    """
    孤子模型

    用于识别和跟踪趋势脉冲（孤子结构）
    """

    # 孤子结构阈值
    MAX_RETRACEMENT_SOLITON = 0.08      # 孤子最大回调8%
    VOLUME_RATIO_SOLITON = 0.40         # 回调成交量/上涨成交量上限
    OI_RETRACEMENT_SOLITON = 0.05       # OI回落上限5%
    DCI_MIN_SOLITON = 0.70              # DCI最低要求
    DCI_SUSTAINED_DAYS = 7              # DCI持续天数要求

    # 衰减警告阈值
    RETRACEMENT_WARNING = 0.12          # 回调>12%警告
    RETRACEMENT_CRITICAL = 0.15         # 回调>15%严重
    VOLUME_RATIO_WARNING = 0.60         # 成交量比>60%警告
    OI_RETRACEMENT_WARNING = 0.10        # OI回落>10%警告

    def analyze(
        self,
        price_high: float,
        price_low_retracement: float,
        up_volume_avg: float,
        down_volume_avg: float,
        oi_start: float,
        oi_current: float,
        oi_retracement_low: Optional[float] = None,
        dci_values: List[float] = None
    ) -> SolitonIndicators:
        """
        分析孤子结构

        Args:
            price_high: 上涨期间最高价
            price_low_retracement: 回落的最低价
            up_volume_avg: 上涨K线平均成交量
            down_volume_avg: 回调K线平均成交量
            oi_start: 起始OI
            oi_current: 当前OI
            oi_retracement_low: 回落后OI最低点
            dci_values: DCI历史值列表
        """
        # 计算最大回调
        max_retracement = (price_high - price_low_retracement) / price_high

        # 成交量比
        volume_ratio = down_volume_avg / up_volume_avg if up_volume_avg > 0 else 1.0

        # OI变化
        oi_change = (oi_current - oi_start) / oi_start if oi_start > 0 else 0
        oi_retracement = 0.0
        if oi_retracement_low is not None and oi_start > 0:
            oi_retracement = (oi_start - oi_retracement_low) / oi_start

        # DCI分析
        dci_min = 0.0
        dci_sustained = 0
        if dci_values:
            dci_min = min(dci_values)
            dci_sustained = len([d for d in dci_values if d >= self.DCI_MIN_SOLITON])

        # 判断是否为孤子
        is_soliton = (
            max_retracement <= self.MAX_RETRACEMENT_SOLITON and
            volume_ratio <= self.VOLUME_RATIO_SOLITON and
            oi_retracement <= self.OI_RETRACEMENT_SOLITON and
            dci_min >= self.DCI_MIN_SOLITON and
            dci_sustained >= self.DCI_SUSTAINED_DAYS
        )

        # 计算置信度
        confidence = self._calculate_confidence(
            max_retracement, volume_ratio, oi_retracement, dci_min, dci_sustained
        )

        return SolitonIndicators(
            max_retracement_pct=max_retracement * 100,
            retracement_volume_ratio=volume_ratio,
            oi_change_pct=oi_change * 100,
            oi_retracement_pct=oi_retracement * 100,
            dci_sustained_days=dci_sustained,
            dci_min_value=dci_min,
            is_soliton=is_soliton,
            confidence=confidence
        )

    def _calculate_confidence(
        self,
        retracement: float,
        volume_ratio: float,
        oi_retracement: float,
        dci_min: float,
        dci_sustained: int
    ) -> float:
        """计算置信度"""
        score = 1.0

        # 回调扣分
        if retracement > self.MAX_RETRACEMENT_SOLITON:
            score -= min(0.3, (retracement - self.MAX_RETRACEMENT_SOLITON) * 5)

        # 成交量比扣分
        if volume_ratio > self.VOLUME_RATIO_SOLITON:
            score -= min(0.2, (volume_ratio - self.VOLUME_RATIO_SOLITON) * 2)

        # OI回落扣分
        if oi_retracement > self.OI_RETRACEMENT_SOLITON:
            score -= min(0.2, (oi_retracement - self.OI_RETRACEMENT_SOLITON) * 5)

        # DCI加分
        if dci_min >= self.DCI_MIN_SOLITON:
            score += 0.1
        if dci_sustained >= self.DCI_SUSTAINED_DAYS:
            score += 0.1

        return max(0, min(1, score))

    def check_decay(
        self,
        soliton_indicators: SolitonIndicators,
        current_retracement: float,
        current_volume_ratio: float,
        current_oi_retracement: float,
        dci_current: float,
        dci_trend: str  # "rising", "falling", "stable"
    ) -> SolitonDecaySignal:
        """
        检查孤子是否正在衰减
        """
        indicators = []
        is_decaying = False
        decay_stage = "healthy"

        # 检查回调深度
        if current_retracement > self.RETRACEMENT_CRITICAL:
            indicators.append(f"回调深度{current_retracement:.1%}超过15%，严重警告")
            is_decaying = True
            decay_stage = "critical"
        elif current_retracement > self.RETRACEMENT_WARNING:
            indicators.append(f"回调深度{current_retracement:.1%}超过12%，开始警告")
            is_decaying = True
            decay_stage = "warning"

        # 检查成交量
        if current_volume_ratio > self.VOLUME_RATIO_WARNING:
            indicators.append(f"回调成交量比{current_volume_ratio:.1%}超过60%，抛压增加")

        # 检查OI回落
        if current_oi_retracement > self.OI_RETRACEMENT_WARNING:
            indicators.append(f"OI回落{current_oi_retracement:.1%}超过10%，多头平仓")

        # 检查DCI
        if dci_current < soliton_indicators.dci_min_value * 0.9:
            indicators.append(f"DCI从{soliton_indicators.dci_min_value:.2f}下降至{dci_current:.2f}，趋势动量减弱")
            is_decaying = True
            if decay_stage != "critical":
                decay_stage = "warning"

        if dci_trend == "falling":
            indicators.append("DCI呈下降趋势")

        # 生成建议
        if decay_stage == "critical":
            action = "立即减仓50%，止损上移至保本价"
        elif decay_stage == "warning":
            action = "减仓30%，收紧止损，等待企稳"
        else:
            action = "持仓不动，回调是加仓机会"

        return SolitonDecaySignal(
            is_decaying=is_decaying,
            decay_stage=decay_stage,
            indicators=indicators,
            recommended_action=action
        )

    def get_trading_implications(self) -> Dict[str, str]:
        """获取孤子模型交易含义"""
        return {
            "soliton_identified": "最大的风险是过早下车，回调是加仓机会",
            "during_trend": "回调K线成交量平均为上涨K线的35%以内是健康信号",
            "ending_signals": "回调变深、DCI下降、OI萎缩是孤子衰减的先兆",
            "after_decay": "孤子衰减后进入高噪声或涡旋阶段，降低仓位等待下一个结构"
        }


# =====================
# 涡旋-随机共振模型
# =====================

@dataclass
class VortexResonancePhase:
    """涡旋-随机共振阶段"""
    phase: VolatilityStructure
    name: str
    math_description: str
    market_description: str
    nemt_action: str


@dataclass
class ResonanceParameters:
    """共振参数"""
    barrier_proxy: float          # 势垒高度代理变量
    noise_intensity: float         # 噪声强度代理变量
    cycle_signal_strength: float   # 周期信号强度
    breakthrough_probability: float  # 突破概率


class VortexResonanceModel:
    """
    涡旋-随机共振模型

    描述涡旋蓄力、随机共振触发、趋势爆发的完整相变过程
    """

    def __init__(self):
        self.soliton_model = SolitonModel()

    def get_phases(self) -> List[VortexResonancePhase]:
        """获取四个阶段的定义"""
        return [
            VortexResonancePhase(
                phase=VolatilityStructure.VORTEX_FORMING,
                name="势垒形成",
                math_description="V(x)的两个势阱深度适中，势垒较高",
                market_description="价格在窄区间内运行，波动率锥收窄，多空对峙",
                nemt_action="涡旋条件开始满足，成熟度<5，不入场"
            ),
            VortexResonancePhase(
                phase=VolatilityStructure.VORTEX_MATURE,
                name="势垒降低",
                math_description="随着时间推移和OI积累，势垒逐渐降低",
                market_description="区间内波动更加频繁，假突破开始出现",
                nemt_action="涡旋成熟度5-15，进入最佳交易准备状态"
            ),
            VortexResonancePhase(
                phase=VolatilityStructure.RESONANCE_TRIGGER,
                name="随机共振触发",
                math_description="σ（噪声强度）与势垒高度匹配，A（宏观信号）被放大",
                market_description="突破K线出现，量能放大，OI跟随",
                nemt_action="突破确认条件满足，执行入场"
            ),
            VortexResonancePhase(
                phase=VolatilityStructure.SOLITON_TREND,
                name="势垒消失",
                math_description="系统逃逸出双势阱，进入单边运动",
                market_description="孤子结构形成，趋势持续",
                nemt_action="相位D，持仓为主，回调加仓"
            )
        ]

    def estimate_barrier_proxy(
        self,
        bbw: float,      #布林带宽度
        atr: float,       #ATR值
        price: float     #当前价格
    ) -> float:
        """
        估计势垒高度代理变量

        公式: BBW(20,2) / (ATR(14) / 价格)
        当比值低于0.3时，势垒已经很低，突破概率大增
        """
        if price <= 0 or atr <= 0:
            return 1.0

        normalized_atr = atr / price
        if normalized_atr <= 0:
            return 1.0

        return bbw / normalized_atr

    def estimate_noise_intensity(self, dci_std_20: float) -> float:
        """
        估计噪声强度

        DCI的20日标准差在0.08-0.15之间时，噪声强度处于随机共振的最佳区间
        """
        return dci_std_20

    def estimate_cycle_signal(self, macro_score: float, onchain_score: float) -> float:
        """
        估计周期信号强度

        将宏观评分和链上评分归一化到0-1区间
        """
        # 归一化到0-10范围
        macro_normalized = min(10, max(0, macro_score)) / 10
        onchain_normalized = min(10, max(0, onchain_score)) / 10

        # 取平均
        return (macro_normalized + onchain_normalized) / 2

    def calculate_breakthrough_probability(
        self,
        barrier_proxy: float,
        noise_intensity: float,
        cycle_signal: float
    ) -> float:
        """
        计算突破概率

        公式:
        P(突破) ≈ 1 / (1 + exp((势垒代理 - 0.3) / 0.1)) × 噪声匹配因子
        """
        # 势垒因子
        try:
            barrier_factor = 1 / (1 + math.exp((barrier_proxy - 0.3) / 0.1))
        except:
            barrier_factor = 0.5

        # 噪声匹配因子
        # DCI波动率在0.08-0.15时最佳
        if 0.08 <= noise_intensity <= 0.15:
            noise_factor = 1.0
        elif noise_intensity < 0.08:
            noise_factor = noise_intensity / 0.08
        else:
            noise_factor = max(0.3, 1 - (noise_intensity - 0.15) / 0.15)

        # 周期信号加成
        signal_factor = 0.5 + 0.5 * cycle_signal

        # 综合概率
        probability = barrier_factor * noise_factor * signal_factor

        return max(0, min(1, probability))

    def get_resonance_parameters(
        self,
        bbw: float,
        atr: float,
        price: float,
        dci_std_20: float,
        macro_score: float,
        onchain_score: float
    ) -> ResonanceParameters:
        """
        获取完整的共振参数
        """
        barrier = self.estimate_barrier_proxy(bbw, atr, price)
        noise = self.estimate_noise_intensity(dci_std_20)
        cycle = self.estimate_cycle_signal(macro_score, onchain_score)
        prob = self.calculate_breakthrough_probability(barrier, noise, cycle)

        return ResonanceParameters(
            barrier_proxy=barrier,
            noise_intensity=noise,
            cycle_signal_strength=cycle,
            breakthrough_probability=prob
        )

    def determine_phase(
        self,
        vortex_maturity: int,
        barrier_proxy: float,
        noise_intensity: float,
        has_breakout: bool
    ) -> VortexResonancePhase:
        """
        确定当前相位
        """
        phases = {p.phase: p for p in self.get_phases()}

        # 检查是否突破
        if has_breakout:
            return phases[VolatilityStructure.SOLITON_TREND]

        # 根据成熟度和势垒判断
        if vortex_maturity < 5:
            return phases[VolatilityStructure.VORTEX_FORMING]
        elif vortex_maturity < 15:
            # 检查势垒
            if barrier_proxy < 0.3:
                # 势垒很低，检查噪声是否匹配
                if 0.08 <= noise_intensity <= 0.15:
                    return phases[VolatilityStructure.RESONANCE_TRIGGER]
            return phases[VolatilityStructure.VORTEX_MATURE]
        else:
            # 成熟度过高，可能已经错过
            return phases[VolatilityStructure.RESONANCE_TRIGGER]

    def get_trading_signal(
        self,
        barrier_proxy: float,
        noise_intensity: float,
        cycle_signal: float,
        vortex_maturity: int,
        current_phase: VolatilityStructure
    ) -> Dict:
        """
        生成交易信号
        """
        prob = self.calculate_breakthrough_probability(barrier_proxy, noise_intensity, cycle_signal)

        # 信号强度
        if prob >= 0.7:
            strength = "strong"
            signal = "bullish"
            action = "突破概率高，准备入场"
        elif prob >= 0.4:
            strength = "medium"
            signal = "cautious_bullish"
            action = "概率中等，轻仓试探"
        else:
            strength = "weak"
            signal = "neutral"
            action = "等待信号明确"

        return {
            "breakthrough_probability": prob,
            "strength": strength,
            "signal": signal,
            "action": action,
            "phase": current_phase.value,
            "maturity": vortex_maturity,
            "recommendations": self._get_recommendations(current_phase, vortex_maturity, prob)
        }

    def _get_recommendations(
        self,
        phase: VolatilityStructure,
        maturity: int,
        prob: float
    ) -> List[str]:
        """获取建议"""
        recs = []

        if phase == VolatilityStructure.VORTEX_FORMING:
            recs.append("等待涡旋成熟")
            recs.append("不预判突破方向")
        elif phase == VolatilityStructure.VORTEX_MATURE:
            recs.append("识别边界，预设条件单")
            recs.append("双向挂单，任一方向触发入场")
        elif phase == VolatilityStructure.RESONANCE_TRIGGER:
            recs.append("突破确认后立即执行")
            recs.append("初始仓位可适当放大")
        elif phase == VolatilityStructure.SOLITON_TREND:
            recs.append("持仓为主，回调加仓")
            recs.append("使用移动止损保护利润")

        if maturity > 12:
            recs.append("注意：成熟度偏高，可能已过最佳入场点")

        return recs


# =====================
# 信号强度评分（SSS）
# =====================

@dataclass
class SignalStrengthScore:
    """信号强度评分"""
    total_score: float             # 总分 0-100
    breakthrough_component: float   # 突破概率分量
    soliton_component: float       # 孤子结构分量
    resonance_factor: float        # 共振系数
    strength_label: str           # 强度标签
    interpretation: str           # 解读


class SignalStrengthScorer:
    """
    信号强度评分器

    综合孤子模型和涡旋-随机共振模型
    """

    def __init__(self):
        self.soliton_model = SolitonModel()
        self.resonance_model = VortexResonanceModel()

    def calculate(
        self,
        # 共振参数
        barrier_proxy: float,
        noise_intensity: float,
        cycle_signal: float,

        # 相位和成熟度
        current_phase: VolatilityStructure,
        vortex_maturity: int,

        # 孤子参数
        max_retracement: float = 0.05,
        volume_ratio: float = 0.3,
        oi_retracement: float = 0.03,
        dci_min: float = 0.5,
        dci_sustained_days: int = 7,
        has_soliton_structure: bool = False,
    ) -> SignalStrengthScore:
        """
        计算信号强度评分

        SSS = [w1 × P(突破) + w2 × S(孤子结构)] × 共振系数
        """
        # 突破概率分量
        p_breakthrough = self.resonance_model.calculate_breakthrough_probability(
            barrier_proxy, noise_intensity, cycle_signal
        )

        # 孤子结构分量
        soliton_confidence = self.soliton_model._calculate_confidence(
            max_retracement, volume_ratio, oi_retracement, dci_min, dci_sustained_days
        )
        s_soliton = soliton_confidence if has_soliton_structure else 0.0

        # 权重
        w1 = 0.6  # 突破概率权重
        w2 = 0.4  # 孤子结构权重

        # 共振系数
        if current_phase == VolatilityStructure.RESONANCE_TRIGGER:
            resonance_factor = 1.2  # 随机共振触发，系数加成
        elif current_phase == VolatilityStructure.VORTEX_MATURE:
            resonance_factor = 1.0
        elif current_phase == VolatilityStructure.SOLITON_TREND:
            resonance_factor = 0.8  # 趋势已形成，入场价值降低
        else:
            resonance_factor = 0.5  # 涡旋未成熟

        # 计算总分
        base_score = w1 * p_breakthrough + w2 * s_soliton
        total_score = base_score * resonance_factor * 100  # 转为0-100

        # 强度标签
        if total_score >= 80:
            strength_label = "极强信号"
            interpretation = "多个模型共振，建议重仓"
        elif total_score >= 60:
            strength_label = "强信号"
            interpretation = "突破概率高，可适当加仓"
        elif total_score >= 40:
            strength_label = "中等信号"
            interpretation = "概率中等，建议轻仓"
        elif total_score >= 20:
            strength_label = "弱信号"
            interpretation = "信号不明确，观望为主"
        else:
            strength_label = "无信号"
            interpretation = "放弃本次机会"

        return SignalStrengthScore(
            total_score=total_score,
            breakthrough_component=p_breakthrough * 100,
            soliton_component=s_soliton * 100,
            resonance_factor=resonance_factor,
            strength_label=strength_label,
            interpretation=interpretation
        )

    def get_position_recommendation(self, score: SignalStrengthScore) -> Dict:
        """
        根据评分获取仓位建议
        """
        if score.total_score >= 80:
            return {
                "position_pct": 80,
                "stop_loss_pct": 5,
                "position_type": "full",
                "add_on_dip": True
            }
        elif score.total_score >= 60:
            return {
                "position_pct": 60,
                "stop_loss_pct": 6,
                "position_type": "medium",
                "add_on_dip": True
            }
        elif score.total_score >= 40:
            return {
                "position_pct": 30,
                "stop_loss_pct": 8,
                "position_type": "light",
                "add_on_dip": False
            }
        else:
            return {
                "position_pct": 0,
                "stop_loss_pct": 10,
                "position_type": "none",
                "add_on_dip": False
            }


# =====================
# 综合波动性分析引擎
# =====================

class NEMTVolatilityEngine:
    """
    NEMT 波动性分析引擎

    综合孤子模型和涡旋-随机共振模型
    """

    def __init__(self):
        self.soliton_model = SolitonModel()
        self.resonance_model = VortexResonanceModel()
        self.sss_scorer = SignalStrengthScorer()

    def analyze(
        self,
        # 市场数据
        current_price: float,
        price_high: float,
        price_low_retracement: float,
        atr: float,
        bbw: float,

        # 成交量和OI
        up_volume_avg: float,
        down_volume_avg: float,
        oi_start: float,
        oi_current: float,
        oi_retracement_low: Optional[float] = None,

        # 指标
        dci_values: List[float] = None,
        dci_current: float = 0.5,
        vortex_maturity: int = 0,
        macro_score: float = 5,
        onchain_score: float = 5,

        # 市场状态
        has_breakout: bool = False
    ) -> Dict:
        """
        运行完整波动性分析
        """
        results = {}

        # 1. 孤子分析
        soliton = self.soliton_model.analyze(
            price_high=price_high,
            price_low_retracement=price_low_retracement,
            up_volume_avg=up_volume_avg,
            down_volume_avg=down_volume_avg,
            oi_start=oi_start,
            oi_current=oi_current,
            oi_retracement_low=oi_retracement_low,
            dci_values=dci_values
        )
        results["soliton"] = {
            "is_soliton": soliton.is_soliton,
            "confidence": f"{soliton.confidence:.0%}",
            "max_retracement": f"{soliton.max_retracement_pct:.1f}%",
            "volume_ratio": f"{soliton.retracement_volume_ratio:.1%}",
            "dci_sustained": f"{soliton.dci_sustained_days}天"
        }

        # 2. 共振参数
        if dci_values and len(dci_values) >= 20:
            dci_std_20 = calculate_std(dci_values[-20:])
            # 确保在合理范围
            dci_std_20 = max(0.01, min(0.3, dci_std_20))
        else:
            dci_std_20 = 0.1  # 默认值

        resonance_params = self.resonance_model.get_resonance_parameters(
            bbw=bbw,
            atr=atr,
            price=current_price,
            dci_std_20=dci_std_20,
            macro_score=macro_score,
            onchain_score=onchain_score
        )
        results["resonance"] = {
            "barrier_proxy": f"{resonance_params.barrier_proxy:.3f}",
            "noise_intensity": f"{resonance_params.noise_intensity:.3f}",
            "cycle_signal": f"{resonance_params.cycle_signal_strength:.1%}",
            "breakthrough_probability": f"{resonance_params.breakthrough_probability:.1%}"
        }

        # 3. 确定相位
        current_phase = self.resonance_model.determine_phase(
            vortex_maturity=vortex_maturity,
            barrier_proxy=resonance_params.barrier_proxy,
            noise_intensity=resonance_params.noise_intensity,
            has_breakout=has_breakout
        )
        results["phase"] = {
            "name": current_phase.name,
            "description": current_phase.market_description,
            "action": current_phase.nemt_action
        }

        # 4. 信号强度评分
        dci_min = min(dci_values) if dci_values else 0.5
        dci_sustained = len([d for d in dci_values if d >= 0.70]) if dci_values else 0
        max_retracement = (price_high - price_low_retracement) / price_high
        volume_ratio = down_volume_avg / up_volume_avg if up_volume_avg > 0 else 1.0
        oi_retracement = (oi_start - (oi_retracement_low or oi_start)) / oi_start if oi_start > 0 else 0

        sss = self.sss_scorer.calculate(
            max_retracement=max_retracement,
            volume_ratio=volume_ratio,
            oi_retracement=oi_retracement,
            dci_min=dci_min,
            dci_sustained_days=dci_sustained,
            has_soliton_structure=soliton.is_soliton,
            barrier_proxy=resonance_params.barrier_proxy,
            noise_intensity=resonance_params.noise_intensity,
            cycle_signal=resonance_params.cycle_signal_strength,
            current_phase=current_phase.phase,
            vortex_maturity=vortex_maturity
        )
        results["signal_strength"] = {
            "score": f"{sss.total_score:.0f}/100",
            "label": sss.strength_label,
            "interpretation": sss.interpretation,
            "breakthrough_component": f"{sss.breakthrough_component:.0f}",
            "soliton_component": f"{sss.soliton_component:.0f}"
        }

        # 5. 仓位建议
        position_rec = self.sss_scorer.get_position_recommendation(sss)
        results["position"] = position_rec

        return results


def calculate_std(values: List[float]) -> float:
    """计算标准差"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


# =====================
# 测试
# =====================

if __name__ == "__main__":
    engine = NEMTVolatilityEngine()

    # 模拟2024年2-3月孤子行情
    result = engine.analyze(
        current_price=60000,
        price_high=73000,
        price_low_retracement=67000,  # 回调约8%
        atr=2500,
        bbw=0.04,
        up_volume_avg=1000,
        down_volume_avg=350,  # 成交量比35%
        oi_start=18e9,
        oi_current=32e9,  # OI增长
        oi_retracement_low=31e9,
        dci_values=[0.72] * 28,  # DCI连续28天维持在0.72以上
        dci_current=0.72,
        vortex_maturity=15,
        macro_score=7,
        onchain_score=7,
        has_breakout=True
    )

    print("=" * 70)
    print("NEMT 波动性建模分析报告")
    print("=" * 70)

    print("\n[孤子分析]")
    for key, value in result["soliton"].items():
        print(f"   {key}: {value}")

    print("\n[涡旋-随机共振]")
    for key, value in result["resonance"].items():
        print(f"   {key}: {value}")

    print("\n[当前相位]")
    print(f"   阶段: {result['phase']['name']}")
    print(f"   描述: {result['phase']['description']}")
    print(f"   行动: {result['phase']['action']}")

    print("\n[信号强度评分]")
    print(f"   评分: {result['signal_strength']['score']}")
    print(f"   标签: {result['signal_strength']['label']}")
    print(f"   解读: {result['signal_strength']['interpretation']}")
    print(f"   突破分量: {result['signal_strength']['breakthrough_component']}")
    print(f"   孤子分量: {result['signal_strength']['soliton_component']}")

    print("\n[仓位建议]")
    print(f"   建议仓位: {result['position']['position_pct']}%")
    print(f"   止损设置: {result['position']['stop_loss_pct']}%")
    print(f"   回撤加仓: {'是' if result['position']['add_on_dip'] else '否'}")
