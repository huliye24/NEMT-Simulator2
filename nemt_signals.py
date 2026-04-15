"""
NEMT信号指标模块
实现第二章、第六章中定义的量化指标

包含：
1. DCI (方向一致性指数) - 测量噪声强度
2. SNR (信号噪声比) - 链上大额/小额转账比
3. 涡旋检测 - 四个条件的量化
4. 随机共振检测 - 三个条件的量化
5. 谱宽计算 - 市场结构稳定性指标
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum


class MarketPhase(Enum):
    """市场四相位"""
    PHASE_A_NOISE = "A"      # 高噪声混乱期
    PHASE_B_VORTEX = "B"     # 涡旋蓄力期
    PHASE_C_RESONANCE = "C"   # 临界爆发前夜
    PHASE_D_TREND = "D"       # 趋势运行期


@dataclass
class DCISettings:
    """DCI计算设置"""
    n_periods: int = 24       # 计算周期（24根K线）
    high_threshold: float = 0.70   # 低噪声阈值
    low_threshold: float = 0.55    # 高噪声阈值
    medium_threshold: float = 0.65  # 中等阈值


@dataclass
class VortexSettings:
    """涡旋检测设置"""
    bbb_percentile: int = 20       # 布林带宽度百分位
    oi_change_threshold: float = 0.05  # OI变化阈值
    oi_level_percentile: int = 80   # OI水平百分位
    funding_rate_threshold: float = 0.0001  # 资金费率阈值(0.01%)


@dataclass
class ResonanceSettings:
    """随机共振检测设置"""
    mvrv_critical_low: float = 0.0   # MVRV临界低值
    mvrv_critical_high: float = 5.0    # MVRV临界高值
    dci_vol_low: float = 0.08        # DCI波动率下限
    dci_vol_high: float = 0.15        # DCI波动率上限
    dci_mean_threshold: float = 0.55   # DCI均值阈值


@dataclass
class DCISignal:
    """DCI信号结果"""
    value: float
    noise_state: str  # "high", "medium", "low"
    direction: str     # "bullish", "bearish", "neutral"
    trend: str        # "strengthening", "weakening", "stable"


@dataclass
class VortexConditions:
    """涡旋四个条件"""
    bbw_narrow: bool = False           # 条件1: 波动率锥收窄
    volume_uniform: bool = False          # 条件2: 成交量均匀分布
    oi_high_flat: bool = False           # 条件3: OI高位走平
    funding_neutral: bool = False        # 条件4: 资金费率零轴摆动
    is_vortex: bool = False             # 是否形成涡旋
    maturity_score: float = 0.0         # 涡旋成熟度
    direction: Optional[str] = None     # 突破方向(如有)


@dataclass
class ResonanceConditions:
    """随机共振三个条件"""
    long_term_critical: bool = False    # 条件1: 长周期临界点
    short_term_noise: bool = False       # 条件2: 短周期噪声适中
    trigger_factor: bool = False        # 条件3: 潜在触发因子
    is_resonance: bool = False          # 是否触发随机共振
    bullish: bool = True                # 方向: True=看涨, False=看跌
    confidence: float = 0.0             # 置信度 0-1


@dataclass
class NEMTSignals:
    """NEMT完整信号"""
    dci: DCISignal
    vortex: VortexConditions
    resonance: ResonanceConditions
    phase: MarketPhase
    phase_confidence: float = 0.0
    spectral_width: Optional[float] = None


class NEMTSignalIndicators:
    """
    NEMT信号指标计算器
    
    根据Notion第二章和第六章的量化定义实现
    """

    def __init__(
        self,
        dci_settings: Optional[DCISettings] = None,
        vortex_settings: Optional[VortexSettings] = None,
        resonance_settings: Optional[ResonanceSettings] = None
    ):
        self.dci_settings = dci_settings or DCISettings()
        self.vortex_settings = vortex_settings or VortexSettings()
        self.resonance_settings = resonance_settings or ResonanceSettings()
        
        # 历史数据缓存
        self.dci_history: List[float] = []
        self.price_history: List[float] = []
        
    def compute_dci(
        self, 
        prices: np.ndarray,
        n_periods: Optional[int] = None
    ) -> DCISignal:
        """
        计算方向一致性指数 (DCI)
        
        DCI = max(U, D) / N
        其中 U = 上涨K线数量, D = 下跌K线数量, N = 总K线数
        
        Args:
            prices: 价格序列 (收盘价)
            n_periods: 计算周期
            
        Returns:
            DCISignal对象
        """
        if n_periods is None:
            n_periods = self.dci_settings.n_periods
            
        n = min(len(prices) - 1, n_periods)
        if n < 2:
            return DCISignal(
                value=0.5,
                noise_state="medium",
                direction="neutral",
                trend="stable"
            )
        
        # 计算涨跌
        returns = np.diff(prices[-n-1:])
        up_count = np.sum(returns > 0)
        down_count = np.sum(returns < 0)
        
        # DCI计算
        max_count = max(up_count, down_count)
        dci_value = max_count / n
        
        # 噪声状态判断
        if dci_value > self.dci_settings.high_threshold:
            noise_state = "low"
        elif dci_value < self.dci_settings.low_threshold:
            noise_state = "high"
        else:
            noise_state = "medium"
        
        # 方向判断
        if up_count > down_count:
            direction = "bullish"
        elif down_count > up_count:
            direction = "bearish"
        else:
            direction = "neutral"
        
        # 趋势判断 (与历史DCI比较)
        self.dci_history.append(dci_value)
        if len(self.dci_history) >= 3:
            recent = np.mean(self.dci_history[-3:])
            prev = np.mean(self.dci_history[-5:-2]) if len(self.dci_history) >= 5 else recent
            if recent > prev * 1.05:
                trend = "strengthening"
            elif recent < prev * 0.95:
                trend = "weakening"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return DCISignal(
            value=dci_value,
            noise_state=noise_state,
            direction=direction,
            trend=trend
        )
    
    def compute_dci_volatility(self, window: int = 20) -> float:
        """
        计算DCI波动率 (用于随机共振条件2)
        
        DCI_vol = DCI的window日标准差
        
        Returns:
            DCI波动率
        """
        if len(self.dci_history) < window:
            return 0.0
        return np.std(self.dci_history[-window:])
    
    def detect_vortex(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        oi_values: np.ndarray,
        funding_rates: np.ndarray,
        bbw_history: np.ndarray,
        atr: Optional[float] = None
    ) -> VortexConditions:
        """
        检测涡旋结构
        
        四个条件:
        1. BBW < 20%分位数 (波动率锥收窄)
        2. 成交量均匀分布 (上涨/下跌各40%-60%)
        3. OI高位走平 (变化率<5%且水平>80%分位)
        4. 资金费率零轴摆动 (7日均值<0.01%)
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            oi_values: 持仓量序列
            funding_rates: 资金费率序列(8小时)
            bbw_history: 布林带宽度历史
            atr: ATR值(可选)
            
        Returns:
            VortexConditions对象
        """
        n = len(prices)
        
        # 条件1: BBW收窄
        if len(bbw_history) >= 30:
            bbw_percentile = np.percentile(bbw_history, self.vortex_settings.bbb_percentile)
            bbw_narrow = bbw_history[-1] < bbw_percentile
        else:
            bbw_narrow = False
        
        # 条件2: 成交量均匀分布
        if n >= 20:
            returns = np.diff(prices)
            up_mask = returns >= 0
            down_mask = returns < 0
            
            up_volume = np.sum(volumes[1:][up_mask])
            down_volume = np.sum(volumes[1:][down_mask])
            total_volume = up_volume + down_volume
            
            if total_volume > 0:
                up_ratio = up_volume / total_volume
                down_ratio = down_volume / total_volume
                volume_uniform = 0.40 <= up_ratio <= 0.60 and 0.40 <= down_ratio <= 0.60
            else:
                volume_uniform = False
        else:
            volume_uniform = False
        
        # 条件3: OI高位走平
        if len(oi_values) >= 7:
            oi_change = np.mean(np.diff(oi_values[-7:])) / np.mean(oi_values[-7:])
            oi_level_percentile = np.percentile(oi_values[-30:], self.vortex_settings.oi_level_percentile) if len(oi_values) >= 30 else np.mean(oi_values)
            oi_high = oi_values[-1] > oi_level_percentile
            oi_flat = abs(oi_change) < self.vortex_settings.oi_change_threshold
            oi_high_flat = oi_high and oi_flat
        else:
            oi_high_flat = False
        
        # 条件4: 资金费率零轴摆动
        if len(funding_rates) >= 7:
            funding_mean = np.mean(np.abs(funding_rates[-7:]))
            funding_neutral = funding_mean < self.vortex_settings.funding_rate_threshold
        else:
            funding_neutral = False
        
        # 判断是否形成涡旋
        conditions_met = sum([bbw_narrow, volume_uniform, oi_high_flat, funding_neutral])
        is_vortex = conditions_met >= 3
        
        # 计算涡旋成熟度
        maturity_score = 0.0
        if is_vortex:
            # 成熟度 = 持续天数 * OI相对水平
            # 简化: 使用条件满足数量和时间作为代理
            base_score = conditions_met * 2.5
            
            # OI相对水平加分
            if len(oi_values) >= 30:
                oi_ratio = oi_values[-1] / np.mean(oi_values[-30:])
                maturity_score = base_score * min(oi_ratio, 2.0)
            else:
                maturity_score = base_score
        
        return VortexConditions(
            bbw_narrow=bbw_narrow,
            volume_uniform=volume_uniform,
            oi_high_flat=oi_high_flat,
            funding_neutral=funding_neutral,
            is_vortex=is_vortex,
            maturity_score=maturity_score
        )
    
    def detect_resonance(
        self,
        mvrv_zscore: Optional[float] = None,
        nupl: Optional[float] = None,
        lth_ratio: Optional[float] = None,
        sth_ratio: Optional[float] = None,
        days_to_halving: Optional[int] = None,
        liquidity_score: Optional[float] = None,
        dci_volatility: Optional[float] = None,
        has_macro_event: bool = False,
        has_onchain_event: bool = False
    ) -> ResonanceConditions:
        """
        检测随机共振
        
        三个条件:
        1. 长周期结构处于临界点
        2. 短周期噪声强度适中
        3. 存在潜在触发因子
        
        Args:
            mvrv_zscore: MVRV Z-score
            nupl: NUPL值
            lth_ratio: 长期持有者供应占比变化
            sth_ratio: 短期持有者供应占比变化
            days_to_halving: 距减半天数
            liquidity_score: 宏观流动性评分(0-10)
            dci_volatility: DCI波动率
            has_macro_event: 是否有宏观事件
            has_onchain_event: 是否有链上事件
            
        Returns:
            ResonanceConditions对象
        """
        rs = self.resonance_settings
        
        # 条件1: 长周期临界点 (计算综合评分)
        long_term_score = 0
        bullish_score = 0
        bearish_score = 0
        
        if mvrv_zscore is not None:
            if mvrv_zscore < rs.mvrv_critical_low:
                long_term_score += 2
                bullish_score += 1
            elif mvrv_zscore > rs.mvrv_critical_high:
                long_term_score += 2
                bearish_score += 1
        
        if nupl is not None:
            if nupl < 0:  # 投降区
                long_term_score += 1
                bullish_score += 1
            elif nupl > 0.75:  # 欣快区
                long_term_score += 1
                bearish_score += 1
        
        if lth_ratio is not None:
            if lth_ratio > 0.01:  # 月增长>1%
                long_term_score += 1
                bullish_score += 1
        
        if sth_ratio is not None:
            if sth_ratio > 0.01:  # 月增长>1%
                long_term_score += 1
                bearish_score += 1
        
        if days_to_halving is not None:
            if -180 <= days_to_halving <= 180:  # 减半附近
                long_term_score += 1
                bullish_score += 1
            elif days_to_halving > 540:  # 减半后18个月以上
                long_term_score += 1
                bearish_score += 1
        
        if liquidity_score is not None:
            if liquidity_score >= 7:
                long_term_score += 1
                bullish_score += 1
            elif liquidity_score <= 3:
                long_term_score += 1
                bearish_score += 1
        
        long_term_critical = long_term_score >= 4
        
        # 条件2: 短周期噪声适中
        if dci_volatility is not None:
            short_term_noise = rs.dci_vol_low <= dci_volatility <= rs.dci_vol_high
        else:
            # 使用默认DCI值作为代理
            if len(self.dci_history) >= 20:
                dci_vol = self.compute_dci_volatility(20)
                short_term_noise = rs.dci_vol_low <= dci_vol <= rs.dci_vol_high
            else:
                short_term_noise = False
        
        # 条件3: 潜在触发因子
        trigger_factor = has_macro_event or has_onchain_event
        
        # 综合判断
        is_resonance = long_term_critical and short_term_noise and trigger_factor
        
        # 方向判断
        bullish = bullish_score > bearish_score
        
        # 置信度
        if is_resonance:
            conditions_met = sum([long_term_critical, short_term_noise, trigger_factor])
            confidence = conditions_met / 3.0
        else:
            confidence = 0.0
        
        return ResonanceConditions(
            long_term_critical=long_term_critical,
            short_term_noise=short_term_noise,
            trigger_factor=trigger_factor,
            is_resonance=is_resonance,
            bullish=bullish,
            confidence=confidence
        )
    
    def determine_phase(
        self,
        dci: DCISignal,
        vortex: VortexConditions,
        resonance: ResonanceConditions
    ) -> Tuple[MarketPhase, float]:
        """
        确定市场相位
        
        相位判定规则:
        1. 随机共振触发 -> 相位C
        2. 涡旋形成 -> 相位B
        3. DCI > 0.65且无涡旋 -> 相位D (趋势)
        4. DCI < 0.55 -> 相位A (高噪声)
        5. 其他 -> 过渡期
        
        Args:
            dci: DCI信号
            vortex: 涡旋条件
            resonance: 随机共振条件
            
        Returns:
            (相位, 置信度)
        """
        # 规则1: 随机共振触发 -> 相位C
        if resonance.is_resonance:
            return MarketPhase.PHASE_C_RESONANCE, resonance.confidence
        
        # 规则2: 涡旋形成 -> 相位B
        if vortex.is_vortex:
            return MarketPhase.PHASE_B_VORTEX, vortex.maturity_score / 15.0
        
        # 规则3: 低DCI -> 相位A
        if dci.value < self.dci_settings.low_threshold:
            return MarketPhase.PHASE_A_NOISE, 1.0 - (self.dci_settings.low_threshold - dci.value) / 0.1
        
        # 规则4: 高DCI -> 相位D (趋势)
        if dci.value > self.dci_settings.medium_threshold:
            return MarketPhase.PHASE_D_TREND, (dci.value - 0.5) * 2
        
        # 规则5: 过渡期
        return MarketPhase.PHASE_A_NOISE, 0.5
    
    def compute_spectral_width(
        self,
        spectrum: np.ndarray,
        freqs: np.ndarray
    ) -> Tuple[float, float]:
        """
        计算谱宽
        
        谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))
        
        Args:
            spectrum: 频谱
            freqs: 频率
            
        Returns:
            (谱宽, 平均频率)
        """
        spectrum_power = np.abs(spectrum) ** 2
        total_power = np.sum(spectrum_power)
        
        if total_power < 1e-10:
            return 0.0, 0.0
        
        # 加权均值
        mean_freq = np.sum(freqs * spectrum_power) / total_power
        
        # 方差
        variance = np.sum((freqs - mean_freq) ** 2 * spectrum_power) / total_power
        spectral_width = np.sqrt(variance)
        
        return spectral_width, mean_freq
    
    def compute_phase_metrics(self, phase: MarketPhase) -> Dict:
        """
        根据相位返回策略指标
        
        Args:
            phase: 当前相位
            
        Returns:
            策略指标字典
        """
        phase_configs = {
            MarketPhase.PHASE_A_NOISE: {
                "position_ratio": 0.20,
                "max_position": 0.20,
                "single_risk": 0.01,
                "leverage": 0,
                "strategy": "仅持有长期底仓，不做短线交易",
                "focus": "等待DCI回升、涡旋条件形成"
            },
            MarketPhase.PHASE_B_VORTEX: {
                "position_ratio": 0.35,
                "max_position": 0.50,
                "single_risk": 0.02,
                "leverage": 0,
                "strategy": "识别区间边界，预设突破条件单，不预判方向",
                "focus": "涡旋成熟度、突破时成交量确认"
            },
            MarketPhase.PHASE_C_RESONANCE: {
                "position_ratio": 0.60,
                "max_position": 0.70,
                "single_risk": 0.03,
                "leverage": 1,
                "strategy": "提高对突破信号的敏感度，敢于追入",
                "focus": "触发事件兑现、突破后量能持续性"
            },
            MarketPhase.PHASE_D_TREND: {
                "position_ratio": 0.85,
                "max_position": 1.00,
                "single_risk": 0.02,
                "leverage": 0,
                "strategy": "持仓为主，回调至均线加仓",
                "focus": "DCI是否从高位回落、SNR是否萎缩"
            }
        }
        
        return phase_configs.get(phase, phase_configs[MarketPhase.PHASE_A_NOISE])
    
    def get_full_signals(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        oi_values: np.ndarray,
        funding_rates: np.ndarray,
        bbw_history: np.ndarray,
        spectrum: Optional[np.ndarray] = None,
        freqs: Optional[np.ndarray] = None,
        **onchain_params
    ) -> NEMTSignals:
        """
        计算完整NEMT信号
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            oi_values: 持仓量序列
            funding_rates: 资金费率序列
            bbw_history: 布林带宽度历史
            spectrum: 频谱(可选)
            freqs: 频率(可选)
            **onchain_params: 链上参数(MVRV, NUPL等)
            
        Returns:
            NEMTSignals对象
        """
        # 1. 计算DCI
        dci = self.compute_dci(prices)
        
        # 2. 计算DCI波动率
        dci_volatility = self.compute_dci_volatility(20)
        
        # 3. 检测涡旋
        vortex = self.detect_vortex(
            prices, volumes, oi_values, 
            funding_rates, bbw_history
        )
        
        # 4. 检测随机共振
        resonance = self.detect_resonance(
            dci_volatility=dci_volatility,
            **onchain_params
        )
        
        # 5. 确定相位
        phase, confidence = self.determine_phase(dci, vortex, resonance)
        
        # 6. 计算谱宽
        spectral_width = None
        if spectrum is not None and freqs is not None:
            spectral_width, _ = self.compute_spectral_width(spectrum, freqs)
        
        return NEMTSignals(
            dci=dci,
            vortex=vortex,
            resonance=resonance,
            phase=phase,
            phase_confidence=confidence,
            spectral_width=spectral_width
        )
    
    def interpret_signals(self, signals: NEMTSignals) -> Dict:
        """
        解释信号，返回可读的交易建议
        
        Args:
            signals: NEMT信号
            
        Returns:
            解释字典
        """
        phase_metrics = self.compute_phase_metrics(signals.phase)
        
        interpretation = {
            "phase_name": {
                "A": "高噪声混乱期",
                "B": "涡旋蓄力期",
                "C": "临界爆发前夜",
                "D": "趋势运行期"
            }[signals.phase.value],
            
            "phase_confidence": f"{signals.phase_confidence:.1%}",
            
            "dci_reading": f"DCI={signals.dci.value:.3f} ({signals.dci.noise_state}噪声)",
            
            "vortex_reading": (
                "涡旋已形成" if signals.vortex.is_vortex 
                else f"涡旋未形成 ({sum([signals.vortex.bbw_narrow, signals.vortex.volume_uniform, 
                     signals.vortex.oi_high_flat, signals.vortex.funding_neutral])}/4条件)"
            ),
            
            "resonance_reading": (
                f"随机共振触发 ({'看涨' if signals.resonance.bullish else '看跌'})" 
                if signals.resonance.is_resonance
                else "随机共振未触发"
            ),
            
            "spectral_width_reading": (
                f"谱宽={signals.spectral_width:.4f}"
                if signals.spectral_width is not None
                else "谱宽未计算"
            ),
            
            "strategy": phase_metrics["strategy"],
            
            "position_recommendation": {
                "ratio": phase_metrics["position_ratio"],
                "max": phase_metrics["max_position"],
                "single_risk": phase_metrics["single_risk"],
                "leverage": phase_metrics["leverage"]
            },
            
            "key_focus": phase_metrics["focus"]
        }
        
        return interpretation
