"""
NEMT 第十二章：趋势概率与执行优化
从分析到盈利的最后一环

包含：
1. 趋势概率综合评估模型
2. 四维概率输入
3. 概率合成公式
4. 贝叶斯更新框架
5. 执行优化
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import math


# =====================
# 交易周期类型
# =====================

class TradeHorizon(Enum):
    """交易周期"""
    LONG_TERM = "long_term"      # 长线持仓>3个月
    MID_TERM = "mid_term"        # 中线持仓2-8周
    SHORT_TERM = "short_term"    # 短线持仓1-5天


# =====================
# 四维概率输入
# =====================

@dataclass
class ProbabilityInputs:
    """概率输入"""
    p_macro: float = 0.5         # 宏观支持概率
    p_onchain: float = 0.5       # 链上结构概率
    p_phase: float = 0.5          # 结构相位概率
    p_spacetime: float = 0.5      # 时空共振概率


@dataclass
class ProbabilityModifiers:
    """概率修正项"""
    # 宏观修正
    real_rate_declining: bool = False      # 实际利率同比下降>0.5%
    credit_spread_widening: bool = False   # 信用利差走阔>20%
    halving_main_window: bool = False      # 减半后6-18个月

    # 链上修正
    btc_exchange_withdrawal: bool = False   # 交易所BTC余额月降幅>5%
    stablecoin_deposit_increase: bool = False  # 稳定币交易所余额月增幅>10%
    whale_inflow_3days: bool = False       # 鲸鱼连续3日净流入交易所

    # 相位修正
    resonance_3_conditions: bool = False   # 随机共振三条件全部满足
    soliton_4_features: bool = False      # 孤子五特征满足四项以上
    noise_burst: bool = False              # 出现噪声暴


# =====================
# 趋势概率模型
# =====================

class TrendProbabilityModel:
    """
    趋势概率综合评估模型
    """

    # 各周期的权重配置
    HORIZON_WEIGHTS = {
        TradeHorizon.LONG_TERM: {
            "p_macro": 0.35,
            "p_onchain": 0.35,
            "p_phase": 0.15,
            "p_spacetime": 0.15
        },
        TradeHorizon.MID_TERM: {
            "p_macro": 0.25,
            "p_onchain": 0.30,
            "p_phase": 0.25,
            "p_spacetime": 0.20
        },
        TradeHorizon.SHORT_TERM: {
            "p_macro": 0.15,
            "p_onchain": 0.20,
            "p_phase": 0.40,
            "p_spacetime": 0.25
        }
    }

    # 修正项加成
    MODIFIER_BONUSES = {
        # 宏观
        "real_rate_declining": 0.10,
        "credit_spread_widening": -0.15,
        "halving_main_window": 0.10,
        # 链上
        "btc_exchange_withdrawal": 0.10,
        "stablecoin_deposit_increase": 0.05,
        "whale_inflow_3days": -0.10,
        # 相位
        "resonance_3_conditions": 0.15,
        "soliton_4_features": 0.10,
        "noise_burst": -0.20
    }

    def __init__(self):
        self.current_p_trend = 0.5
        self.update_history: List[Dict] = []

    def apply_modifiers(
        self,
        base_prob: float,
        modifiers: ProbabilityModifiers,
        dimension: str
    ) -> float:
        """
        应用修正项到基础概率
        """
        prob = base_prob

        if dimension == "macro":
            if modifiers.real_rate_declining:
                prob += self.MODIFIER_BONUSES["real_rate_declining"]
            if modifiers.credit_spread_widening:
                prob += self.MODIFIER_BONUSES["credit_spread_widening"]
            if modifiers.halving_main_window:
                prob += self.MODIFIER_BONUSES["halving_main_window"]
        elif dimension == "onchain":
            if modifiers.btc_exchange_withdrawal:
                prob += self.MODIFIER_BONUSES["btc_exchange_withdrawal"]
            if modifiers.stablecoin_deposit_increase:
                prob += self.MODIFIER_BONUSES["stablecoin_deposit_increase"]
            if modifiers.whale_inflow_3days:
                prob += self.MODIFIER_BONUSES["whale_inflow_3days"]
        elif dimension == "phase":
            if modifiers.resonance_3_conditions:
                prob += self.MODIFIER_BONUSES["resonance_3_conditions"]
            if modifiers.soliton_4_features:
                prob += self.MODIFIER_BONUSES["soliton_4_features"]
            if modifiers.noise_burst:
                prob += self.MODIFIER_BONUSES["noise_burst"]

        # 限制范围
        return max(0.05, min(0.95, prob))

    def calculate_p_trend(
        self,
        inputs: ProbabilityInputs,
        modifiers: ProbabilityModifiers,
        horizon: TradeHorizon = TradeHorizon.MID_TERM
    ) -> Dict:
        """
        计算趋势概率

        使用加权几何平均
        """
        weights = self.HORIZON_WEIGHTS[horizon]

        # 应用修正项
        p_macro = self.apply_modifiers(inputs.p_macro, modifiers, "macro")
        p_onchain = self.apply_modifiers(inputs.p_onchain, modifiers, "onchain")
        p_phase = self.apply_modifiers(inputs.p_phase, modifiers, "phase")
        p_spacetime = inputs.p_spacetime  # 时空暂无修正项

        # 加权几何平均
        # P_trend = (P1^w1 * P2^w2 * P3^w3 * P4^w4)^(1/(w1+w2+w3+w4))
        try:
            log_sum = (
                weights["p_macro"] * math.log(max(0.01, p_macro)) +
                weights["p_onchain"] * math.log(max(0.01, p_onchain)) +
                weights["p_phase"] * math.log(max(0.01, p_phase)) +
                weights["p_spacetime"] * math.log(max(0.01, p_spacetime))
            )
            p_trend = math.exp(log_sum)
        except:
            p_trend = (p_macro + p_onchain + p_phase + p_spacetime) / 4

        # 更新当前概率
        self.current_p_trend = p_trend

        return {
            "p_trend": p_trend,
            "p_macro": p_macro,
            "p_onchain": p_onchain,
            "p_phase": p_phase,
            "p_spacetime": p_spacetime,
            "horizon": horizon.value,
            "weights": weights
        }

    def get_position_coefficient(self, p_trend: float) -> float:
        """
        概率到仓位的映射

        仓位系数
        """
        if p_trend >= 0.80:
            return 1.0
        elif p_trend >= 0.70:
            return 0.8
        elif p_trend >= 0.60:
            return 0.6
        elif p_trend >= 0.50:
            return 0.4
        else:
            return 0.0

    def calculate_position(
        self,
        p_trend: float,
        phase_max_position: float
    ) -> Dict:
        """
        计算实际仓位
        """
        coef = self.get_position_coefficient(p_trend)
        position = phase_max_position * coef

        return {
            "position_pct": position * 100,
            "coefficient": coef,
            "phase_max": phase_max_position * 100,
            "action": self._get_position_action(position)
        }

    def _get_position_action(self, position: float) -> str:
        """获取仓位建议"""
        if position >= 0.8:
            return "重仓持有，趋势明确"
        elif position >= 0.5:
            return "标准仓位"
        elif position >= 0.3:
            return "轻仓试探"
        else:
            return "观望或清仓"


# =====================
# 贝叶斯更新模型
# =====================

@dataclass
class EvidenceLikelihood:
    """证据似然比"""
    evidence: str
    p_e_given_h: float    # 趋势为真时观察到该证据的概率
    p_e_given_not_h: float  # 趋势为假时观察到该证据的概率
    likelihood_ratio: float  # 似然比 = P(E|H) / P(E|~H)


class BayesianUpdateModel:
    """
    贝叶斯更新框架

    用于根据新证据动态更新趋势概率
    """

    # 预设的常见证据似然比
    PRESET_EVIDENCES = {
        # 看多证据
        "breakout_confirmed": {
            "p_e_given_h": 0.85,
            "p_e_given_not_h": 0.30,
            "description": "突破确认（量价配合）"
        },
        "dci_sustained_above_0.7": {
            "p_e_given_h": 0.80,
            "p_e_given_not_h": 0.25,
            "description": "DCI持续高于0.7超过5天"
        },
        "oi_following": {
            "p_e_given_h": 0.75,
            "p_e_given_not_h": 0.35,
            "description": "OI跟随价格上涨"
        },
        "whale_accumulation": {
            "p_e_given_h": 0.70,
            "p_e_given_not_h": 0.40,
            "description": "鲸鱼累积信号"
        },
        "macro_score_improving": {
            "p_e_given_h": 0.70,
            "p_e_given_not_h": 0.45,
            "description": "宏观评分持续改善"
        },

        # 看空证据
        "fake_breakout": {
            "p_e_given_h": 0.15,
            "p_e_given_not_h": 0.70,
            "description": "假突破后回落"
        },
        "dci_divergence": {
            "p_e_given_h": 0.20,
            "p_e_given_not_h": 0.65,
            "description": "DCI与价格背离"
        },
        "oi_drop": {
            "p_e_given_h": 0.25,
            "p_e_given_not_h": 0.60,
            "description": "OI下跌伴随价格上涨"
        },
        "volume_decline": {
            "p_e_given_h": 0.30,
            "p_e_given_not_h": 0.55,
            "description": "上涨时成交量萎缩"
        },
        "noise_burst": {
            "p_e_given_h": 0.10,
            "p_e_given_not_h": 0.80,
            "description": "噪声暴出现"
        },

        # 中性/混合证据
        "consolidation": {
            "p_e_given_h": 0.60,
            "p_e_given_not_h": 0.50,
            "description": "盘整（正常调整）"
        }
    }

    def bayesian_update(
        self,
        p_old: float,
        evidence_key: str,
        custom_likelihood: Optional[Tuple[float, float]] = None
    ) -> Dict:
        """
        贝叶斯更新

        P_new = P(E|H) * P_old / (P(E|H) * P_old + P(E|~H) * (1-P_old))
        """
        if custom_likelihood:
            p_e_given_h = custom_likelihood[0]
            p_e_given_not_h = custom_likelihood[1]
        elif evidence_key in self.PRESET_EVIDENCES:
            ev = self.PRESET_EVIDENCES[evidence_key]
            p_e_given_h = ev["p_e_given_h"]
            p_e_given_not_h = ev["p_e_given_not_h"]
        else:
            return {
                "p_new": p_old,
                "p_old": p_old,
                "evidence": evidence_key,
                "error": "未知证据类型"
            }

        # 计算似然比
        likelihood_ratio = p_e_given_h / p_e_given_not_h if p_e_given_not_h > 0 else 1.0

        # 贝叶斯公式
        numerator = p_e_given_h * p_old
        denominator = p_e_given_h * p_old + p_e_given_not_h * (1 - p_old)

        if denominator > 0:
            p_new = numerator / denominator
        else:
            p_new = p_old

        return {
            "p_new": p_new,
            "p_old": p_old,
            "p_change": p_new - p_old,
            "evidence": evidence_key,
            "evidence_description": self.PRESET_EVIDENCES.get(evidence_key, {}).get("description", ""),
            "p_e_given_h": p_e_given_h,
            "p_e_given_not_h": p_e_given_not_h,
            "likelihood_ratio": likelihood_ratio,
            "is_confirming": p_new > p_old
        }

    def simplified_update(
        self,
        p_old: float,
        signal: str  # "bullish", "bearish", "neutral"
    ) -> float:
        """
        简化的概率调整

        规则：
        - 确认证据出现：P + 0.10
        - 否定证据出现：P - 0.15
        - 中性证据：P 不变
        """
        if signal == "bullish":
            return max(0.05, min(0.95, p_old + 0.10))
        elif signal == "bearish":
            return max(0.05, min(0.95, p_old - 0.15))
        else:
            return p_old

    def should_exit(self, p_trend: float) -> bool:
        """
        判断是否应该离场

        P_trend < 0.50 时启动离场程序
        """
        return p_trend < 0.50


# =====================
# 执行优化模型
# =====================

@dataclass
class ExecutionPlan:
    """执行计划"""
    order_type: str           # "twap", "vwap", "market"
    num_splits: int           # 分批数量
    split_interval_minutes: int  # 每批间隔分钟数
    avoid_funding_times: List[str]  # 应避开的时间
    liquidity_check_passed: bool


@dataclass
class StopLossPlan:
    """止损计划"""
    atr_distance: float        # ATR距离止损
    atr_multiplier: float      # ATR倍数K
    structure_distance: float  # 结构止损距离
    final_stop_loss: float     # 最终止损位
    stop_loss_pct: float       # 止损百分比


class ExecutionOptimizer:
    """
    执行优化模型

    入场滑点控制、最优止损位
    """

    # ATR倍数K（根据P_trend调整）
    ATR_MULTIPLIERS = {
        (0.80, 1.0): 1.5,   # 高概率，轻止损
        (0.60, 0.80): 2.0,
        (0.40, 0.60): 2.5,
        (0.20, 0.40): 3.0,   # 低概率，宽止损
    }

    # 资金费率结算时刻
    FUNDING_SETTLEMENT_TIMES = ["UTC 00:00", "UTC 08:00", "UTC 16:00"]
    AVOID_WINDOW_MINUTES = 10

    def __init__(self):
        self.bayesian_model = BayesianUpdateModel()

    def create_entry_plan(
        self,
        position_size_usd: float,
        current_price: float,
        order_type: str = "twap"
    ) -> ExecutionPlan:
        """
        创建入场执行计划

        Args:
            position_size_usd: 仓位大小（美元）
            current_price: 当前价格
            order_type: 订单类型
        """
        # 分批数量参考
        if position_size_usd <= 10000:
            num_splits = 1
        elif position_size_usd <= 50000:
            num_splits = 3
        elif position_size_usd <= 100000:
            num_splits = 5
        elif position_size_usd <= 500000:
            num_splits = 8
        else:
            num_splits = 10

        # 每批间隔
        split_interval = 3 if num_splits <= 5 else 5

        # 检查流动性（简化版）
        # 假设前10档卖盘总量为仓位的5倍视为深度足够
        liquidity_check_passed = True  # 实际应检查订单簿

        return ExecutionPlan(
            order_type=order_type,
            num_splits=num_splits,
            split_interval_minutes=split_interval,
            avoid_funding_times=self.FUNDING_SETTLEMENT_TIMES,
            liquidity_check_passed=liquidity_check_passed
        )

    def calculate_stop_loss(
        self,
        atr: float,
        current_price: float,
        p_trend: float,
        entry_price: float,
        is_long: bool = True,
        # 结构支撑/阻力位
        vortex_mid: Optional[float] = None,
        recent_low: Optional[float] = None,
        lth_cost_basis: Optional[float] = None
    ) -> StopLossPlan:
        """
        计算最优止损位

        步骤一：ATR基础止损
        步骤二：结构约束
        """
        # ATR倍数K
        atr_multiplier = 2.0  # 默认值
        for (low, high), k in self.ATR_MULTIPLIERS.items():
            if low <= p_trend < high:
                atr_multiplier = k
                break

        atr_distance = atr * atr_multiplier

        # 结构止损位（多头）
        structure_distance = float('inf')
        structure_level = None

        if is_long:
            # 多头止损必须在关键支撑之下
            candidates = []
            if vortex_mid:
                candidates.append(("涡旋区间中轴", vortex_mid))
            if recent_low:
                candidates.append(("近期低点", recent_low))
            if lth_cost_basis:
                candidates.append(("LTH成本基础", lth_cost_basis))

            # 取最小值作为结构止损参考
            if candidates:
                _, min_level = min(candidates, key=lambda x: abs(x[1] - entry_price))
                structure_distance = entry_price - min_level
                structure_level = min_level
        else:
            # 空头止损必须在关键阻力之上
            candidates = []
            if vortex_mid:
                candidates.append(("涡旋区间中轴", vortex_mid))
            if recent_low:
                candidates.append(("近期高点", recent_low))

            if candidates:
                _, max_level = max(candidates, key=lambda x: abs(x[1] - entry_price))
                structure_distance = max_level - entry_price
                structure_level = max_level

        # 取ATR和结构的较小值
        if atr_distance < structure_distance:
            final_distance = atr_distance
            constraint_type = "atr"
        else:
            final_distance = structure_distance
            constraint_type = "structure"

        # 计算止损价格
        if is_long:
            final_stop = entry_price - final_distance
        else:
            final_stop = entry_price + final_distance

        stop_loss_pct = (final_distance / entry_price) * 100

        return StopLossPlan(
            atr_distance=atr_distance,
            atr_multiplier=atr_multiplier,
            structure_distance=structure_distance if structure_distance != float('inf') else 0,
            final_stop_loss=final_stop,
            stop_loss_pct=stop_loss_pct
        )

    def get_trailing_stop(
        self,
        current_price: float,
        entry_price: float,
        highest_price: float,
        atr: float,
        phase: str,
        is_long: bool = True
    ) -> Dict:
        """
        计算移动止损
        """
        # 基础移动止损
        if is_long:
            # 从最高点回落一定比例/ATR
            pullback_threshold = atr * 1.5  # 回落1.5倍ATR
            trailing_stop = highest_price - pullback_threshold

            # 不能低于入场价
            trailing_stop = max(trailing_stop, entry_price)

            # 保本价
            breakeven = entry_price
        else:
            pullback_threshold = atr * 1.5
            trailing_stop = lowest_price + pullback_threshold if 'lowest_price' in dir() else current_price + atr * 1.5
            trailing_stop = min(trailing_stop, entry_price)
            breakeven = entry_price

        # 根据相位调整
        if phase in ["C", "D"]:
            # 趋势相位，可以更紧的移动止损
            if is_long:
                trailing_stop = max(trailing_stop, highest_price * 0.95)  # 不超过最高点5%
            else:
                trailing_stop = min(trailing_stop, lowest_price * 1.05 if 'lowest_price' in dir() else current_price * 1.05)

        return {
            "trailing_stop": trailing_stop,
            "pullback_threshold": pullback_threshold,
            "breakeven": breakeven,
            "current_profit_pct": ((current_price - entry_price) / entry_price) * 100 if is_long else ((entry_price - current_price) / entry_price) * 100
        }


# =====================
# 综合概率执行引擎
# =====================

class NEMTProbabilityEngine:
    """
    NEMT 概率执行引擎

    综合趋势概率、贝叶斯更新、执行优化
    """

    def __init__(self):
        self.probability_model = TrendProbabilityModel()
        self.bayesian_model = BayesianUpdateModel()
        self.execution_optimizer = ExecutionOptimizer()

    def analyze_and_plan(
        self,
        # 概率输入
        p_macro: float = 0.5,
        p_onchain: float = 0.5,
        p_phase: float = 0.5,
        p_spacetime: float = 0.5,

        # 修正项
        modifiers: Optional[ProbabilityModifiers] = None,

        # 交易周期
        horizon: TradeHorizon = TradeHorizon.MID_TERM,

        # 相位最大仓位
        phase_max_position: float = 0.7,

        # 执行参数
        position_size_usd: float = 10000,
        atr: float = 2000,
        current_price: float = 60000,

        # 结构位
        vortex_mid: Optional[float] = None,
        recent_low: Optional[float] = None,
        lth_cost_basis: Optional[float] = None,
    ) -> Dict:
        """
        运行完整的概率分析和执行规划
        """
        if modifiers is None:
            modifiers = ProbabilityModifiers()

        # 1. 计算趋势概率
        prob_result = self.probability_model.calculate_p_trend(
            inputs=ProbabilityInputs(
                p_macro=p_macro,
                p_onchain=p_onchain,
                p_phase=p_phase,
                p_spacetime=p_spacetime
            ),
            modifiers=modifiers,
            horizon=horizon
        )

        # 2. 计算仓位
        position_result = self.probability_model.calculate_position(
            p_trend=prob_result["p_trend"],
            phase_max_position=phase_max_position
        )

        # 3. 创建执行计划
        execution_plan = self.execution_optimizer.create_entry_plan(
            position_size_usd=position_size_usd,
            current_price=current_price
        )

        # 4. 计算止损
        stop_loss_plan = self.execution_optimizer.calculate_stop_loss(
            atr=atr,
            current_price=current_price,
            p_trend=prob_result["p_trend"],
            entry_price=current_price,  # 假设以当前价入场
            vortex_mid=vortex_mid,
            recent_low=recent_low,
            lth_cost_basis=lth_cost_basis
        )

        # 5. 综合判断
        should_enter = prob_result["p_trend"] >= 0.50
        should_exit = self.bayesian_model.should_exit(prob_result["p_trend"])

        return {
            # 概率分析
            "probability": {
                "p_trend": f"{prob_result['p_trend']:.1%}",
                "p_macro": f"{prob_result['p_macro']:.1%}",
                "p_onchain": f"{prob_result['p_onchain']:.1%}",
                "p_phase": f"{prob_result['p_phase']:.1%}",
                "p_spacetime": f"{prob_result['p_spacetime']:.1%}",
                "horizon": horizon.value
            },
            # 仓位建议
            "position": {
                "recommended_pct": f"{position_result['position_pct']:.0f}%",
                "coefficient": position_result["coefficient"],
                "action": position_result["action"]
            },
            # 执行计划
            "execution": {
                "order_type": execution_plan.order_type,
                "num_splits": execution_plan.num_splits,
                "split_interval": f"{execution_plan.split_interval_minutes}分钟",
                "avoid_times": execution_plan.avoid_funding_times,
                "liquidity_check": "通过" if execution_plan.liquidity_check_passed else "失败"
            },
            # 止损计划
            "stop_loss": {
                "atr_distance": f"${stop_loss_plan.atr_distance:.0f}",
                "atr_multiplier": stop_loss_plan.atr_multiplier,
                "stop_price": f"${stop_loss_plan.final_stop_loss:.0f}",
                "stop_loss_pct": f"{stop_loss_plan.stop_loss_pct:.1f}%"
            },
            # 综合决策
            "decision": {
                "should_enter": should_enter,
                "should_exit": should_exit,
                "confidence": "高" if prob_result["p_trend"] >= 0.7 else "中" if prob_result["p_trend"] >= 0.5 else "低"
            }
        }


# =====================
# 测试
# =====================

if __name__ == "__main__":
    engine = NEMTProbabilityEngine()

    # 计算示例
    result = engine.analyze_and_plan(
        p_macro=0.65,      # 宏观评分6
        p_onchain=0.80,    # 链上评分7
        p_phase=0.75,      # 相位C，随机共振触发
        p_spacetime=0.65,  # 时空评分2

        modifiers=ProbabilityModifiers(
            resonance_3_conditions=True,  # 随机共振三条件全部满足
            halving_main_window=True,     # 减半后6-18个月
        ),

        horizon=TradeHorizon.MID_TERM,
        phase_max_position=0.70,  # 相位C上限70%

        position_size_usd=50000,
        atr=2000,
        current_price=60000,

        vortex_mid=58000,
        recent_low=55000,
    )

    print("=" * 70)
    print("NEMT 趋势概率与执行优化分析")
    print("=" * 70)

    print("\n[概率分析]")
    for key, value in result["probability"].items():
        print(f"   {key}: {value}")

    print("\n[仓位建议]")
    print(f"   推荐仓位: {result['position']['recommended_pct']}")
    print(f"   仓位系数: {result['position']['coefficient']}")
    print(f"   行动: {result['position']['action']}")

    print("\n[执行计划]")
    print(f"   订单类型: {result['execution']['order_type']}")
    print(f"   分批数量: {result['execution']['num_splits']}")
    print(f"   间隔: {result['execution']['split_interval']}")
    print(f"   避开时刻: {result['execution']['avoid_times']}")

    print("\n[止损计划]")
    print(f"   ATR距离: {result['stop_loss']['atr_distance']}")
    print(f"   ATR倍数: {result['stop_loss']['atr_multiplier']}")
    print(f"   止损位: {result['stop_loss']['stop_price']}")
    print(f"   止损%: {result['stop_loss']['stop_loss_pct']}")

    print("\n[综合决策]")
    print(f"   入场: {'是' if result['decision']['should_enter'] else '否'}")
    print(f"   离场: {'是' if result['decision']['should_exit'] else '否'}")
    print(f"   信心: {result['decision']['confidence']}")

    print("\n" + "=" * 70)
    print("贝叶斯更新示例")
    print("=" * 70)

    bayesian = BayesianUpdateModel()
    p_old = 0.71

    # 假设出现假突破
    update1 = bayesian.bayesian_update(p_old, "fake_breakout")
    print(f"\n假突破后: {p_old:.1%} -> {update1['p_new']:.1%}")

    # 假设DCI持续高于0.7
    update2 = bayesian.bayesian_update(p_old, "dci_sustained_above_0.7")
    print(f"DCI持续确认: {p_old:.1%} -> {update2['p_new']:.1%}")
