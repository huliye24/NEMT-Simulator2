"""
NEMT 第九章：时间-空间决策
多周期信号叠加与市场间套利

包含：
1. 多周期决策框架（5个层级）
2. 周期共振与冲突处理
3. 跨交易所价差指标
4. 期现结构与资金费率
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta


# =====================
# 周期层级定义
# =====================

class CycleLevel(Enum):
    """时间周期层级"""
    MACRO = "macro"           # 宏观层：月线级别
    STRATEGIC = "strategic"   # 战略层：周线级别
    TACTICAL = "tactical"     # 战术层：日线级别
    EXECUTION = "execution"   # 执行层：4小时级别
    MICRO = "micro"           # 微观层：15分钟级别


@dataclass
class CycleSignal:
    """周期信号"""
    level: CycleLevel
    direction: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0-1
    weight: float  # 决策权重
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CycleResonanceResult:
    """周期共振结果"""
    resonance_score: float  # 0-10
    dominant_direction: str
    conflict_count: int
    conflict_details: List[str]
    recommendation: str


# =====================
# 多周期决策框架
# =====================

class MultiCycleFramework:
    """
    多周期决策框架
    
    权重原则：
    - 越上层的信号，越决定"做不做"
    - 越下层的信号，越决定"怎么做"
    """

    # 周期层级权重配置
    CYCLE_WEIGHTS = {
        CycleLevel.MACRO: 0.30,      # 宏观层：30%
        CycleLevel.STRATEGIC: 0.25,   # 战略层：25%
        CycleLevel.TACTICAL: 0.25,    # 战术层：25%
        CycleLevel.EXECUTION: 0.15,   # 执行层：15%
        CycleLevel.MICRO: 0.05,       # 微观层：5%
    }

    # 周期层级与观察周期
    CYCLE_OBSERVATION = {
        CycleLevel.MACRO: "每月第一周",
        CycleLevel.STRATEGIC: "每周",
        CycleLevel.TACTICAL: "每日收盘",
        CycleLevel.EXECUTION: "每4小时",
        CycleLevel.MICRO: "实时",
    }

    def __init__(self):
        self.signals: Dict[CycleLevel, CycleSignal] = {}

    def add_signal(self, signal: CycleSignal):
        """添加周期信号"""
        self.signals[signal.level] = signal

    def calculate_resonance(self) -> CycleResonanceResult:
        """
        计算周期共振
        
        Returns:
            CycleResonanceResult对象
        """
        if not self.signals:
            return CycleResonanceResult(
                resonance_score=0,
                dominant_direction="neutral",
                conflict_count=0,
                conflict_details=["无信号"],
                recommendation="等待信号"
            )

        # 计算加权方向
        direction_scores = {
            "bullish": 0.0,
            "bearish": 0.0,
            "neutral": 0.0
        }

        conflicts = []
        previous_direction = None

        for level in CycleLevel:
            if level in self.signals:
                sig = self.signals[level]
                weight = self.CYCLE_WEIGHTS[level]
                
                if sig.direction == "bullish":
                    direction_scores["bullish"] += weight * sig.confidence
                elif sig.direction == "bearish":
                    direction_scores["bearish"] += weight * sig.confidence
                else:
                    direction_scores["neutral"] += weight * sig.confidence

                # 检测冲突
                if previous_direction and previous_direction != sig.direction:
                    conflicts.append(f"{level.value}与上一级信号冲突: {previous_direction} vs {sig.direction}")
                
                previous_direction = sig.direction

        # 计算共振分数
        total = sum(direction_scores.values())
        dominant = max(direction_scores, key=direction_scores.get)
        dominant_score = direction_scores[dominant] / total if total > 0 else 0

        resonance_score = dominant_score * 10  # 0-10

        # 生成建议
        if resonance_score >= 8:
            recommendation = f"强烈{dominant}信号，执行{'做多' if dominant == 'bullish' else '做空' if dominant == 'bearish' else '观望'}策略"
        elif resonance_score >= 6:
            recommendation = f"{dominant}信号，可适度建仓"
        elif resonance_score >= 4:
            recommendation = "信号分歧，保持观望，等待共振明确"
        else:
            recommendation = "信号混乱，放弃本次机会"

        return CycleResonanceResult(
            resonance_score=resonance_score,
            dominant_direction=dominant,
            conflict_count=len(conflicts),
            conflict_details=conflicts,
            recommendation=recommendation
        )

    def handle_conflict(self, level_a: CycleLevel, level_b: CycleLevel, 
                       direction_a: str, direction_b: str) -> str:
        """
        处理周期冲突
        
        规则：上级优先原则
        """
        # 定义层级优先级
        priority = {
            CycleLevel.MACRO: 5,
            CycleLevel.STRATEGIC: 4,
            CycleLevel.TACTICAL: 3,
            CycleLevel.EXECUTION: 2,
            CycleLevel.MICRO: 1,
        }

        # 上级优先
        if priority[level_a] > priority[level_b]:
            return f"以{level_a.value}为准，{level_b.value}信号暂不执行"
        else:
            return f"以{level_b.value}为准，{level_a.value}等待调整"

    def get_decision_summary(self) -> Dict:
        """获取决策摘要"""
        resonance = self.calculate_resonance()
        
        return {
            "signals": {
                level.value: {
                    "direction": sig.direction,
                    "confidence": f"{sig.confidence:.0%}",
                    "reason": sig.reason
                }
                for level, sig in self.signals.items()
            },
            "resonance_score": resonance.resonance_score,
            "dominant_direction": resonance.dominant_direction,
            "conflict_count": resonance.conflict_count,
            "recommendation": resonance.recommendation
        }


# =====================
# 跨交易所价差指标
# =====================

@dataclass
class PremiumIndex:
    """价差指标"""
    name: str
    current_value: float
    threshold: float
    signal: str  # "bullish", "bearish", "neutral"
    duration_hours: float
    interpretation: str


class CrossExchangeFramework:
    """
    跨交易所价格离散框架
    
    三个关键价差指标：
    1. Coinbase溢价指数
    2. 韩国泡菜溢价
    3. 稳定币脱锚指数
    """

    def __init__(self):
        self.premium_history: List[PremiumIndex] = []

    def check_coinbase_premium(
        self,
        coinbase_price: float,
        binance_price: float,
        duration_hours: float = 4
    ) -> PremiumIndex:
        """
        Coinbase溢价指数
        
        规则：
        - 溢价>0.3%且持续>4小时 → 机构买盘强劲，趋势看涨
        - 折价>0.3%且持续>4小时 → 机构卖压或避险，趋势看跌
        - ±0.1%内波动 → 正常状态
        """
        premium_pct = (coinbase_price - binance_price) / binance_price * 100
        
        if premium_pct > 0.3 and duration_hours >= 4:
            signal = "bullish"
            interpretation = "机构买盘强劲，趋势看涨"
        elif premium_pct < -0.3 and duration_hours >= 4:
            signal = "bearish"
            interpretation = "机构卖压或避险，趋势看跌"
        else:
            signal = "neutral"
            interpretation = "正常状态，无额外信息"

        return PremiumIndex(
            name="Coinbase溢价指数",
            current_value=premium_pct,
            threshold=0.3,
            signal=signal,
            duration_hours=duration_hours,
            interpretation=interpretation
        )

    def check_kimchi_premium(
        self,
        korean_price: float,
        global_price: float
    ) -> PremiumIndex:
        """
        韩国泡菜溢价
        
        规则：
        - 溢价>5% → 散户FOMO，短期顶部
        - 溢价>10% → 强烈顶部预警
        - 折价(负溢价) → 韩国散户恐慌，往往是阶段性底部
        """
        premium_pct = (korean_price - global_price) / global_price * 100
        
        if premium_pct > 10:
            signal = "bearish"
            interpretation = "强烈顶部预警，应考虑减仓"
        elif premium_pct > 5:
            signal = "bearish"
            interpretation = "散户FOMO，短期顶部信号"
        elif premium_pct < 0:
            signal = "bullish"
            interpretation = "韩国散户恐慌，往往是阶段性底部"
        else:
            signal = "neutral"
            interpretation = "正常状态"

        return PremiumIndex(
            name="泡菜溢价",
            current_value=premium_pct,
            threshold=5.0,
            signal=signal,
            duration_hours=0,
            interpretation=interpretation
        )

    def check_stablecoin_depeg(
        self,
        stablecoin_prices: Dict[str, float]  # {exchange: price}
    ) -> PremiumIndex:
        """
        稳定币脱锚指数
        
        规则：
        - 任一稳定币在主要交易所折价>0.5% → 恐慌信号，短期看跌
        - 稳定币溢价>0.5% → 资金涌入，看涨
        """
        max_discount = 0.0
        max_premium = 0.0
        
        for exchange, price in stablecoin_prices.items():
            if price < 1.0:
                discount = (1.0 - price) * 100
                max_discount = max(max_discount, discount)
            else:
                premium = (price - 1.0) * 100
                max_premium = max(max_premium, premium)

        if max_discount > 0.5:
            signal = "bearish"
            interpretation = f"市场在抛售稳定币换取法币，是恐慌信号"
        elif max_premium > 0.5:
            signal = "bullish"
            interpretation = f"资金在涌入加密市场，看涨"
        else:
            signal = "neutral"
            interpretation = "稳定币锚定正常"

        return PremiumIndex(
            name="稳定币脱锚指数",
            current_value=-max_discount if max_discount > 0 else max_premium,
            threshold=0.5,
            signal=signal,
            duration_hours=0,
            interpretation=interpretation
        )

    def get_arbitrage_signals(
        self,
        coinbase_price: float,
        binance_price: float,
        korean_price: float,
        global_price: float,
        stablecoin_prices: Dict[str, float]
    ) -> Dict:
        """
        获取所有套利信号
        """
        coinbase = self.check_coinbase_premium(coinbase_price, binance_price)
        kimchi = self.check_kimchi_premium(korean_price, global_price)
        stablecoin = self.check_stablecoin_depeg(stablecoin_prices)

        # 综合判断
        signals = [coinbase.signal, kimchi.signal, stablecoin.signal]
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")

        if bullish_count >= 2:
            composite = "bullish"
        elif bearish_count >= 2:
            composite = "bearish"
        else:
            composite = "neutral"

        return {
            "coinbase_premium": {
                "value": f"{coinbase.current_value:.2f}%",
                "signal": coinbase.signal,
                "interpretation": coinbase.interpretation
            },
            "kimchi_premium": {
                "value": f"{kimchi.current_value:.2f}%",
                "signal": kimchi.signal,
                "interpretation": kimchi.interpretation
            },
            "stablecoin_depeg": {
                "value": f"{stablecoin.current_value:.2f}%",
                "signal": stablecoin.signal,
                "interpretation": stablecoin.interpretation
            },
            "composite_signal": composite,
            "recommendations": self._get_arbitrage_recommendations(
                coinbase, kimchi, stablecoin
            )
        }

    def _get_arbitrage_recommendations(
        self,
        coinbase: PremiumIndex,
        kimchi: PremiumIndex,
        stablecoin: PremiumIndex
    ) -> List[str]:
        """获取套利建议"""
        recommendations = []

        # Coinbase溢价用法
        if coinbase.signal == "bearish":
            recommendations.append("趋势向上但Coinbase持续折价，上涨根基不稳，降低仓位、收紧止损")
        
        # 泡菜溢价极端值
        if kimchi.current_value > 10:
            recommendations.append("泡菜溢价>10% + NUPL>0.75，分批卖出锁定利润")
        elif kimchi.current_value < 0:
            recommendations.append("泡菜溢价转负，可能是阶段性底部关注")

        # 稳定币脱锚
        if stablecoin.signal == "bearish":
            recommendations.append("稳定币折价>0.5%，是恐慌信号，短期看跌")
        elif stablecoin.signal == "bullish":
            recommendations.append("稳定币溢价>0.5%，资金涌入，看涨")

        return recommendations if recommendations else ["无特殊套利建议"]


# =====================
# 期现结构与资金费率
# =====================

@dataclass
class BasisData:
    """基差数据"""
    futures_price: float
    spot_price: float
    basis_pct: float  # (futures - spot) / spot * 100
    basis_type: str  # "contango" (正基差) or "backwardation" (负基差)


@dataclass
class FundingRateData:
    """资金费率数据"""
    rate_pct: float  # 百分比
    rate_annualized: float  # 年化
    interpretation: str


class FuturesSpotFramework:
    """
    期现结构与资金费率框架
    """

    def check_basis_signal(
        self,
        futures_price: float,
        spot_price: float,
        previous_basis_pct: Optional[float] = None
    ) -> Dict:
        """
        基差信号
        
        基差变化速率比绝对水平更重要
        """
        basis_pct = (futures_price - spot_price) / spot_price * 100
        
        basis_type = "contango" if basis_pct > 0 else "backwardation"
        
        # 基差变化
        if previous_basis_pct is not None:
            basis_change = basis_pct - previous_basis_pct
        else:
            basis_change = 0

        # 信号判断
        if basis_pct > 5:
            signal = "very_bullish"
            interpretation = "正基差扩大，市场极度乐观，警惕顶部"
        elif basis_pct > 2:
            signal = "bullish"
            interpretation = "正常牛市基差结构"
        elif basis_pct < -2:
            signal = "bearish"
            interpretation = "负基差，市场恐慌或牛市末期"
        else:
            signal = "neutral"
            interpretation = "基差收窄，观望"

        # 基差变化信号
        if basis_change < -3:
            change_signal = "bearish"
            change_interpretation = "基差急剧收窄，可能转势"
        elif basis_change > 3:
            change_signal = "bullish"
            change_interpretation = "基差快速扩大，看涨情绪升温"
        else:
            change_signal = "neutral"
            change_interpretation = "基差变化平稳"

        return {
            "basis": {
                "value": f"{basis_pct:.2f}%",
                "type": basis_type,
                "signal": signal,
                "interpretation": interpretation
            },
            "basis_change": {
                "value": f"{basis_change:+.2f}%",
                "signal": change_signal,
                "interpretation": change_interpretation
            }
        }

    def check_funding_rate(
        self,
        funding_rate: float,  # 如 0.0001 = 0.01%
        period_hours: float = 8  # 结算周期
    ) -> FundingRateData:
        """
        资金费率分析
        
        规则：
        - 极端正值(>0.05%) → 多头拥挤，警惕顶部
        - 极端负值(<-0.05%) → 空头拥挤，警惕底部
        - 资金费率由正转负 → 可能开始下跌
        """
        rate_pct = funding_rate * 100
        rate_annualized = rate_pct * (365 * 24 / period_hours)

        if rate_pct > 0.05:
            interpretation = "多头拥挤，极端贪婪，警惕顶部"
        elif rate_pct > 0.01:
            interpretation = "多头略占优势，正常"
        elif rate_pct < -0.05:
            interpretation = "空头拥挤，极端恐慌，可能是底部"
        elif rate_pct < -0.01:
            interpretation = "空头略占优势"
        else:
            interpretation = "多空平衡"

        return FundingRateData(
            rate_pct=rate_pct,
            rate_annualized=rate_annualized,
            interpretation=interpretation
        )

    def get_entry_optimization(
        self,
        funding_rate: float,
        time_of_day: Optional[str] = None  # "morning", "afternoon", "evening", "night"
    ) -> Dict:
        """
        入场时机优化
        
        规则：
        - 避免在资金费率极端值时开仓
        - 资金费率>0.05%或<-0.05%时谨慎
        """
        rate_pct = abs(funding_rate) * 100
        
        if rate_pct > 0.05:
            position_size_reduction = 0.5
            warning = "资金费率极端，减少仓位50%"
        elif rate_pct > 0.02:
            position_size_reduction = 0.8
            warning = "资金费率偏高，减少仓位20%"
        else:
            position_size_reduction = 1.0
            warning = None

        # 最佳开仓时间（资金费率通常在结算时变化）
        best_times = {
            "morning": "UTC 00:00 结算后4小时内",
            "afternoon": "UTC 08:00 结算后4小时内",
            "evening": "UTC 16:00 结算后4小时内",
        }

        return {
            "current_rate": f"{rate_pct:.3f}%",
            "position_size_reduction": f"{position_size_reduction:.0%}",
            "warning": warning,
            "best_entry_times": best_times,
            "avoid_times": ["结算前1小时", "极端波动时段"]
        }


# =====================
# 综合决策引擎
# =====================

class NEMTSpatialTemporalEngine:
    """
    NEMT 时空决策引擎
    
    综合多周期信号、跨交易所价差、期现结构
    """

    def __init__(self):
        self.cycle_framework = MultiCycleFramework()
        self.cross_exchange = CrossExchangeFramework()
        self.futures_spot = FuturesSpotFramework()

    def run_full_analysis(
        self,
        # 周期信号
        macro_direction: str = "neutral",
        strategic_direction: str = "neutral",
        tactical_direction: str = "neutral",
        execution_direction: str = "neutral",
        
        # 价差数据
        coinbase_premium: float = 0.0,
        kimchi_premium: float = 0.0,
        stablecoin_discount: float = 0.0,
        
        # 期现数据
        basis_pct: float = 0.0,
        funding_rate: float = 0.0,
        
        # 其他
        phase: str = "A",
        nupl: float = 0.5,
    ) -> Dict:
        """
        运行完整分析
        """
        # 1. 多周期共振
        if macro_direction != "neutral":
            self.cycle_framework.add_signal(CycleSignal(
                level=CycleLevel.MACRO,
                direction=macro_direction,
                confidence=0.8,
                weight=0.30,
                reason="宏观流动性评分"
            ))
        
        if strategic_direction != "neutral":
            self.cycle_framework.add_signal(CycleSignal(
                level=CycleLevel.STRATEGIC,
                direction=strategic_direction,
                confidence=0.7,
                weight=0.25,
                reason="战略周期判断"
            ))
        
        if tactical_direction != "neutral":
            self.cycle_framework.add_signal(CycleSignal(
                level=CycleLevel.TACTICAL,
                direction=tactical_direction,
                confidence=0.6,
                weight=0.25,
                reason="战术相位判断"
            ))
        
        if execution_direction != "neutral":
            self.cycle_framework.add_signal(CycleSignal(
                level=CycleLevel.EXECUTION,
                direction=execution_direction,
                confidence=0.5,
                weight=0.15,
                reason="执行层信号"
            ))

        resonance = self.cycle_framework.calculate_resonance()

        # 2. 跨交易所信号
        arbitrage_signals = self.cross_exchange.get_arbitrage_signals(
            coinbase_price=1 + coinbase_premium / 100,
            binance_price=1.0,
            korean_price=1 + kimchi_premium / 100,
            global_price=1.0,
            stablecoin_prices={"binance": 1 - stablecoin_discount / 100}
        )

        # 3. 期现结构
        basis_signals = self.futures_spot.check_basis_signal(
            futures_price=1 + basis_pct / 100,
            spot_price=1.0
        )
        funding_data = self.futures_spot.check_funding_rate(funding_rate)
        entry_optimization = self.futures_spot.get_entry_optimization(funding_rate)

        # 4. 综合决策
        signals = [
            resonance.dominant_direction,
            arbitrage_signals["composite_signal"],
            basis_signals["basis"]["signal"].replace("very_", ""),
        ]
        
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")

        if bullish_count >= 2:
            final_signal = "bullish"
        elif bearish_count >= 2:
            final_signal = "bearish"
        else:
            final_signal = "neutral"

        # 5. 仓位调整
        position_adjustments = []
        
        if arbitrage_signals["coinbase_premium"]["signal"] == "bearish":
            position_adjustments.append("Coinbase折价：降低仓位20%")
        
        if kimchi_premium > 10 and nupl > 0.75:
            position_adjustments.append("泡菜溢价+NUPL过高：分批卖出")
        
        if stablecoin_discount > 0.5:
            position_adjustments.append("稳定币脱锚：观望或减仓")
        
        if abs(funding_rate) * 100 > 0.05:
            position_adjustments.append(f"极端资金费率：{entry_optimization['warning']}")

        return {
            "cycle_analysis": {
                "resonance_score": resonance.resonance_score,
                "dominant_direction": resonance.dominant_direction,
                "conflicts": resonance.conflict_count,
                "recommendation": resonance.recommendation
            },
            "arbitrage_signals": arbitrage_signals,
            "basis_signals": basis_signals,
            "funding_rate": {
                "rate": f"{funding_data.rate_pct:.3f}%",
                "annualized": f"{funding_data.rate_annualized:.1f}%",
                "interpretation": funding_data.interpretation
            },
            "final_signal": final_signal,
            "position_adjustments": position_adjustments,
            "entry_optimization": entry_optimization,
            "action_plan": self._generate_action_plan(
                final_signal, position_adjustments, phase
            )
        }

    def _generate_action_plan(
        self,
        signal: str,
        adjustments: List[str],
        phase: str
    ) -> Dict:
        """生成行动计划"""
        if signal == "bullish" and phase in ["B", "C", "D"]:
            if phase == "B":
                action = "识别边界，预设突破条件单"
                position = "50%"
            elif phase == "C":
                action = "提高敏感度，敢于追入"
                position = "70%"
            else:
                action = "持仓为主，回调加仓"
                position = "100%"
        elif signal == "bearish":
            action = "观望或轻仓，避免逆势"
            position = "20%"
        else:
            action = "等待信号明确"
            position = "持有底仓"

        return {
            "action": action,
            "recommended_position": position,
            "adjustments": adjustments,
            "risk_level": "high" if len(adjustments) > 2 else "medium" if len(adjustments) > 0 else "low"
        }


# =====================
# 测试
# =====================

if __name__ == "__main__":
    engine = NEMTSpatialTemporalEngine()
    
    # 模拟分析
    result = engine.run_full_analysis(
        macro_direction="bullish",
        strategic_direction="bullish",
        tactical_direction="neutral",
        execution_direction="bullish",
        coinbase_premium=0.5,
        kimchi_premium=3.5,
        stablecoin_discount=0.2,
        basis_pct=3.5,
        funding_rate=0.0001,
        nupl=0.6
    )
    
    print("\n[NEMT 时空决策分析结果]")
    print("=" * 70)
    
    print("\n[1] 多周期共振:")
    print(f"   共振分数: {result['cycle_analysis']['resonance_score']:.1f}/10")
    print(f"   主导方向: {result['cycle_analysis']['dominant_direction']}")
    print(f"   冲突数量: {result['cycle_analysis']['conflicts']}")
    print(f"   建议: {result['cycle_analysis']['recommendation']}")
    
    print("\n[2] 跨交易所信号:")
    print(f"   Coinbase溢价: {result['arbitrage_signals']['coinbase_premium']['value']} -> {result['arbitrage_signals']['coinbase_premium']['interpretation']}")
    print(f"   泡菜溢价: {result['arbitrage_signals']['kimchi_premium']['value']} -> {result['arbitrage_signals']['kimchi_premium']['interpretation']}")
    print(f"   稳定币: {result['arbitrage_signals']['stablecoin_depeg']['value']} -> {result['arbitrage_signals']['stablecoin_depeg']['interpretation']}")
    print(f"   综合信号: {result['arbitrage_signals']['composite_signal']}")
    
    print("\n[3] 期现结构:")
    print(f"   基差: {result['basis_signals']['basis']['value']} ({result['basis_signals']['basis']['type']})")
    print(f"   资金费率: {result['funding_rate']['rate']} (年化 {result['funding_rate']['annualized']})")
    
    print("\n[4] 最终信号:", result['final_signal'].upper())
    print("   行动计划:", result['action_plan']['action'])
    print("   建议仓位:", result['action_plan']['recommended_position'])
    
    if result['action_plan']['adjustments']:
        print("\n[5] 仓位调整:")
        for adj in result['action_plan']['adjustments']:
            print(f"   - {adj}")
