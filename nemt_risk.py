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
NEMT风控模块
实现第八章中定义的风险控制系统

包含：
1. 仓位管理 - 相位驱动的动态仓位
2. 波动管理 - ATR适应型止损
3. 杠杆管理 - 安全杠杆使用
4. 资金曲线管理 - 回撤控制
5. 心理风控 - 冷静期规则
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import deque

from nemt_signals import MarketPhase
from nemt_state_machine import NEMTStateMachine


@dataclass
class PositionSize:
    """仓位配置"""
    max_position: float      # 最大仓位
    single_risk: float      # 单笔风险上限
    leverage_allowed: int    # 允许杠杆
    position_ratio: float    # 当前建议比例


@dataclass
class StopLossConfig:
    """止损配置"""
    atr_multiplier: float   # ATR倍数
    structure_buffer: float  # 结构缓冲
    max_loss_pct: float    # 最大亏损比例
    trailing_threshold: float  # 移动止损门槛


@dataclass
class DrawdownLevel:
    """回撤等级"""
    level: str     # "green", "yellow", "orange", "red"
    threshold: float
    action: str
    waiting_period: Optional[timedelta] = None


@dataclass
class RiskStats:
    """风控统计"""
    peak_balance: float
    current_balance: float
    drawdown: float
    drawdown_pct: float
    trades_today: int
    losses_today: int
    cooling_off: bool
    cooling_off_until: Optional[datetime] = None


class KellyCriterion:
    """
    凯利公式计算器
    实现改进的凯利公式用于仓位计算
    """

    @staticmethod
    def calculate_position_fraction(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        confidence: float = 1.0,
        fraction: float = 0.25  # 实际使用fraction比例的凯利
    ) -> float:
        """
        计算仓位比例
        
        公式: f* = (p * b - q) / b
        其中 p=胜率, q=败率, b=盈亏比
        
        Args:
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利
            avg_loss: 平均亏损
            confidence: 信心系数
            fraction: 凯利比例系数
            
        Returns:
            建议仓位比例
        """
        if avg_loss <= 0 or win_rate <= 0:
            return 0.0
        
        b = avg_win / avg_loss  # 盈亏比
        q = 1 - win_rate
        p = win_rate
        
        # 凯利公式
        kelly = (p * b - q) / b
        
        # 考虑信心系数和分数凯利
        adjusted = kelly * confidence * fraction
        
        # 限制在合理范围
        return max(0.0, min(0.5, adjusted))  # 最大50%仓位


