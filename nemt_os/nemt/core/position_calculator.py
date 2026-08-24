"""
PositionCalculator - 仓位计算引擎

提供多种仓位计算算法:
- DynamicRiskCalculator: 动态风险计算器
- HybridPositionAlgorithm: 复合算法 (ATR + 凯利 + 信心度)
- KellyCalculator: 凯利公式计算器
- ATRCalculator: ATR 波动率计算
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


__all__ = [
    "PositionCalculator",
    "PositionResult",
    "RiskTier",
    "AlgoMode",
    "KellyCalculator",
    "ATRCalculator",
    "DynamicRiskCalculator",
    "HybridPositionAlgorithm",
]


class RiskTier(Enum):
    """风险等级"""

    MICRO = "micro"  # < 1万
    SMALL = "small"  # 1-10万
    MEDIUM = "medium"  # 10-100万
    LARGE = "large"  # > 100万


class AlgoMode(Enum):
    """算法模式"""

    SIMPLE = "simple"  # 简单动态百分比
    HYBRID = "hybrid"  # ATR + 凯利 + 信心度复合算法


@dataclass
class PositionResult:
    """
    仓位计算结果

    Attributes:
        position_value: 建议仓位金额
        position_pct: 仓位百分比 (0.0 - 1.0)
        contracts: 合约/股数
        risk_amount: 风险金额
        risk_tier: 风险等级
        algo_mode: 使用的算法模式
        methods: 各算法贡献 (hybrid 模式时)
        timestamp: 计算时间
    """

    position_value: float
    position_pct: float
    contracts: float
    risk_amount: float
    risk_tier: RiskTier
    algo_mode: AlgoMode
    methods: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_value": self.position_value,
            "position_pct": self.position_pct,
            "contracts": self.contracts,
            "risk_amount": self.risk_amount,
            "risk_tier": self.risk_tier.value,
            "algo_mode": self.algo_mode.value,
            "methods": self.methods,
            "timestamp": self.timestamp,
        }


class KellyCalculator:
    """
    凯利公式计算器

    凯利公式: f = (b * p - q) / b
    其中:
        b = 赔率 (reward_ratio)
        p = 胜率 (win_rate)
        q = 败率 (1 - p)

    为了控制风险，通常使用半凯利 (f * 0.5) 或四分之一凯利 (f * 0.25)
    """

    DEFAULT_KELLY_MULTIPLIER = 0.5  # 半凯利
    MAX_POSITION_FRACTION = 0.25  # 最大仓位不超过25%

    def __init__(self, kelly_multiplier: float = DEFAULT_KELLY_MULTIPLIER):
        """
        初始化凯利计算器

        Args:
            kelly_multiplier: 凯利系数乘数，默认半凯利 (0.5)
        """
        self._kelly_multiplier = kelly_multiplier

    def calculate(
        self,
        equity: float,
        win_rate: float,
        reward_ratio: float,
        entry_price: float,
    ) -> Dict[str, Any]:
        """
        计算凯利公式仓位

        Args:
            equity: 当前权益
            win_rate: 胜率 (0.0 - 1.0)
            reward_ratio: 盈亏比 (如 2.0 表示盈利是亏损的2倍)
            entry_price: 入场价格

        Returns:
            包含凯利仓位和建议交易量的字典
        """
        # 验证输入
        win_rate = max(0.0, min(1.0, win_rate))
        reward_ratio = max(0.01, reward_ratio)

        # 计算凯利 fraction
        b = reward_ratio
        p = win_rate
        q = 1 - p

        kelly_fraction = (b * p - q) / b

        # 应用保守系数
        conservative_fraction = kelly_fraction * self._kelly_multiplier

        # 限制在合理范围内
        safe_fraction = max(0.0, min(conservative_fraction, self.MAX_POSITION_FRACTION))

        # 计算仓位
        position_value = equity * safe_fraction
        contracts = position_value / entry_price if entry_price > 0 else 0

        # 计算期望收益
        expected_return = (p * reward_ratio) - q

        return {
            "kelly_fraction": kelly_fraction,
            "conservative_fraction": conservative_fraction,
            "safe_fraction": safe_fraction,
            "position_value": position_value,
            "contracts": contracts,
            "expected_return": expected_return,
            "win_rate": win_rate,
            "reward_ratio": reward_ratio,
        }

    def suggest_win_rate(
        self,
        kelly_fraction: float,
        reward_ratio: float,
    ) -> float:
        """
        根据凯利仓位反推需要的胜率

        Args:
            kelly_fraction: 目标凯利仓位比例
            reward_ratio: 盈亏比

        Returns:
            需要的胜率
        """
        # f = (b * p - q) / b
        # f = (b * p - (1 - p)) / b
        # f * b = b * p - 1 + p
        # b * p + p = f * b + 1
        # p * (b + 1) = f * b + 1
        # p = (f * b + 1) / (b + 1)

        b = reward_ratio
        p = (kelly_fraction * b + 1) / (b + 1)
        return max(0.0, min(1.0, p))


class ATRCalculator:
    """
    ATR (Average True Range) 波动率计算器

    ATR 是衡量市场波动的指标，用于计算基于波动率的止损和仓位
    """

    DEFAULT_ATR_PERIOD = 14

    def __init__(self, period: int = DEFAULT_ATR_PERIOD):
        """
        初始化 ATR 计算器

        Args:
            period: ATR 周期，默认14
        """
        self._period = period
        self._tr_list: List[float] = []

    def update(self, high: float, low: float, close: float, prev_close: float = 0) -> float:
        """
        更新数据并计算 ATR

        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            prev_close: 前一收盘价

        Returns:
            当前 ATR 值
        """
        tr = self._calc_true_range(high, low, close, prev_close)
        self._tr_list.append(tr)

        # 保持固定长度
        if len(self._tr_list) > self._period * 2:
            self._tr_list = self._tr_list[-self._period * 2 :]

        return self.get_atr()

    def get_atr(self) -> float:
        """
        获取当前 ATR 值 (使用指数移动平均)

        Returns:
            ATR 值
        """
        if len(self._tr_list) < self._period:
            return sum(self._tr_list) / len(self._tr_list) if self._tr_list else 0.0

        # 使用简单移动平均 (可用 EMA 替代)
        recent_tr = self._tr_list[-self._period :]
        return sum(recent_tr) / self._period

    def get_atr_percent(self, current_price: float) -> float:
        """
        获取 ATR 占当前价格的百分比

        Args:
            current_price: 当前价格

        Returns:
            ATR 百分比 (如 0.02 表示 2%)
        """
        if current_price <= 0:
            return 0.0
        return self.get_atr() / current_price

    @staticmethod
    def _calc_true_range(high: float, low: float, close: float, prev_close: float) -> float:
        """
        计算 True Range

        TR = max(H - L, |H - PC|, |L - PC|)
        其中 PC 是前一个收盘价
        """
        if prev_close <= 0:
            return high - low

        hl = high - low
        hpc = abs(high - prev_close)
        lpc = abs(low - prev_close)

        return max(hl, hpc, lpc)

    def calculate_position_size(
        self,
        equity: float,
        risk_amount: float,
        entry_price: float,
        atr_multiplier: float = 2.0,
    ) -> Dict[str, Any]:
        """
        基于 ATR 计算仓位大小

        Args:
            equity: 当前权益
            risk_amount: 风险金额 (如 equity * 0.03 表示3%风险)
            entry_price: 入场价格
            atr_multiplier: ATR 倍数 (用于止损距离)

        Returns:
            仓位计算结果
        """
        atr = self.get_atr()

        if atr <= 0 or entry_price <= 0:
            return {
                "atr": atr,
                "atr_percent": 0.0,
                "position_value": 0.0,
                "contracts": 0.0,
                "risk_per_contract": 0.0,
            }

        # 止损距离 = ATR * 倍数
        stop_distance = atr * atr_multiplier
        stop_distance_pct = stop_distance / entry_price

        # 仓位 = 风险金额 / 止损距离
        position_value = risk_amount / stop_distance_pct if stop_distance_pct > 0 else 0
        contracts = position_value / entry_price if entry_price > 0 else 0

        # 检查是否超过最大可交易量
        max_position = equity * 0.5  # 最多50%仓位
        position_value = min(position_value, max_position)

        return {
            "atr": atr,
            "atr_percent": stop_distance_pct,
            "position_value": position_value,
            "contracts": contracts,
            "risk_per_contract": stop_distance * contracts,
            "stop_distance": stop_distance,
            "stop_distance_pct": stop_distance_pct,
        }


class DynamicRiskCalculator:
    """
    动态风险计算器

    根据资金规模自动调整风险暴露:
    - 小资金 (< 1万): 高风险偏好，单笔可承受 5% 亏损
    - 中小资金 (1-10万): 中等风险，单笔可承受 3% 亏损
    - 中等资金 (10-100万): 稳健，单笔可承受 2% 亏损
    - 大资金 (> 100万): 保守，单笔可承受 1% 亏损
    """

    # 风险等级配置
    RISK_TIERS: Dict[RiskTier, Dict[str, Any]] = {
        RiskTier.MICRO: {
            "max_equity": 10000,
            "risk_per_trade": 0.05,  # 5%
            "max_position_pct": 0.25,  # 最大25%仓位
            "max_daily_loss": 0.10,  # 最大日亏损10%
            "max_drawdown": 0.20,  # 最大回撤20%
            "label": "微型",
        },
        RiskTier.SMALL: {
            "max_equity": 100000,
            "risk_per_trade": 0.03,  # 3%
            "max_position_pct": 0.20,  # 最大20%仓位
            "max_daily_loss": 0.08,  # 最大日亏损8%
            "max_drawdown": 0.15,  # 最大回撤15%
            "label": "小型",
        },
        RiskTier.MEDIUM: {
            "max_equity": 1000000,
            "risk_per_trade": 0.02,  # 2%
            "max_position_pct": 0.15,  # 最大15%仓位
            "max_daily_loss": 0.05,  # 最大日亏损5%
            "max_drawdown": 0.10,  # 最大回撤10%
            "label": "中型",
        },
        RiskTier.LARGE: {
            "max_equity": float("inf"),
            "risk_per_trade": 0.01,  # 1%
            "max_position_pct": 0.10,  # 最大10%仓位
            "max_daily_loss": 0.03,  # 最大日亏损3%
            "max_drawdown": 0.05,  # 最大回撤5%
            "label": "大型",
        },
    }

    def __init__(self, custom_tiers: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        初始化风险计算器

        Args:
            custom_tiers: 自定义风险配置，格式如 {
                "micro": {"max_equity": 10000, "risk_per_trade": 0.05, ...}
            }
        """
        if custom_tiers:
            self._load_custom_tiers(custom_tiers)

    def _load_custom_tiers(self, custom_tiers: Dict[str, Dict[str, Any]]) -> None:
        """加载自定义风险配置"""
        tier_map = {"micro": RiskTier.MICRO, "small": RiskTier.SMALL, "medium": RiskTier.MEDIUM, "large": RiskTier.LARGE}
        for key, config in custom_tiers.items():
            if key in tier_map:
                self.RISK_TIERS[tier_map[key]].update(config)

    def get_risk_tier(self, equity: float) -> RiskTier:
        """
        根据权益获取风险等级

        Args:
            equity: 当前权益

        Returns:
            风险等级
        """
        if equity < 10000:
            return RiskTier.MICRO
        elif equity < 100000:
            return RiskTier.SMALL
        elif equity < 1000000:
            return RiskTier.MEDIUM
        else:
            return RiskTier.LARGE

    def get_tier_config(self, tier: RiskTier) -> Dict[str, Any]:
        """获取指定风险等级的配置"""
        return self.RISK_TIERS.get(tier, self.RISK_TIERS[RiskTier.MEDIUM])

    def calculate(
        self,
        equity: float,
        entry_price: float,
        stop_loss_pct: float,
        signal_confidence: float = 1.0,
    ) -> PositionResult:
        """
        计算动态风险仓位

        Args:
            equity: 当前权益
            entry_price: 入场价格
            stop_loss_pct: 止损百分比 (如 0.02 = 2%)
            signal_confidence: 信号信心度 (0.0 - 1.0)

        Returns:
            PositionResult 仓位计算结果
        """
        # 确定风险等级
        tier = self.get_risk_tier(equity)
        config = self.RISK_TIERS[tier]

        # 计算风险金额 (绝对值)
        risk_amount = equity * config["risk_per_trade"]

        # 计算仓位数量
        # 仓位 = 风险金额 / 止损百分比
        if stop_loss_pct > 0:
            position_value = risk_amount / stop_loss_pct
        else:
            position_value = 0

        # 应用信号信心度调整
        adjusted_position = position_value * signal_confidence

        # 检查最大仓位限制
        max_position = equity * config["max_position_pct"]
        final_position = min(adjusted_position, max_position)

        # 计算手数/股数
        contracts = final_position / entry_price if entry_price > 0 else 0

        return PositionResult(
            position_value=final_position,
            position_pct=final_position / equity if equity > 0 else 0,
            contracts=contracts,
            risk_amount=risk_amount,
            risk_tier=tier,
            algo_mode=AlgoMode.SIMPLE,
            methods={"base": final_position, "confidence_adjusted": adjusted_position},
        )

    def get_risk_profile(self, equity: float) -> Dict[str, Any]:
        """
        获取当前权益的风险配置画像

        Args:
            equity: 当前权益

        Returns:
            风险配置信息
        """
        tier = self.get_risk_tier(equity)
        config = self.RISK_TIERS[tier]

        return {
            "tier": tier.value,
            "tier_label": config["label"],
            "risk_per_trade_pct": config["risk_per_trade"] * 100,
            "max_position_pct": config["max_position_pct"] * 100,
            "risk_amount": equity * config["risk_per_trade"],
            "max_position": equity * config["max_position_pct"],
            "max_daily_loss": equity * config["max_daily_loss"],
        }


