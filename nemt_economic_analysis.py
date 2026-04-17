"""
NEMT 第十章：市场非平衡视角下的经济因子分析
从宏观经济到比特币价格的NEMT传导模型

包含：
1. 三层能量传导模型
2. 核心经济因子NEMT解读
3. 货币政策与比特币周期
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


# =====================
# 能量层级定义
# =====================

class EnergyLevel(Enum):
    """能量层级"""
    FOUNDATION = "foundation"    # 基础能量：央行资产负债表
    MARGINAL = "marginal"       # 边际能量：边际收紧/宽松
    IMPULSE = "impulse"         # 脉冲能量：危机事件


@dataclass
class EnergyReading:
    """能量读数"""
    level: EnergyLevel
    value: float
    direction: str  # "expanding", "contracting", "neutral"
    score: float  # -2 到 +2
    interpretation: str


@dataclass
class EconomicIndicator:
    """经济指标"""
    name: str
    value: float
    unit: str
    previous_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


# =====================
# 全球流动性指标
# =====================

class GlobalLiquidityAnalyzer:
    """
    全球流动性分析器

    四大央行（美联储+欧央行+日央行+中国央行）资产负债表总和
    """

    # 能量分级阈值
    HIGH_ENERGY_THRESHOLD = 0.10      # >10% 高能注入
    MEDIUM_ENERGY_THRESHOLD = 0.05   # 5-10% 中能注入
    LOW_ENERGY_THRESHOLD = 0.0       # 0-5% 低能/中性
    # <0% 能量流出

    def __init__(self):
        self.history: List[EconomicIndicator] = []

    def calculate_liquidity_energy(
        self,
        current_balance_sheet: float,
        balance_12_months_ago: float
    ) -> EnergyReading:
        """
        计算流动性能量

        公式: (当前规模 / 12个月前规模) - 1
        """
        if balance_12_months_ago <= 0:
            energy = 0.0
        else:
            energy = (current_balance_sheet / balance_12_months_ago) - 1

        # 能量分级
        if energy > self.HIGH_ENERGY_THRESHOLD:
            level_desc = "高能注入"
            direction = "expanding"
            score = 2.0
            interpretation = "2020-2021年级别的史诗级宽松，驱动超级牛市"
        elif energy > self.MEDIUM_ENERGY_THRESHOLD:
            level_desc = "中能注入"
            direction = "expanding"
            score = 1.0
            interpretation = "正常宽松周期，支撑趋势上涨"
        elif energy > self.LOW_ENERGY_THRESHOLD:
            level_desc = "低能/中性"
            direction = "neutral"
            score = 0.0
            interpretation = "存量博弈，震荡为主"
        else:
            level_desc = "能量流出"
            direction = "contracting"
            score = -2.0
            interpretation = "缩表周期，系统性逆风"

        return EnergyReading(
            level=EnergyLevel.FOUNDATION,
            value=energy * 100,  # 转为百分比
            direction=direction,
            score=score,
            interpretation=interpretation
        )

    def get_macro_score_contribution(self, energy: EnergyReading) -> float:
        """
        计算对宏观评分的贡献
        """
        return energy.score

    def get_conduction_path(self) -> List[str]:
        """
        获取流动性传导路径
        """
        return [
            "1. 央行扩表/缩表",
            "2. 商业银行准备金变化",
            "3. 资金成本下降/上升",
            "4. 风险偏好变化",
            "5. 资金流向风险资产",
            "6. 财富效应",
            "7. 稳定币发行量变化",
            "8. 交易所弹药变化",
        ]

    def get_lead_lag_relationships(self) -> Dict[str, Tuple[str, str]]:
        """
        关键领先滞后关系
        """
        return {
            "balance_sheet_to_stablecoin": ("3-6个月", "央行资产负债表 -> 稳定币总市值"),
            "stablecoin_to_btc": ("1-2个月", "稳定币市值 -> 比特币价格"),
        }


# =====================
# 实际利率分析
# =====================

class RealRateAnalyzer:
    """
    实际利率分析器

    10年期TIPS收益率
    """

    def __init__(self):
        self.history: List[EconomicIndicator] = []

    def analyze_real_rate(
        self,
        tips_yield: float,
        tips_yield_1y_ago: Optional[float] = None,
        inflation_rate: Optional[float] = None
    ) -> Dict:
        """
        分析实际利率

        注意：实际利率的"二阶导"比水平更重要
        """
        result = {
            "current_rate": tips_yield,
            "level_signal": "neutral",
            "level_interpretation": "",
            "momentum_signal": "neutral",
            "momentum_interpretation": "",
            "macro_score_contribution": 0.0,
            "action": ""
        }

        # 绝对水平分析
        if tips_yield < 0:
            result["level_signal"] = "bullish"
            result["level_interpretation"] = "实际利率为负，宏观评分额外+1"
            result["macro_score_contribution"] += 1.0
        elif tips_yield > 2.0:
            result["level_signal"] = "bearish"
            result["level_interpretation"] = "实际利率高企，持有比特币机会成本大"
            result["macro_score_contribution"] -= 1.0
        else:
            result["level_interpretation"] = "实际利率处于中性区间"

        # 二阶导分析（变化速率）
        if tips_yield_1y_ago is not None:
            change = tips_yield - tips_yield_1y_ago
            result["yoy_change"] = change

            if change < -0.5:
                result["momentum_signal"] = "bullish"
                result["momentum_interpretation"] = "实际利率同比下降>0.5%，边际宽松，宏观评分+1"
                result["macro_score_contribution"] += 1.0
            elif change > 0.5:
                result["momentum_signal"] = "bearish"
                result["momentum_interpretation"] = "实际利率同比上升>0.5%，边际收紧，宏观评分-1"
                result["macro_score_contribution"] -= 1.0
            else:
                result["momentum_interpretation"] = "实际利率变化平稳"

        # 综合行动
        if result["momentum_signal"] == "bullish":
            result["action"] = "边际宽松，看涨信号，可适当提高风险敞口"
        elif result["momentum_signal"] == "bearish":
            result["action"] = "边际收紧，降低风险敞口，保护资本"
        elif result["level_signal"] == "bullish":
            result["action"] = "实际利率为负，额外看涨信号"
        else:
            result["action"] = "等待更多信息"

        return result


# =====================
# 美元指数分析
# =====================

class DollarIndexAnalyzer:
    """
    美元指数（DXY）分析器

    DXY对比特币的影响是情境依赖的
    """

    def __init__(self):
        self.context_indicators: Dict[str, bool] = {}

    def set_context(
        self,
        vix_rising: bool = False,
        treasury_yield_rising: bool = False,
        stock_market_rising: bool = True
    ):
        """
        设置市场背景

        Args:
            vix_rising: VIX指数是否上涨（避险情绪）
            treasury_yield_rising: 美债收益率是否上涨
            stock_market_rising: 美股是否上涨
        """
        self.context_indicators = {
            "vix_rising": vix_rising,
            "treasury_yield_rising": treasury_yield_rising,
            "stock_market_rising": stock_market_rising
        }

    def analyze_dxy_change(
        self,
        dxy_change_pct: float
    ) -> Dict:
        """
        分析DXY变化
        """
        result = {
            "dxy_change": dxy_change_pct,
            "signal": "neutral",
            "interpretation": "",
            "macro_score_adjustment": 0,
            "action": ""
        }

        if dxy_change_pct > 3.0:
            # DXY单月涨幅>3%，检查是否是避险驱动
            if self.context_indicators.get("vix_rising") and \
               self.context_indicators.get("treasury_yield_rising"):
                result["signal"] = "bearish"
                result["interpretation"] = "DXY上涨由避险驱动，比特币看跌"
                result["macro_score_adjustment"] = -1
                result["action"] = "降低风险暴露，宏观评分-1"
            else:
                result["signal"] = "neutral"
                result["interpretation"] = "DXY上涨但非避险驱动，以其他指标为准"
                result["action"] = "关注其他指标"
        elif dxy_change_pct > 0:
            if self.context_indicators.get("vix_rising"):
                result["signal"] = "bearish"
                result["interpretation"] = "DXY上涨由避险驱动（VIX同步上涨）"
                result["action"] = "谨慎，降低风险敞口"
            elif self.context_indicators.get("treasury_yield_rising") and \
                 self.context_indicators.get("stock_market_rising"):
                result["signal"] = "neutral"
                result["interpretation"] = "DXY上涨由增长驱动（美股不跌），中性"
                result["action"] = "以其他指标为准"
            else:
                result["interpretation"] = "DXY小幅上涨，无明确信号"
        elif dxy_change_pct < -3.0:
            result["signal"] = "bullish"
            result["interpretation"] = "DXY下跌，美元走弱，风险资产受益"
            result["action"] = "提高风险敞口"
        else:
            result["interpretation"] = "DXY变化平稳，无明确信号"

        return result


# =====================
# 信用利差分析
# =====================

class CreditSpreadAnalyzer:
    """
    信用利差分析器

    高收益债利差或Baa-Aaa公司债利差
    """

    def __init__(self):
        self.alert_levels = {
            "normal": 3.0,      # 正常 <3%
            "elevated": 5.0,    # 偏高 3-5%
            "stress": 7.0,       # 压力 >5%
            "crisis": 10.0      # 危机 >7%
        }

    def analyze_credit_spread(
        self,
        spread_bps: float,
        previous_spread: Optional[float] = None
    ) -> Dict:
        """
        分析信用利差

        Args:
            spread_bps: 信用利差（基点）
            previous_spread: 上一期利差
        """
        result = {
            "spread_bps": spread_bps,
            "alert_level": "normal",
            "signal": "neutral",
            "interpretation": "",
            "action": ""
        }

        # 利差水平判断
        if spread_bps < self.alert_levels["normal"]:
            result["alert_level"] = "normal"
            result["signal"] = "neutral"
            result["interpretation"] = "信用利差正常，系统风险低"
        elif spread_bps < self.alert_levels["elevated"]:
            result["alert_level"] = "elevated"
            result["signal"] = "caution"
            result["interpretation"] = "信用利差偏高，开始关注"
        elif spread_bps < self.alert_levels["stress"]:
            result["alert_level"] = "stress"
            result["signal"] = "bearish"
            result["interpretation"] = "信用利差扩大，系统性风险上升"
            result["action"] = "降低风险敞口，准备防御"
        elif spread_bps < self.alert_levels["crisis"]:
            result["alert_level"] = "crisis"
            result["signal"] = "bearish"
            result["interpretation"] = "信用利差危机水平，市场承压"
            result["action"] = "大幅降低仓位，启动黑天鹅预案"
        else:
            result["alert_level"] = "extreme_crisis"
            result["signal"] = "extreme_bearish"
            result["interpretation"] = "信用利差极端水平，系统性风险爆发"
            result["action"] = "清仓观望，保护资本"

        # 利差变化判断
        if previous_spread is not None:
            spread_change = spread_bps - previous_spread
            result["spread_change_bps"] = spread_change

            if spread_change > 100:  # 单日扩大超过100bps
                result["interpretation"] += "（利差急剧扩大）"
                result["action"] = "紧急减仓，流动性可能枯竭"
            elif spread_change > 50:  # 单周扩大超过50bps
                result["interpretation"] += "（利差快速扩大）"

        return result

    def get_historical_validation(self) -> Dict[str, str]:
        """
        历史验证案例
        """
        return {
            "2022_pre_bear": "2022年全年信用利差持续走阔，提前3-6个月预示比特币深熊",
            "2023_svb_crisis": "2023年3月硅谷银行危机期间，利差短暂飙升后迅速回落，对应比特币V型反转"
        }


# =====================
# 美联储政策分析
# =====================

class FedPolicyAnalyzer:
    """
    美联储政策分析器
    """

    # 政策周期阶段
    class PolicyCycle(Enum):
        TIGHTENING = "tightening"     # 紧缩
        PAUSE = "pause"               # 暂停
        EASING = "easing"             # 宽松
        HOLD = "hold"                 # 按兵不动

    def __init__(self):
        self.current_cycle = self.PolicyCycle.EASING  # 假设当前是降息周期中段

    def analyze_fomc_result(
        self,
        rate_change_bps: float,
        dot_plot_shift: float,  # 点阵图终端利率预期变化
        sep_gdp_change: float = 0,  # SEP中GDP预测调整
        hawkish_language: int = 0,  # 鹰派措辞增加程度 0-5
        dovish_language: int = 0    # 鸽派措辞增加程度 0-5
    ) -> Dict:
        """
        分析FOMC会议结果
        """
        result = {
            "rate_change_bps": rate_change_bps,
            "dot_plot_shift": dot_plot_shift,
            "overall_tone": "neutral",
            "macro_score_adjustment": 0,
            "interpretation": "",
            "actions": []
        }

        # 综合判断
        net_hawkishness = hawkish_language - dovish_language

        if dot_plot_shift < -25:  # 降息预期提前
            result["overall_tone"] = "dovish"
            result["macro_score_adjustment"] = 1
            result["interpretation"] = "点阵图显示降息预期提前，宏观评分+1"
            result["actions"].append("提高风险敞口")
        elif dot_plot_shift > 25:  # 降息预期推迟
            result["overall_tone"] = "hawkish"
            result["macro_score_adjustment"] = -1
            result["interpretation"] = "点阵图显示降息预期推迟，宏观评分-1"
            result["actions"].append("降低风险敞口")
        elif net_hawkishness > 2:  # 鹰派措辞明显增加
            result["overall_tone"] = "hawkish"
            result["macro_score_adjustment"] = -1
            result["interpretation"] = "鲍威尔强调通胀风险，宏观评分-1"
            result["actions"].append("谨慎操作")
        elif net_hawkishness < -2:  # 鸽派措辞明显增加
            result["overall_tone"] = "dovish"
            result["macro_score_adjustment"] = 1
            result["interpretation"] = "鲍威尔释放鸽派信号，宏观评分+1"
            result["actions"].append("可适度提高风险敞口")
        else:
            result["interpretation"] = "FOMC结果符合预期，无明显倾向"

        return result

    def get_cycle_phase_info(self) -> Dict:
        """
        获取当前周期阶段信息
        """
        return {
            "current_phase": self.current_cycle.value,
            "description": {
                self.PolicyCycle.TIGHTENING: "紧缩周期，比特币系统性逆风",
                self.PolicyCycle.PAUSE: "暂停加息，市场喘息期",
                self.PolicyCycle.EASING: "宽松周期，利好风险资产",
                self.PolicyCycle.HOLD: "按兵不动，观察期"
            }[self.current_cycle],
            "nemt_implications": {
                self.PolicyCycle.TIGHTENING: {
                    "liquidity_score": "3-4",
                    "risk_level": "high",
                    "recommended_position": "20-30%"
                },
                self.PolicyCycle.PAUSE: {
                    "liquidity_score": "5-6",
                    "risk_level": "medium",
                    "recommended_position": "40-50%"
                },
                self.PolicyCycle.EASING: {
                    "liquidity_score": "6-8",
                    "risk_level": "low",
                    "recommended_position": "60-100%"
                },
                self.PolicyCycle.HOLD: {
                    "liquidity_score": "5-6",
                    "risk_level": "medium",
                    "recommended_position": "40-60%"
                }
            }[self.current_cycle]
        }

    def analyze_halving_fed_cycle_resonance(
        self,
        halving_cycle: int,  # 1=2012, 2=2016, 3=2020, 4=2024
        fed_cycle: str,  # "tightening", "pause", "easing"
        halving_type: str = "halving_only"  # "halving_only", "pre_halving", "post_halving"
    ) -> Dict:
        """
        分析减半与美联储周期共振
        """
        # 历史规律
        historical_patterns = {
            1: {"fed": "easing", "result": "strong_bull"},
            2: {"fed": "pause", "result": "moderate_bull"},
            3: {"fed": "easing", "result": "strong_bull"},
        }

        result = {
            "cycle": halving_cycle,
            "halving_type": halving_type,
            "fed_cycle": fed_cycle,
            "resonance_score": 0,
            "signal": "neutral",
            "interpretation": "",
            "recommendation": ""
        }

        # 共振评分
        if fed_cycle == "easing":
            result["resonance_score"] += 2
        elif fed_cycle == "pause":
            result["resonance_score"] += 1
        elif fed_cycle == "tightening":
            result["resonance_score"] -= 2

        # 减半前后
        if halving_type == "pre_halving":
            result["resonance_score"] += 1  # 减半前通常有预期行情
        elif halving_type == "post_halving":
            result["resonance_score"] += 0.5  # 减半后供给减少效应

        # 信号判断
        if result["resonance_score"] >= 3:
            result["signal"] = "strong_bullish"
            result["interpretation"] = "减半 + 美联储宽松 = 最强牛市信号"
            result["recommendation"] = "满仓持有，回调加仓"
        elif result["resonance_score"] >= 1:
            result["signal"] = "bullish"
            result["interpretation"] = "减半 + 美联储宽松/中性 = 较强牛市"
            result["recommendation"] = "保持高仓位，回调买入"
        elif result["resonance_score"] <= -1:
            result["signal"] = "bearish"
            result["interpretation"] = "减半 + 美联储紧缩 = 结构性压制"
            result["recommendation"] = "降低仓位，等待周期转折"
        else:
            result["signal"] = "neutral"
            result["interpretation"] = "周期共振不明显，以其他信号为准"
            result["recommendation"] = "观望等待明确信号"

        return result


# =====================
# 综合经济分析引擎
# =====================

class NEMTEconomicAnalyzer:
    """
    NEMT经济分析引擎

    综合所有经济因子生成宏观评分和交易建议
    """

    def __init__(self):
        self.liquidity_analyzer = GlobalLiquidityAnalyzer()
        self.real_rate_analyzer = RealRateAnalyzer()
        self.dxy_analyzer = DollarIndexAnalyzer()
        self.credit_spread_analyzer = CreditSpreadAnalyzer()
        self.fed_analyzer = FedPolicyAnalyzer()

    def run_full_analysis(
        self,
        # 流动性数据
        current_balance_sheet: float = 0,
        balance_12_months_ago: float = 0,

        # 实际利率数据
        tips_yield: float = 0,
        tips_yield_1y_ago: float = 0,

        # DXY数据
        dxy_change_pct: float = 0,
        vix_rising: bool = False,
        treasury_yield_rising: bool = False,
        stock_market_rising: bool = True,

        # 信用利差数据
        credit_spread_bps: float = 3.0,
        credit_spread_previous: float = 3.0,

        # FOMC数据
        dot_plot_shift: float = 0,
        hawkish_language: int = 0,
        dovish_language: int = 0,

        # 减半周期
        halving_type: str = "post_halving",
        fed_cycle: str = "easing"
    ) -> Dict:
        """
        运行完整经济分析
        """
        results = {}

        # 1. 流动性分析
        liquidity = self.liquidity_analyzer.calculate_liquidity_energy(
            current_balance_sheet, balance_12_months_ago
        )
        results["liquidity"] = {
            "energy_pct": f"{liquidity.value:.1f}%",
            "direction": liquidity.direction,
            "score": liquidity.score,
            "interpretation": liquidity.interpretation
        }

        # 2. 实际利率分析
        self.real_rate_analyzer.history.append(
            EconomicIndicator("TIPS", tips_yield, "%")
        )
        real_rate_result = self.real_rate_analyzer.analyze_real_rate(
            tips_yield, tips_yield_1y_ago
        )
        results["real_rate"] = real_rate_result

        # 3. DXY分析
        self.dxy_analyzer.set_context(vix_rising, treasury_yield_rising, stock_market_rising)
        dxy_result = self.dxy_analyzer.analyze_dxy_change(dxy_change_pct)
        results["dxy"] = dxy_result

        # 4. 信用利差分析
        credit_result = self.credit_spread_analyzer.analyze_credit_spread(
            credit_spread_bps, credit_spread_previous
        )
        results["credit_spread"] = credit_result

        # 5. FOMC分析
        fomc_result = self.fed_analyzer.analyze_fomc_result(
            rate_change_bps=0,
            dot_plot_shift=dot_plot_shift,
            hawkish_language=hawkish_language,
            dovish_language=dovish_language
        )
        results["fomc"] = fomc_result

        # 6. 减半周期共振
        halving_resonance = self.fed_analyzer.analyze_halving_fed_cycle_resonance(
            halving_cycle=4,
            fed_cycle=fed_cycle,
            halving_type=halving_type
        )
        results["halving_resonance"] = halving_resonance

        # 7. 综合宏观评分
        total_score = 5.0  # 基准分

        # 加权汇总
        total_score += liquidity.score * 1.5  # 流动性权重最高
        total_score += real_rate_result["macro_score_contribution"]
        total_score += dxy_result["macro_score_adjustment"]

        if credit_result["signal"] in ["bearish", "extreme_bearish"]:
            total_score -= 1
        if credit_result["alert_level"] in ["stress", "crisis"]:
            total_score -= 2

        total_score += fomc_result["macro_score_adjustment"]

        # 限制范围
        total_score = max(0, min(10, total_score))

        # 评分解读
        if total_score >= 8:
            score_interpretation = "极度看涨"
            recommended_position = "80-100%"
        elif total_score >= 6:
            score_interpretation = "看涨"
            recommended_position = "60-80%"
        elif total_score >= 4:
            score_interpretation = "中性"
            recommended_position = "40-60%"
        elif total_score >= 2:
            score_interpretation = "看跌"
            recommended_position = "20-40%"
        else:
            score_interpretation = "极度看跌"
            recommended_position = "10-20%"

        results["composite"] = {
            "macro_score": total_score,
            "score_interpretation": score_interpretation,
            "recommended_position": recommended_position,
            "key_drivers": self._get_key_drivers(results),
            "risk_factors": self._get_risk_factors(results)
        }

        return results

    def _get_key_drivers(self, results: Dict) -> List[str]:
        """识别关键驱动因素"""
        drivers = []

        if results["liquidity"]["score"] > 0:
            drivers.append(f"流动性{results['liquidity']['direction']}（{results['liquidity']['energy_pct']}）")

        if results["real_rate"]["level_signal"] == "bullish":
            drivers.append("实际利率为负")

        if results["halving_resonance"]["signal"] in ["strong_bullish", "bullish"]:
            drivers.append("减半周期共振")

        if results["fomc"]["overall_tone"] == "dovish":
            drivers.append("FOMC释放鸽派信号")

        return drivers if drivers else ["无明确驱动因素"]

    def _get_risk_factors(self, results: Dict) -> List[str]:
        """识别风险因素"""
        risks = []

        if results["liquidity"]["score"] < 0:
            risks.append(f"流动性{results['liquidity']['direction']}（{results['liquidity']['energy_pct']}）")

        if results["credit_spread"]["signal"] in ["bearish", "extreme_bearish"]:
            risks.append(f"信用利差扩大（{results['credit_spread']['spread_bps']}bps）")

        if results["dxy"]["signal"] == "bearish":
            risks.append("DXY避险上涨")

        if results["fomc"]["overall_tone"] == "hawkish":
            risks.append("FOMC释放鹰派信号")

        return risks if risks else ["无明显风险"]


# =====================
# 测试
# =====================

if __name__ == "__main__":
    analyzer = NEMTEconomicAnalyzer()

    # 模拟2026年降息周期中段的分析
    result = analyzer.run_full_analysis(
        # 流动性：温和扩张
        current_balance_sheet=25e12,  # 25万亿美元
        balance_12_months_ago=24e12,

        # 实际利率：从高位回落
        tips_yield=1.2,
        tips_yield_1y_ago=1.8,

        # DXY：小幅下跌
        dxy_change_pct=-1.5,
        vix_rising=False,
        stock_market_rising=True,

        # 信用利差：正常
        credit_spread_bps=3.2,
        credit_spread_previous=3.0,

        # FOMC：鸽派
        dot_plot_shift=-25,
        dovish_language=3,

        # 减半周期
        halving_type="post_halving",
        fed_cycle="easing"
    )

    print("=" * 70)
    print("NEMT 经济因子分析报告")
    print("=" * 70)

    print("\n[1] 全球流动性")
    print(f"   能量: {result['liquidity']['energy_pct']}")
    print(f"   方向: {result['liquidity']['direction']}")
    print(f"   解读: {result['liquidity']['interpretation']}")

    print("\n[2] 实际利率")
    print(f"   当前水平: {result['real_rate']['current_rate']:.2f}%")
    print(f"   年变化: {result['real_rate'].get('yoy_change', 0):+.2f}%")
    print(f"   解读: {result['real_rate']['level_interpretation']}")
    print(f"   行动: {result['real_rate']['action']}")

    print("\n[3] 美元指数")
    print(f"   变化: {result['dxy']['dxy_change']:.1f}%")
    print(f"   信号: {result['dxy']['signal']}")
    print(f"   解读: {result['dxy']['interpretation']}")

    print("\n[4] 信用利差")
    print(f"   利差: {result['credit_spread']['spread_bps']}bps")
    print(f"   警戒级别: {result['credit_spread']['alert_level']}")
    print(f"   解读: {result['credit_spread']['interpretation']}")

    print("\n[5] FOMC")
    print(f"   整体基调: {result['fomc']['overall_tone']}")
    print(f"   解读: {result['fomc']['interpretation']}")

    print("\n[6] 减半周期共振")
    print(f"   共振分数: {result['halving_resonance']['resonance_score']}")
    print(f"   信号: {result['halving_resonance']['signal']}")
    print(f"   建议: {result['halving_resonance']['recommendation']}")

    print("\n" + "=" * 70)
    print("[综合宏观评分]")
    print("=" * 70)
    print(f"\n宏观评分: {result['composite']['macro_score']:.1f}/10")
    print(f"解读: {result['composite']['score_interpretation']}")
    print(f"建议仓位: {result['composite']['recommended_position']}")

    print("\n关键驱动因素:")
    for driver in result['composite']['key_drivers']:
        print(f"   - {driver}")

    if result['composite']['risk_factors']:
        print("\n风险因素:")
        for risk in result['composite']['risk_factors']:
            print(f"   - {risk}")