class NEMTRiskManager:
    """
    NEMT风险管理器
    
    实现第八章定义的完整风控系统
    """

    def __init__(
        self,
        initial_balance: float = 100000.0,
        config: Optional[Dict] = None
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_balance = initial_balance
        
        # 配置
        self.config = config or self._default_config()
        
        # 状态
        self.max_drawdown = 0.0
        self.daily_stats = {
            "trades": 0,
            "losses": 0,
            "loss_amount": 0.0
        }
        self.cooling_off_until: Optional[datetime] = None
        
        # 交易历史
        self.trade_log: List[Dict] = []
        
        # 仓位缓存
        self.current_position_ratio = 0.0

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 仓位配置
            "max_position_phase_a": 0.20,
            "max_position_phase_b": 0.50,
            "max_position_phase_c": 0.70,
            "max_position_phase_d": 1.00,
            "single_risk_phase_a": 0.01,  # 1%
            "single_risk_phase_b": 0.02,
            "single_risk_phase_c": 0.03,
            "single_risk_phase_d": 0.02,
            
            # 止损配置
            "atr_multiplier_vortex": 1.5,
            "atr_multiplier_resonance": 2.0,
            "atr_multiplier_trend": 1.0,
            "structure_buffer": 0.02,
            "max_loss_pct": 0.05,
            
            # 移动止损
            "trailing_profit_threshold": 0.10,  # 10%利润后启动
            "trailing_distance": 0.03,  # 3%追踪距离
            
            # 回撤控制
            "drawdown_levels": [
                {"level": "yellow", "threshold": 0.10, "action": "复盘近5笔交易"},
                {"level": "orange", "threshold": 0.15, "action": "仓位降至50%，暂停新开仓一周"},
                {"level": "red", "threshold": 0.20, "action": "清仓，停止交易一个月"}
            ],
            
            # 杠杆配置
            "leverage_phase_c": 2,
            "leverage_phase_d": 1,
            "leverage_safety_margin": 0.05,  # 5%安全边际
            
            # 冷静期配置
            "cool_off_single_loss": 24,  # 单笔亏损>3%后冷静24小时
            "cool_off_daily_loss": 48,  # 单日亏损>5%后冷静48小时
            "cool_off_after_stop": 24,  # 止损后冷静24小时
            
            # 波动率警戒
            "volatility_yellow": 1.5,  # ATR放大50%
            "volatility_orange": 2.0,  # ATR放大100%
            "volatility_red": 1.15,   # 单日波动15%
        }

    # =====================
    # 仓位管理
    # =====================
    
    def get_position_size(self, phase: MarketPhase) -> PositionSize:
        """
        根据相位获取仓位配置
        
        Args:
            phase: 当前市场相位
            
        Returns:
            PositionSize对象
        """
        phase_key = {
            MarketPhase.PHASE_A_NOISE: "phase_a",
            MarketPhase.PHASE_B_VORTEX: "phase_b",
            MarketPhase.PHASE_C_RESONANCE: "phase_c",
            MarketPhase.PHASE_D_TREND: "phase_d"
        }.get(phase, "phase_a")
        
        return PositionSize(
            max_position=self.config[f"max_position_{phase_key}"],
            single_risk=self.config[f"single_risk_{phase_key}"],
            leverage_allowed=self.config.get(f"leverage_{phase_key}", 0),
            position_ratio=0.0  # 待计算
        )

    def calculate_position_size(
        self,
        phase: MarketPhase,
        entry_price: float,
        stop_loss: float,
        account_balance: Optional[float] = None,
        p_trend: float = 0.5,
        signal_confidence: float = 0.5
    ) -> Tuple[float, float]:
        """
        计算仓位大小
        
        Args:
            phase: 当前相位
            entry_price: 入场价格
            stop_loss: 止损价格
            account_balance: 账户余额
            p_trend: 趋势概率
            signal_confidence: 信号置信度
            
        Returns:
            (仓位大小, 风险金额)
        """
        if account_balance is None:
            account_balance = self.balance
        
        pos_size = self.get_position_size(phase)
        
        # 单笔风险上限
        risk_amount = account_balance * pos_size.single_risk
        
        # 止损距离
        stop_distance = entry_price - stop_loss
        stop_distance_pct = stop_distance / entry_price
        
        if stop_distance_pct <= 0:
            return 0.0, 0.0
        
        # 凯利仓位
        kelly_pos = KellyCriterion.calculate_position_fraction(
            win_rate=signal_confidence,
            avg_win=1.0,  # 相对值
            avg_loss=stop_distance_pct,
            confidence=p_trend
        )
        
        # 综合仓位 (取较小值)
        max_by_risk = risk_amount / stop_distance
        max_position = min(
            pos_size.max_position,
            kelly_pos,
            account_balance * pos_size.max_position / entry_price
        )
        
        position_size = min(max_by_risk, max_position)
        actual_risk = position_size * stop_distance
        
        self.current_position_ratio = position_size * entry_price / account_balance
        
        return position_size, actual_risk

    # =====================
    # 止损管理
    # =====================
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        signal_type: str,
        phase: MarketPhase,
        vortex_low: Optional[float] = None
    ) -> float:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            atr: ATR值
            signal_type: 信号类型
            phase: 当前相位
            vortex_low: 涡旋区间低点(可选)
            
        Returns:
            止损价格
        """
        # ATR基础止损
        if signal_type == "vortex_breakout":
            atr_mult = self.config["atr_multiplier_vortex"]
        elif signal_type == "resonance_trigger":
            atr_mult = self.config["atr_multiplier_resonance"]
        else:
            atr_mult = self.config["atr_multiplier_trend"]
        
        atr_distance = atr * atr_mult
        
        # 结构止损
        if vortex_low is not None:
            structure_distance = entry_price - vortex_low
            structure_stop = entry_price - structure_distance * (1 + self.config["structure_buffer"])
        else:
            structure_stop = entry_price - atr_distance
        
        # 最大亏损限制
        max_loss_distance = entry_price * self.config["max_loss_pct"]
        
        # 取最保守的止损
        stop_price = min(
            entry_price - atr_distance,
            structure_stop,
            entry_price - max_loss_distance
        )
        
        return max(stop_price, entry_price * 0.9)  # 最低90%价格

    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        current_stop: float,
        highest_price: float
    ) -> float:
        """
        计算移动止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            current_stop: 当前止损价
            highest_price: 持仓期间最高价
            
        Returns:
            新的止损价格
        """
        profit = (current_price - entry_price) / entry_price
        
        if profit < self.config["trailing_profit_threshold"]:
            return current_stop
        
        # 移动止损: 从最高点回撤一定比例
        trailing_stop = highest_price * (1 - self.config["trailing_distance"])
        
        # 只能上移，不能下移
        return max(current_stop, trailing_stop, entry_price * 1.005)  # 保本+0.5%

    # =====================
    # 杠杆管理
    # =====================
    
    def calculate_safe_leverage(
        self,
        entry_price: float,
        stop_loss: float,
        phase: MarketPhase,
        maintenance_margin: float = 0.005  # 0.5%维持保证金
    ) -> Tuple[int, float]:
        """
        计算安全杠杆
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            phase: 当前相位
            maintenance_margin: 维持保证金率
            
        Returns:
            (杠杆倍数, 强平价格)
        """
        max_leverage = self.config.get(f"leverage_phase_{phase.value.lower()}", 1)
        
        # 止损距离
        stop_distance = entry_price - stop_loss
        stop_pct = stop_distance / entry_price
        
        # 计算允许的最大杠杆
        # 强平价格 = 入场价 * (1 - 1/杠杆 + 维持保证金)
        # 我们需要: 强平价 < 止损价 * (1 - 安全边际)
        
        safety_margin = self.config["leverage_safety_margin"]
        
        for leverage in range(max_leverage, 0, -1):
            # 计算强平价
            liquidation_price = entry_price * (1 - 1/leverage + maintenance_margin)
            
            # 检查安全边际
            if liquidation_price < stop_loss * (1 - safety_margin):
                return leverage, liquidation_price
        
        return 1, entry_price * 0.99

    # =====================
    # 资金曲线管理
    # =====================
    
    def check_drawdown(self) -> Tuple[DrawdownLevel, bool]:
        """
        检查回撤
        
        Returns:
            (回撤等级, 是否需要行动)
        """
        self.peak_balance = max(self.peak_balance, self.balance)
        current_drawdown = self.peak_balance - self.balance
        drawdown_pct = current_drawdown / self.peak_balance if self.peak_balance > 0 else 0
        
        self.max_drawdown = max(self.max_drawdown, drawdown_pct)
        
        # 检查各等级
        action_required = False
        level = DrawdownLevel(
            level="green",
            threshold=0.0,
            action="正常交易"
        )
        
        for dl in self.config["drawdown_levels"]:
            if drawdown_pct >= dl["threshold"]:
                level = DrawdownLevel(
                    level=dl["level"],
                    threshold=dl["threshold"],
                    action=dl["action"],
                    waiting_period=self._get_waiting_period(dl["level"])
                )
                action_required = True
        
        return level, action_required

    def _get_waiting_period(self, level: str) -> Optional[timedelta]:
        """获取等待期"""
        periods = {
            "yellow": timedelta(hours=0),
            "orange": timedelta(days=7),
            "red": timedelta(days=30)
        }
        return periods.get(level)

    # =====================
    # 心理风控
    # =====================
    
    def check_cooling_off(self) -> bool:
        """检查是否处于冷静期"""
        if self.cooling_off_until is None:
            return False
        
        if datetime.now() >= self.cooling_off_until:
            self.cooling_off_until = None
            return False
        
        return True

    def trigger_cooling_off(self, hours: int):
        """触发冷静期"""
        self.cooling_off_until = datetime.now() + timedelta(hours=hours)
        self.daily_stats["cooling_off"] = True

    def should_trade(
        self,
        single_loss_pct: float = 0.0,
        daily_loss_pct: float = 0.0,
        was_stopped_out: bool = False
    ) -> Tuple[bool, str]:
        """
        判断是否可以交易
        
        Args:
            single_loss_pct: 单笔亏损百分比
            daily_loss_pct: 当日亏损百分比
            was_stopped_out: 是否被止损
            
        Returns:
            (是否可以交易, 原因)
        """
        # 冷静期检查
        if self.check_cooling_off():
            remaining = self.cooling_off_until - datetime.now()
            return False, f"冷静期，剩余 {remaining.total_seconds()/3600:.1f} 小时"
        
        # 回撤检查
        level, action = self.check_drawdown()
        if level.level != "green":
            return False, f"回撤{level.threshold:.0%}，{level.action}"
        
        # 单笔亏损检查
        if single_loss_pct > 0.03:  # >3%
            self.trigger_cooling_off(self.config["cool_off_single_loss"])
            return False, f"单笔亏损>{single_loss_pct:.1%}，冷静24小时"
        
        # 单日亏损检查
        if daily_loss_pct > 0.05:  # >5%
            self.trigger_cooling_off(self.config["cool_off_daily_loss"])
            return False, f"单日亏损>{daily_loss_pct:.1%}，冷静48小时"
        
        # 止损后冷静
        if was_stopped_out:
            self.trigger_cooling_off(self.config["cool_off_after_stop"])
            return False, "止损触发，冷静24小时，禁止反手"
        
        return True, "可以交易"

    # =====================
    # 波动率警戒
    # =====================
    
    def check_volatility_alert(
        self,
        current_atr: float,
        historical_avg_atr: float,
        daily_change_pct: float
    ) -> Tuple[str, Optional[str]]:
        """
        检查波动率警戒
        
        Args:
            current_atr: 当前ATR
            historical_avg_atr: 历史平均ATR
            daily_change_pct: 当日价格变动百分比
            
        Returns:
            (警戒级别, 行动建议)
        """
        atr_ratio = current_atr / historical_avg_atr if historical_avg_atr > 0 else 1.0
        
        # 红色警戒
        if daily_change_pct > self.config["volatility_red"]:
            return "red", "强制减仓50%，离场观察24小时"
        
        # 橙色警戒
        if atr_ratio > self.config["volatility_orange"]:
            return "orange", "停止新开仓，收紧止损至成本价"
        
        # 黄色警戒
        if atr_ratio > self.config["volatility_yellow"]:
            return "yellow", "降低杠杆至≤2x，新开仓减半"
        
        return "green", "正常交易"

    # =====================
    # 仓位再平衡
    # =====================
    
    def should_rebalance(
        self,
        current_position_value: float,
        current_price: float,
        target_ratio: float,
        phase: MarketPhase,
        macro_score_changed: float = 0.0,
        onchain_score_changed: float = 0.0
    ) -> Tuple[str, float]:
        """
        判断是否需要仓位再平衡
        
        Args:
            current_position_value: 当前持仓市值
            current_price: 当前价格
            target_ratio: 目标比例
            phase: 当前相位
            macro_score_changed: 宏观评分变化
            onchain_score_changed: 链上评分变化
            
        Returns:
            (操作类型, 调整比例)
        """
        current_ratio = current_position_value / self.balance if self.balance > 0 else 0
        max_pos = self.get_position_size(phase).max_position
        
        # 减仓触发
        if phase == MarketPhase.PHASE_A_NOISE and current_ratio > 0.20:
            return "reduce", 0.20 - current_ratio
        
        if macro_score_changed < -2 or onchain_score_changed < -2:
            if current_ratio > max_pos * 0.6:
                return "reduce", max_pos * 0.6 - current_ratio
        
        # 增仓触发
        if phase in [MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_D_TREND]:
            if current_ratio < max_pos:
                return "add", min(max_pos - current_ratio, 0.20)
        
        return "hold", 0.0

    # =====================
    # 止盈管理
    # =====================
    
    def calculate_take_profit_levels(
        self,
        entry_price: float,
        risk_amount: float,
        mvrv_score: float,
        nupl: float,
        exchange_balance_trend: str,
        dci_value: float
    ) -> List[Dict]:
        """
        计算分批止盈水平
        
        Args:
            entry_price: 入场价格
            risk_amount: 风险金额
            mvrv_score: MVRV评分
            nupl: NUPL值
            exchange_balance_trend: 交易所余额趋势
            dci_value: DCI值
            
        Returns:
            止盈水平列表
        """
        levels = []
        
        # 第一批: MVRV > 5
        if mvrv_score > 5:
            levels.append({
                "name": "MVRV过热",
                "price": entry_price * (1 + 3 * risk_amount / entry_price * 0.3),  # 30%利润
                "quantity_pct": 0.30
            })
        
        # 第二批: 交易所余额由降转升
        if exchange_balance_trend == "increasing":
            levels.append({
                "name": "交易所余额上升",
                "price": entry_price * (1 + 3 * risk_amount / entry_price * 0.5),
                "quantity_pct": 0.30
            })
        
        # 第三批: DCI从高位跌破
        if dci_value < 0.55:
            levels.append({
                "name": "DCI破位",
                "price": entry_price * (1 + 3 * risk_amount / entry_price * 0.7),
                "quantity_pct": 0.30
            })
        
        # 第四批: 宏观恶化
        levels.append({
            "name": "宏观离场",
            "price": entry_price * (1 + 3 * risk_amount / entry_price),
            "quantity_pct": 0.10
        })
        
        return levels

    # =====================
    # 统计和报告
    # =====================
    
    def get_risk_stats(self) -> RiskStats:
        """获取风控统计"""
        level, _ = self.check_drawdown()
        
        return RiskStats(
            peak_balance=self.peak_balance,
            current_balance=self.balance,
            drawdown=self.peak_balance - self.balance,
            drawdown_pct=(self.peak_balance - self.balance) / self.peak_balance if self.peak_balance > 0 else 0,
            trades_today=self.daily_stats["trades"],
            losses_today=self.daily_stats["losses"],
            cooling_off=self.check_cooling_off(),
            cooling_off_until=self.cooling_off_until
        )

    def get_risk_report(self) -> Dict:
        """生成风控报告"""
        stats = self.get_risk_stats()
        level, _ = self.check_drawdown()
        
        return {
            "balance": {
                "current": f"${stats.current_balance:,.2f}",
                "peak": f"${stats.peak_balance:,.2f}",
                "drawdown": f"${stats.drawdown:,.2f}",
                "drawdown_pct": f"{stats.drawdown_pct:.1%}"
            },
            "risk_level": level.level.upper(),
            "risk_action": level.action,
            "cooling_off": {
                "active": stats.cooling_off,
                "until": stats.cooling_off_until.isoformat() if stats.cooling_off_until else None
            },
            "today_stats": {
                "trades": stats.trades_today,
                "losses": stats.losses_today
            },
            "max_drawdown": f"{self.max_drawdown:.1%}",
            "current_position_ratio": f"{self.current_position_ratio:.1%}"
        }

    def print_risk_dashboard(self):
        """打印风控仪表板"""
        report = self.get_risk_report()
        
        print("\n" + "=" * 60)
        print("NEMT 风控仪表板")
        print("=" * 60)
        
        print(f"\n账户:")
        print(f"  当前余额: {report['balance']['current']}")
        print(f"  历史峰值: {report['balance']['peak']}")
        print(f"  回撤: {report['balance']['drawdown']} ({report['balance']['drawdown_pct']})")
        
        print(f"\n风险等级: {report['risk_level']}")
        print(f"行动建议: {report['risk_action']}")
        
        print(f"\n冷静期: {'是' if report['cooling_off']['active'] else '否'}")
        if report['cooling_off']['until']:
            print(f"  解除时间: {report['cooling_off']['until']}")
        
        print(f"\n今日统计:")
        print(f"  交易次数: {report['today_stats']['trades']}")
        print(f"  亏损次数: {report['today_stats']['losses']}")
        
        print(f"\n最大历史回撤: {report['max_drawdown']}")
        print(f"当前持仓比例: {report['current_position_ratio']}")
        
        print("=" * 60)


def create_risk_manager(initial_balance: float = 100000.0) -> NEMTRiskManager:
    """创建风险管理器"""
    return NEMTRiskManager(initial_balance)