class HybridPositionAlgorithm:
    """
    复合仓位算法

    结合三种方法计算最优仓位:
    1. ATR 波动率仓位 (权重 40%)
    2. 凯利公式仓位 (权重 30%)
    3. 信心度加权仓位 (权重 30%)
    """

    DEFAULT_WEIGHTS = {"atr": 0.40, "kelly": 0.30, "confidence": 0.30}

    def __init__(
        self,
        atr_calculator: Optional[ATRCalculator] = None,
        kelly_calculator: Optional[KellyCalculator] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        初始化复合算法

        Args:
            atr_calculator: ATR 计算器实例
            kelly_calculator: 凯利计算器实例
            weights: 各算法权重，默认为 40/30/30
        """
        self._atr_calc = atr_calculator or ATRCalculator()
        self._kelly_calc = kelly_calculator or KellyCalculator()
        self._weights = weights or self.DEFAULT_WEIGHTS.copy()

    def set_weights(self, atr: float, kelly: float, confidence: float) -> None:
        """设置算法权重"""
        total = atr + kelly + confidence
        self._weights = {
            "atr": atr / total,
            "kelly": kelly / total,
            "confidence": confidence / total,
        }

    def calculate(
        self,
        equity: float,
        entry_price: float,
        atr: float,
        signal_confidence: float,
        historical_win_rate: float = 0.55,
        reward_ratio: float = 1.5,
        atr_multiplier: float = 2.0,
    ) -> PositionResult:
        """
        计算复合仓位

        Args:
            equity: 当前权益
            entry_price: 入场价格
            atr: 当前 ATR 值
            signal_confidence: 信号信心度 (0.0 - 1.0)
            historical_win_rate: 历史胜率 (默认 0.55)
            reward_ratio: 盈亏比 (默认 1.5)
            atr_multiplier: ATR 倍数 (默认 2.0)

        Returns:
            PositionResult 仓位计算结果
        """
        # 更新 ATR 计算器
        if atr > 0:
            # 直接设置 ATR 值
            self._atr_calc._tr_list.append(atr)
            if len(self._atr_calc._tr_list) > self._atr_calc._period * 2:
                self._atr_calc._tr_list = self._atr_calc._tr_list[-self._atr_calc._period * 2 :]

        # 方法1: ATR 仓位
        risk_per_trade = DynamicRiskCalculator().RISK_TIERS[
            DynamicRiskCalculator().get_risk_tier(equity)
        ]["risk_per_trade"]
        risk_amount = equity * risk_per_trade

        atr_result = self._atr_calc.calculate_position_size(
            equity=equity,
            risk_amount=risk_amount,
            entry_price=entry_price,
            atr_multiplier=atr_multiplier,
        )

        # 方法2: 凯利仓位
        kelly_result = self._kelly_calc.calculate(
            equity=equity,
            win_rate=historical_win_rate,
            reward_ratio=reward_ratio,
            entry_price=entry_price,
        )

        # 方法3: 信心度仓位 (基于风险平价)
        confidence_position = equity * risk_per_trade * 3 * signal_confidence  # 约 3-5 倍风险
        confidence_contracts = confidence_position / entry_price if entry_price > 0 else 0

        # 加权平均
        atr_position = atr_result["position_value"]
        kelly_position = kelly_result["position_value"]
        confidence_position_val = confidence_position

        final_value = (
            atr_position * self._weights["atr"]
            + kelly_position * self._weights["kelly"]
            + confidence_position_val * self._weights["confidence"]
        )

        # 限制最大仓位
        max_position = equity * 0.30  # 最多30%
        final_value = min(final_value, max_position)

        contracts = final_value / entry_price if entry_price > 0 else 0

        # 确定风险等级
        tier = DynamicRiskCalculator().get_risk_tier(equity)

        return PositionResult(
            position_value=final_value,
            position_pct=final_value / equity if equity > 0 else 0,
            contracts=contracts,
            risk_amount=risk_amount,
            risk_tier=tier,
            algo_mode=AlgoMode.HYBRID,
            methods={
                "atr": atr_position,
                "kelly": kelly_position,
                "confidence": confidence_position_val,
                "weights": self._weights.copy(),
            },
        )


class PositionCalculator:
    """
    统一仓位计算器

    对外提供统一的仓位计算接口，支持切换算法模式
    """

    def __init__(
        self,
        algo_mode: AlgoMode = AlgoMode.SIMPLE,
        custom_tiers: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        初始化仓位计算器

        Args:
            algo_mode: 算法模式
            custom_tiers: 自定义风险配置
        """
        self._algo_mode = algo_mode
        self._dynamic_calc = DynamicRiskCalculator(custom_tiers)
        self._hybrid_calc = HybridPositionAlgorithm()

    def set_algo_mode(self, mode: AlgoMode) -> None:
        """设置算法模式"""
        self._algo_mode = mode

    def get_algo_mode(self) -> AlgoMode:
        """获取当前算法模式"""
        return self._algo_mode

    def set_custom_tiers(self, tiers: Dict[str, Dict[str, Any]]) -> None:
        """设置自定义风险等级"""
        self._dynamic_calc._load_custom_tiers(tiers)

    def calculate(
        self,
        equity: float,
        entry_price: float,
        stop_loss_pct: float,
        signal_confidence: float = 1.0,
        atr: float = 0.0,
        historical_win_rate: float = 0.55,
        reward_ratio: float = 1.5,
    ) -> PositionResult:
        """
        计算仓位

        Args:
            equity: 当前权益
            entry_price: 入场价格
            stop_loss_pct: 止损百分比 (如 0.02 = 2%)
            signal_confidence: 信号信心度 (0.0 - 1.0)
            atr: ATR 值 (hybrid 模式需要)
            historical_win_rate: 历史胜率 (hybrid 模式需要)
            reward_ratio: 盈亏比 (hybrid 模式需要)

        Returns:
            PositionResult 仓位计算结果
        """
        if self._algo_mode == AlgoMode.HYBRID:
            return self._hybrid_calc.calculate(
                equity=equity,
                entry_price=entry_price,
                atr=atr,
                signal_confidence=signal_confidence,
                historical_win_rate=historical_win_rate,
                reward_ratio=reward_ratio,
            )
        else:
            return self._dynamic_calc.calculate(
                equity=equity,
                entry_price=entry_price,
                stop_loss_pct=stop_loss_pct,
                signal_confidence=signal_confidence,
            )

    def get_risk_profile(self, equity: float) -> Dict[str, Any]:
        """获取风险配置画像"""
        return self._dynamic_calc.get_risk_profile(equity)
