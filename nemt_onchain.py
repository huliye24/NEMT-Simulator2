"""
NEMT链上数据模块
实现第五章中定义的链上指标

包含：
1. MVRV / MVRV Z-score
2. NUPL (未实现净损益)
3. 交易所余额
4. LTH/STH供应占比
5. 稳定币指标
6. 鲸鱼行为指标
7. 链上健康度评分
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from datetime import datetime


@dataclass
class OnchainMetrics:
    """链上指标数据类"""
    # 估值指标
    mvrv_ratio: Optional[float] = None
    mvrv_zscore: Optional[float] = None
    
    # 情绪指标
    nupl: Optional[float] = None
    nupl_stage: Optional[str] = None
    
    # 供需指标
    exchange_balance: Optional[float] = None
    exchange_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    
    # 持有者结构
    lth_ratio: Optional[float] = None
    sth_ratio: Optional[float] = None
    lth_change: Optional[float] = None
    
    # 稳定币
    stablecoin_mcap: Optional[float] = None
    stablecoin_change: Optional[float] = None
    
    # 鲸鱼行为
    whale_netflow: Optional[float] = None  # 正=流入交易所, 负=流出
    whale_address_count: Optional[float] = None
    
    # 矿工
    miner_flow: Optional[float] = None
    
    # 时间戳
    timestamp: Optional[datetime] = None


@dataclass
class CycleIndicators:
    """周期定位指标"""
    phase: str  # "accumulation", "bull_start", "bull_mid", "bull_late", "bear_early", "bear_deep", "bear_late"
    cycle_score: float  # 0-1, 综合周期评分
    halving_phase: str  # "pre", "at", "post_early", "post_mid", "post_late"
    days_to_halving: Optional[int] = None
    cycle_age: float = 0.0  # 周期年龄 0-1


@dataclass
class OnchainHealthScore:
    """链上健康度评分"""
    total_score: float = 5.0  # 0-10
    mvrv_score: float = 1.0   # 0-2
    nupl_score: float = 1.0   # 0-2
    exchange_score: float = 1.0  # 0-2
    lth_score: float = 1.0    # 0-2
    stablecoin_score: float = 1.0  # 0-2
    whale_score: float = 1.0  # 0-2


class OnchainCalculator:
    """
    链上数据计算器
    
    实现第五章中定义的各项指标计算
    """

    def __init__(self):
        # 历史数据缓存
        self.price_history: List[float] = []
        self.mvrv_history: List[float] = []
        self.exchange_balance_history: List[float] = []
        self.lth_ratio_history: List[float] = []

    def calculate_mvrv(
        self,
        market_cap: float,
        realized_cap: float
    ) -> Tuple[float, float]:
        """
        计算MVRV和MVRV Z-score
        
        MVRV = 市值 / 已实现市值
        MVRV Z-score = (MVRV - 均值) / 标准差
        
        Args:
            market_cap: 当前市值
            realized_cap: 已实现市值
            
        Returns:
            (MVRV比率, Z-score)
        """
        if realized_cap <= 0:
            return 1.0, 0.0
        
        mvrv = market_cap / realized_cap
        
        # 更新历史
        self.mvrv_history.append(mvrv)
        
        if len(self.mvrv_history) < 30:
            return mvrv, 0.0
        
        # 计算Z-score
        mean_mvrv = np.mean(self.mvrv_history[-365:])  # 使用1年数据
        std_mvrv = np.std(self.mvrv_history[-365:])
        
        if std_mvrv > 0:
            zscore = (mvrv - mean_mvrv) / std_mvrv
        else:
            zscore = 0.0
        
        return mvrv, zscore

    def calculate_mvrv_simple(
        self,
        prices: np.ndarray,
        holdings: np.ndarray
    ) -> Tuple[float, float]:
        """
        简化版MVRV计算 (使用持仓成本)
        
        Args:
            prices: 每枚币的购买价格数组
            holdings: 每枚币的数量数组
            
        Returns:
            (MVRV比率, Z-score)
        """
        current_price = prices[-1] if len(prices) > 0 else 0
        
        if len(prices) == 0 or len(holdings) == 0:
            return 1.0, 0.0
        
        # 市值
        market_cap = np.sum(holdings) * current_price
        
        # 已实现市值 = Σ(购买价格 × 持有数量)
        realized_cap = np.sum(prices * holdings)
        
        return self.calculate_mvrv(market_cap, realized_cap)

    def calculate_nupl(
        self,
        market_cap: float,
        realized_cap: float
    ) -> Tuple[float, str]:
        """
        计算NUPL (Net Unrealized Profit/Loss)
        
        NUPL = (市值 - 已实现市值) / 市值
        
        阶段:
        - < 0: 投降 (Capitulation)
        - 0-0.25: 希望/恐惧 (Hope/Fear)
        - 0.25-0.50: 乐观/焦虑 (Optimism/Anxiety)
        - 0.50-0.75: 信念/否认 (Belief/Denial)
        - > 0.75: 欣快/贪婪 (Euphoria/Greed)
        
        Args:
            market_cap: 当前市值
            realized_cap: 已实现市值
            
        Returns:
            (NUPL值, 阶段名称)
        """
        if market_cap <= 0:
            return 0.0, "unknown"
        
        nupl = (market_cap - realized_cap) / market_cap
        
        if nupl < 0:
            stage = "capitulation"
        elif nupl < 0.25:
            stage = "hope_fear"
        elif nupl < 0.50:
            stage = "optimism_anxiety"
        elif nupl < 0.75:
            stage = "belief_denial"
        else:
            stage = "euphoria_greed"
        
        return nupl, stage

    def calculate_nupl_simple(
        self,
        current_price: float,
        avg_cost: float,
        supply: float
    ) -> Tuple[float, str]:
        """
        简化版NUPL计算
        
        Args:
            current_price: 当前价格
            avg_cost: 平均持仓成本
            supply: 流通供应量
            
        Returns:
            (NUPL值, 阶段)
        """
        market_cap = current_price * supply
        realized_cap = avg_cost * supply
        return self.calculate_nupl(market_cap, realized_cap)

    def calculate_exchange_trend(
        self,
        exchange_balances: List[float],
        lookback: int = 30
    ) -> Tuple[float, str]:
        """
        计算交易所余额趋势
        
        Args:
            exchange_balances: 交易所余额历史
            lookback: 回看天数
            
        Returns:
            (余额变化率, 趋势方向)
        """
        if len(exchange_balances) < 10:
            return 0.0, "stable"
        
        recent = np.mean(exchange_balances[-min(lookback//2, len(exchange_balances)):])
        older = np.mean(exchange_balances[-lookback:-min(lookback//2, len(exchange_balances))])
        
        if older > 0:
            change_rate = (recent - older) / older
        else:
            change_rate = 0.0
        
        if change_rate > 0.02:  # 2%上升
            trend = "increasing"
        elif change_rate < -0.02:  # 2%下降
            trend = "decreasing"
        else:
            trend = "stable"
        
        return change_rate, trend

    def calculate_lth_sth_ratio(
        self,
        short_holdings: np.ndarray,  # <155天的持仓
        long_holdings: np.ndarray,    # >155天的持仓
        supply: float
    ) -> Tuple[float, float, float]:
        """
        计算LTH/STH供应占比
        
        Args:
            short_holdings: 短期持有者持仓数组
            long_holdings: 长期持有者持仓数组
            supply: 总流通供应量
            
        Returns:
            (LTH占比, STH占比, LTH变化率)
        """
        sth_total = np.sum(short_holdings)
        lth_total = np.sum(long_holdings)
        
        if supply > 0:
            lth_ratio = lth_total / supply
            sth_ratio = sth_total / supply
        else:
            lth_ratio = 0.5
            sth_ratio = 0.5
        
        # 计算LTH变化
        self.lth_ratio_history.append(lth_ratio)
        if len(self.lth_ratio_history) >= 30:
            lth_change = (lth_ratio - self.lth_ratio_history[-30]) / self.lth_ratio_history[-30]
        else:
            lth_change = 0.0
        
        return lth_ratio, sth_ratio, lth_change

    def calculate_onchain_health_score(
        self,
        metrics: OnchainMetrics,
        historical_mvrv: Optional[List[float]] = None,
        historical_exchange: Optional[List[float]] = None
    ) -> OnchainHealthScore:
        """
        计算链上健康度评分 (0-10)
        
        根据第五章评分规则:
        - MVRV Z-score: <1且上升=+2, 1-3=+1, >5或快速下降=0
        - NUPL: <0.25=+2, 0.25-0.50=+1, >0.75=+0
        - 交易所BTC余额: 月降幅>3%=+2, 变化<1%=+1, 月增幅>3%=+0
        - LTH供应占比变化: 月增>1%=+2, 变化<0.5%=+1, 月降>1%=+0
        - 稳定币余额: 月增>10%=+2, 变化<5%=+1, 月降>10%=+0
        - 鲸鱼交易所净流量: 净流出>10k=+2, 净流量<5k=+1, 净流入>10k=+0
        
        Args:
            metrics: 链上指标数据
            historical_mvrv: 历史MVRV数据
            historical_exchange: 历史交易所余额
            
        Returns:
            OnchainHealthScore对象
        """
        score = OnchainHealthScore()
        
        # 1. MVRV Z-score评分
        if metrics.mvrv_zscore is not None:
            zscore = metrics.mvrv_zscore
            
            # 检查趋势
            zscore_rising = False
            if len(self.mvrv_history) >= 7:
                zscore_rising = self.mvrv_history[-1] > self.mvrv_history[-7]
            
            if zscore < 1 and zscore_rising:
                score.mvrv_score = 2.0
            elif 1 <= zscore <= 3:
                score.mvrv_score = 1.0
            elif zscore > 5 or zscore < -1:
                score.mvrv_score = 0.0
            else:
                score.mvrv_score = 0.5
        
        # 2. NUPL评分
        if metrics.nupl is not None:
            nupl = metrics.nupl
            if nupl < 0.25:
                score.nupl_score = 2.0
            elif nupl < 0.50:
                score.nupl_score = 1.0
            elif nupl < 0.75:
                score.nupl_score = 0.5
            else:
                score.nupl_score = 0.0
        
        # 3. 交易所余额评分
        if metrics.exchange_trend is not None:
            if metrics.exchange_trend == "decreasing":
                score.exchange_score = 2.0
            elif metrics.exchange_trend == "stable":
                score.exchange_score = 1.0
            else:
                score.exchange_score = 0.0
        
        # 4. LTH评分
        if metrics.lth_change is not None:
            if metrics.lth_change > 0.01:  # 月增>1%
                score.lth_score = 2.0
            elif abs(metrics.lth_change) < 0.005:  # 变化<0.5%
                score.lth_score = 1.0
            else:
                score.lth_score = 0.0
        
        # 5. 稳定币评分
        if metrics.stablecoin_change is not None:
            if metrics.stablecoin_change > 0.10:  # 月增>10%
                score.stablecoin_score = 2.0
            elif abs(metrics.stablecoin_change) < 0.05:  # 变化<5%
                score.stablecoin_score = 1.0
            else:
                score.stablecoin_score = 0.0
        
        # 6. 鲸鱼评分
        if metrics.whale_netflow is not None:
            if metrics.whale_netflow < -10000:  # 净流出>10k
                score.whale_score = 2.0
            elif abs(metrics.whale_netflow) < 5000:  # 净流量<5k
                score.whale_score = 1.0
            else:
                score.whale_score = 0.0
        
        # 总分
        score.total_score = (
            score.mvrv_score +
            score.nupl_score +
            score.exchange_score +
            score.lth_score +
            score.stablecoin_score +
            score.whale_score
        )
        
        return score

    def estimate_cycle_phase(
        self,
        lth_ratio: float,
        sth_ratio: float,
        mvrv_zscore: float,
        nupl: float,
        halving_date: datetime,
        current_date: Optional[datetime] = None
    ) -> CycleIndicators:
        """
        估算周期阶段
        
        Args:
            lth_ratio: LTH供应占比
            sth_ratio: STH供应占比
            mvrv_zscore: MVRV Z-score
            nupl: NUPL值
            halving_date: 下次减半日期
            current_date: 当前日期
            
        Returns:
            CycleIndicators对象
        """
        if current_date is None:
            current_date = datetime.now()
        
        # 计算距减半天数
        days_to_halving = (halving_date - current_date).days
        
        # 确定减半周期阶段
        if days_to_halving > 365:
            halving_phase = "pre"  # 减半前12个月以上
        elif days_to_halving > 0:
            halving_phase = "pre"   # 减半前
        elif days_to_halving > -180:
            halving_phase = "post_early"  # 减半后6个月
        elif days_to_halving > -365:
            halving_phase = "post_mid"  # 减半后6-12个月
        else:
            halving_phase = "post_late"  # 减半后12个月以上
        
        # 综合周期评分 (0-1)
        cycle_score = 0.5
        
        # 基于MVRV调整
        if mvrv_zscore < 0:
            cycle_score += 0.2  # 底部区域
        elif mvrv_zscore > 5:
            cycle_score -= 0.3  # 顶部区域
        
        # 基于NUPL调整
        if nupl < 0:
            cycle_score += 0.2  # 投降区
        elif nupl > 0.75:
            cycle_score -= 0.2  # 贪婪区
        
        # 基于LTH调整
        if lth_ratio > 0.7:
            cycle_score += 0.1  # 强手积累
        elif sth_ratio > 0.5:
            cycle_score -= 0.1  # 散户主导
        
        cycle_score = max(0.0, min(1.0, cycle_score))
        
        # 确定周期阶段
        if lth_ratio > 0.65 and mvrv_zscore < 0:
            phase = "accumulation"  # 积累期
        elif lth_ratio > 0.55 and nupl < 0.25:
            phase = "bull_start"  # 牛市启动
        elif nupl > 0.25 and nupl < 0.75 and sth_ratio > 0.4:
            phase = "bull_mid"  # 牛市中期
        elif nupl > 0.75 or (lth_ratio < 0.5 and sth_ratio > 0.5):
            phase = "bull_late"  # 牛市末期
        elif lth_ratio > 0.6:
            phase = "bear_late"  # 熊市末期
        elif lth_ratio < 0.5 and nupl < 0:
            phase = "bear_deep"  # 熊市深期
        else:
            phase = "bear_early"  # 熊市初期
        
        return CycleIndicators(
            phase=phase,
            cycle_score=cycle_score,
            halving_phase=halving_phase,
            days_to_halving=days_to_halving
        )

    def get_market_stage_from_nupl(self, nupl: float) -> str:
        """
        从NUPL获取市场阶段名称
        
        Args:
            nupl: NUPL值
            
        Returns:
            市场阶段描述
        """
        stages = {
            "capitulation": "投降",
            "hope_fear": "希望/恐惧",
            "optimism_anxiety": "乐观/焦虑",
            "belief_denial": "信念/否认",
            "euphoria_greed": "欣快/贪婪"
        }
        
        return stages.get(self.calculate_nupl(
            market_cap=1000,  # dummy values
            realized_cap=1000
        )[1] if False else "unknown", "未知")

    def interpret_onchain_health(
        self,
        score: OnchainHealthScore
    ) -> Dict:
        """
        解释链上健康度评分
        
        Args:
            score: 链上健康度评分
            
        Returns:
            解释字典
        """
        interpretations = []
        
        if score.total_score >= 9:
            level = "极度健康"
            action = "可满仓操作"
        elif score.total_score >= 7:
            level = "良好"
            action = "标准仓位"
        elif score.total_score >= 5:
            level = "中性"
            action = "降低仓位，等待明确方向"
        elif score.total_score >= 3:
            level = "偏弱"
            action = "降低仓位或空仓等待"
        else:
            level = "极度恶化"
            action = "清仓观望"
        
        if score.mvrv_score >= 1.5:
            interpretations.append(f"MVRV: 极度低估 (Z={score.mvrv_score:.1f}/2)")
        elif score.mvrv_score >= 0.5:
            interpretations.append(f"MVRV: 正常区间 ({score.mvrv_score:.1f}/2)")
        else:
            interpretations.append(f"MVRV: 高度低估或过热 ({score.mvrv_score:.1f}/2)")
        
        if score.nupl_score >= 1.5:
            interpretations.append(f"NUPL: 极度贪婪/恐惧区域")
        elif score.nupl_score >= 0.5:
            interpretations.append(f"NUPL: 中性区间")
        else:
            interpretations.append(f"NUPL: 极度贪婪")
        
        if score.exchange_score >= 1.5:
            interpretations.append("交易所余额: 流出(积累)")
        elif score.exchange_score >= 0.5:
            interpretations.append("交易所余额: 稳定")
        else:
            interpretations.append("交易所余额: 流入(派发)")
        
        return {
            "level": level,
            "score": f"{score.total_score:.1f}/10",
            "action": action,
            "interpretations": interpretations
        }


class SimpleOnchainSimulator:
    """
    简化链上数据模拟器
    
    用于在没有真实链上数据时生成模拟数据
    """

    @staticmethod
    def simulate_mvrv_zscore(phase: str, noise_level: float = 0.2) -> float:
        """
        根据周期阶段模拟MVRV Z-score
        
        Args:
            phase: 周期阶段
            noise_level: 噪声水平
            
        Returns:
            MVRV Z-score
        """
        base_values = {
            "accumulation": -0.5,
            "bull_start": 0.5,
            "bull_mid": 2.0,
            "bull_late": 4.5,
            "bear_early": 1.5,
            "bear_deep": -1.0,
            "bear_late": -0.3
        }
        
        base = base_values.get(phase, 0.0)
        noise = np.random.randn() * noise_level * 2
        
        return base + noise

    @staticmethod
    def simulate_nupl(phase: str, noise_level: float = 0.05) -> float:
        """
        根据周期阶段模拟NUPL
        
        Args:
            phase: 周期阶段
            noise_level: 噪声水平
            
        Returns:
            NUPL值
        """
        base_values = {
            "accumulation": 0.1,
            "bull_start": 0.3,
            "bull_mid": 0.5,
            "bull_late": 0.8,
            "bear_early": 0.3,
            "bear_deep": -0.1,
            "bear_late": 0.1
        }
        
        base = base_values.get(phase, 0.3)
        noise = np.random.randn() * noise_level
        
        return max(-0.2, min(0.95, base + noise))

    @staticmethod
    def simulate_exchange_trend(phase: str) -> str:
        """
        根据周期阶段模拟交易所余额趋势
        
        Args:
            phase: 周期阶段
            
        Returns:
            趋势方向
        """
        trends = {
            "accumulation": "decreasing",
            "bull_start": "decreasing",
            "bull_mid": "stable",
            "bull_late": "increasing",
            "bear_early": "increasing",
            "bear_deep": "increasing",
            "bear_late": "decreasing"
        }
        
        return trends.get(phase, "stable")
