#!/usr/bin/env python3
"""
NEMT Strategy Service
====================
云端策略层服务 - 策略管理、回测、评分、淘汰

功能：
1. 策略工厂 - 策略模板管理 + 参数生成
2. 回测引擎 - 历史数据回测
3. 评分系统 - Sharpe/回撤/胜率计算
4. 淘汰机制 - 差策略自动标记/休眠
5. Notion同步 - 策略双向同步

使用方法:
    python strategy_service.py --port 8002
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import sqlite3
import numpy as np

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 数据结构
# ============================================================================

class StrategyStatus(Enum):
    """策略状态"""
    ALIVE = "alive"         # 正常运行
    TESTING = "testing"     # 测试中
    DORMANT = "dormant"     # 休眠
    DEAD = "dead"           # 淘汰

class StrategyType(Enum):
    """策略类型"""
    TREND = "trend"              # 趋势策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归策略
    MOMENTUM = "momentum"       # 动量策略
    NEMT = "nemt"              # NEMT原生策略
    HYBRID = "hybrid"          # 混合策略


@dataclass
class StrategyMetrics:
    """策略性能指标"""
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_holding_hours: float = 0.0
    total_pnl: float = 0.0
    recent_sharpe: float = 0.0
    recent_return: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Strategy:
    """策略"""
    id: str
    name: str
    strategy_type: StrategyType
    version: str = "1.0"
    description: str = ""
    
    # 状态
    status: StrategyStatus = StrategyStatus.TESTING
    capital_weight: float = 0.0
    
    # 指标
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)
    performance: List[float] = field(default_factory=list)
    
    # 时间戳
    created_at: str = ""
    last_trade_at: Optional[str] = None
    last_update_at: str = ""
    
    # 参数
    params: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "strategy_type": self.strategy_type.value,
            "version": self.version,
            "description": self.description,
            "status": self.status.value,
            "capital_weight": self.capital_weight,
            "metrics": self.metrics.to_dict(),
            "performance": self.performance,
            "created_at": self.created_at,
            "last_trade_at": self.last_trade_at,
            "last_update_at": self.last_update_at,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Strategy":
        metrics = StrategyMetrics(**data.get("metrics", {}))
        return cls(
            id=data["id"],
            name=data["name"],
            strategy_type=StrategyType(data.get("strategy_type", "nemt")),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            status=StrategyStatus(data.get("status", "testing")),
            capital_weight=data.get("capital_weight", 0.0),
            metrics=metrics,
            performance=data.get("performance", []),
            created_at=data.get("created_at", ""),
            last_trade_at=data.get("last_trade_at"),
            last_update_at=data.get("last_update_at", ""),
            params=data.get("params", {})
        )


@dataclass
class BacktestConfig:
    """回测配置"""
    strategy_id: str
    symbol: str = "BTCUSDT"
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 10000.0
    slippage_bps: float = 1.0
    commission_bps: float = 5.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_id: str
    initial_capital: float
    final_equity: float
    total_pnl: float
    return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class StrategyScore:
    """策略评分"""
    strategy_id: str
    total_score: float  # 0-100
    profitability_score: float  # 0-30
    consistency_score: float  # 0-20
    risk_adjusted_score: float  # 0-30
    adaptability_score: float  # 0-20
    reasoning: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EvictionEvent:
    """淘汰事件"""
    strategy_id: str
    strategy_name: str
    action: str  # "dormant", "dead", "activate"
    score_before: float
    score_after: float
    reason: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# 策略工厂
# ============================================================================

class StrategyFactory:
    """策略工厂 - 创建和管理策略"""
    
    TEMPLATES = {
        "trend_ma": {
            "name": "趋势均线策略",
            "type": StrategyType.TREND,
            "params": {
                "fast_period": 10,
                "slow_period": 30,
                "ma_type": "sma"
            }
        },
        "mean_reversion_bb": {
            "name": "布林带均值回归策略",
            "type": StrategyType.MEAN_REVERSION,
            "params": {
                "period": 20,
                "std_dev": 2.0,
                "mode": "bollinger"
            }
        },
        "momentum_roc": {
            "name": "动量ROC策略",
            "type": StrategyType.MOMENTUM,
            "params": {
                "roc_period": 10,
                "threshold": 2.0
            }
        },
        "nemt_dci": {
            "name": "NEMT DCI策略",
            "type": StrategyType.NEMT,
            "params": {
                "dci_period": 24,
                "dci_threshold": 0.65,
                "min_confidence": 0.6
            }
        },
        "nemt_vortex": {
            "name": "NEMT 涡旋策略",
            "type": StrategyType.NEMT,
            "params": {
                "vortex_maturity_threshold": 0.6,
                "bbw_percentile": 20
            }
        },
        "hybrid_nemt": {
            "name": "NEMT混合策略",
            "type": StrategyType.HYBRID,
            "params": {
                "dci_weight": 0.4,
                "vortex_weight": 0.3,
                "momentum_weight": 0.3
            }
        }
    }
    
    @classmethod
    def create_strategy(cls, template: str, name: str = None, custom_params: Dict = None) -> Strategy:
        """创建策略"""
        if template not in cls.TEMPLATES:
            raise ValueError(f"未知模板: {template}")
        
        tmpl = cls.TEMPLATES[template]
        params = custom_params or tmpl["params"]
        
        strategy = Strategy(
            id=str(uuid.uuid4())[:8],
            name=name or tmpl["name"],
            strategy_type=tmpl["type"],
            description=f"基于 {tmpl['name']} 模板",
            status=StrategyStatus.TESTING,
            capital_weight=10.0,  # 测试阶段10%权重
            created_at=datetime.now().isoformat(),
            last_update_at=datetime.now().isoformat(),
            params=params
        )
        
        return strategy
    
    @classmethod
    def get_templates(cls) -> List[Dict]:
        """获取所有模板"""
        return [
            {"id": k, "name": v["name"], "type": v["type"].value, "params": v["params"]}
            for k, v in cls.TEMPLATES.items()
        ]


# ============================================================================
# 评分系统
# ============================================================================

class StrategyScorer:
    """策略评分系统"""
    
    def __init__(self):
        self.weights = {
            "profitability": 0.3,
            "consistency": 0.2,
            "risk_adjusted": 0.3,
            "adaptability": 0.2
        }
    
    def calculate_score(self, strategy: Strategy) -> StrategyScore:
        """计算策略综合评分"""
        scores = {
            "profitability": 50.0,
            "consistency": 50.0,
            "risk_adjusted": 50.0,
            "adaptability": 50.0
        }
        reasoning_parts = []
        
        # 盈利能力 (0-30)
        if len(strategy.performance) == 0:
            scores["profitability"] = 60.0
            reasoning_parts.append("新策略，基础分60")
        else:
            pnl = strategy.metrics.total_pnl
            if pnl > 0:
                scores["profitability"] = min(100, 50 + pnl / 100)
                reasoning_parts.append(f"盈利: {pnl:.2f}")
            elif pnl < 0:
                scores["profitability"] = max(20, 50 + pnl / 100)
                reasoning_parts.append(f"亏损: {pnl:.2f}")
            else:
                scores["profitability"] = 50.0
                reasoning_parts.append("盈亏平衡")
        
        # 一致性 (0-20)
        if strategy.metrics.total_trades > 0:
            scores["consistency"] = strategy.metrics.win_rate * 100
            reasoning_parts.append(f"胜率: {strategy.metrics.win_rate*100:.1f}%")
        
        # 风险调整收益 (0-30)
        if len(strategy.performance) >= 5:
            sharpe = strategy.metrics.sharpe_ratio
            scores["risk_adjusted"] = min(100, max(20, sharpe * 10 + 50))
            reasoning_parts.append(f"夏普: {sharpe:.2f}")
        
        # 适应性 (0-20)
        if len(strategy.performance) >= 10:
            recent = strategy.performance[-10:]
            older = strategy.performance[-20:-10] if len(strategy.performance) >= 20 else recent
            if np.mean(older) != 0:
                adapt_ratio = np.mean(recent) / np.mean(older)
                scores["adaptability"] = min(100, max(20, adapt_ratio * 50))
                reasoning_parts.append(f"适应: {adapt_ratio:.2f}x")
        
        # 加权总分 (0-100)
        total = sum(scores[k] * self.weights[k] for k in scores)
        total = min(100, max(0, total))
        
        return StrategyScore(
            strategy_id=strategy.id,
            total_score=total,
            profitability_score=scores["profitability"] * 0.3,
            consistency_score=scores["consistency"] * 0.2,
            risk_adjusted_score=scores["risk_adjusted"] * 0.3,
            adaptability_score=scores["adaptability"] * 0.2,
            reasoning="; ".join(reasoning_parts)
        )
    
    def should_evict(self, score: StrategyScore, strategy: Strategy) -> tuple[bool, str]:
        """判断是否应该淘汰"""
        if score.total_score < 30:
            return True, f"评分过低: {score.total_score:.1f}"
        if strategy.metrics.max_drawdown > 20:
            return True, f"回撤过大: {strategy.metrics.max_drawdown:.1f}%"
        if strategy.metrics.sharpe_ratio < 0.5 and len(strategy.performance) >= 10:
            return True, f"夏普过低: {strategy.metrics.sharpe_ratio:.2f}"
        return False, "正常"


# ============================================================================
# 淘汰机制
# ============================================================================

class EvictionManager:
    """策略淘汰管理器"""
    
    def __init__(self, min_score: float = 30.0, dormancy_score: float = 50.0):
        self.min_score = min_score
        self.dormancy_score = dormancy_score
        self.scorer = StrategyScorer()
        self.events: List[EvictionEvent] = []
    
    def evaluate_strategy(self, strategy: Strategy) -> tuple[str, EvictionEvent]:
        """评估策略并返回动作"""
        score = self.scorer.calculate_score(strategy)
        should_evict, reason = self.scorer.should_evict(score, strategy)
        
        old_status = strategy.status
        old_score = score.total_score
        
        if should_evict:
            if score.total_score < 20:
                action = "dead"
                strategy.status = StrategyStatus.DEAD
                strategy.capital_weight = 0
            else:
                action = "dormant"
                strategy.status = StrategyStatus.DORMANT
                strategy.capital_weight = max(0, strategy.capital_weight * 0.5)
        elif score.total_score > self.dormancy_score and strategy.status == StrategyStatus.DORMANT:
            action = "activate"
            strategy.status = StrategyStatus.ALIVE
        else:
            action = "keep"
        
        event = EvictionEvent(
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            action=action,
            score_before=old_score,
            score_after=score.total_score if action != "keep" else old_score,
            reason=reason,
            timestamp=datetime.now().isoformat()
        )
        
        self.events.append(event)
        strategy.last_update_at = datetime.now().isoformat()
        
        return action, event
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """获取最近的淘汰事件"""
        return [e.to_dict() for e in self.events[-limit:]]


# ============================================================================
# 回测引擎 (简化版)
# ============================================================================

class BacktestEngine:
    """简化的回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        self.position = 0
        self.cash = config.initial_capital
        self.equity = config.initial_capital
        self.peak_equity = config.initial_capital
        self.max_drawdown = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def run(self, prices: List[float], strategy_func) -> BacktestResult:
        """运行回测"""
        self.trades = []
        self.equity_curve = []
        self.position = 0
        self.cash = self.config.initial_capital
        self.equity = self.config.initial_capital
        self.peak_equity = self.config.initial_capital
        self.max_drawdown = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        entry_price = 0
        entry_time = ""
        
        for i, price in enumerate(prices):
            # 生成信号
            signal = strategy_func(prices[:i+1], self.position)
            
            # 记录权益
            self.equity = self.cash + self.position * price
            self.equity_curve.append({
                "index": i,
                "price": price,
                "equity": self.equity,
                "position": self.position,
                "timestamp": i
            })
            
            # 更新峰值和回撤
            if self.equity > self.peak_equity:
                self.peak_equity = self.equity
            drawdown = (self.peak_equity - self.equity) / self.peak_equity * 100
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
            
            # 交易逻辑
            if signal > 0.5 and self.position == 0:  # 买入
                entry_price = price * (1 + self.config.slippage_bps / 10000)
                cost = self.cash * 0.95  # 保留5%手续费
                self.position = cost / entry_price
                self.cash -= cost
                entry_time = f"index_{i}"
                
            elif signal < -0.5 and self.position > 0:  # 卖出
                exit_price = price * (1 - self.config.slippage_bps / 10000)
                pnl = (exit_price - entry_price) / entry_price * 100
                
                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
                
                self.trades.append({
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": f"index_{i}",
                    "exit_price": exit_price,
                    "pnl_pct": pnl,
                    "pnl_value": self.position * (exit_price - entry_price)
                })
                
                self.cash += self.position * exit_price
                self.position = 0
        
        # 计算最终结果
        final_equity = self.cash + self.position * prices[-1] if self.position > 0 else self.cash
        total_pnl = final_equity - self.config.initial_capital
        return_pct = total_pnl / self.config.initial_capital * 100
        total_trades = len(self.trades)
        win_rate = self.winning_trades / total_trades if total_trades > 0 else 0
        
        # 计算夏普比率
        returns = [t["pnl_pct"] / 100 for t in self.trades] if self.trades else [0]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # 盈亏比
        winning_pnl = [t["pnl_pct"] for t in self.trades if t["pnl_pct"] > 0]
        losing_pnl = [abs(t["pnl_pct"]) for t in self.trades if t["pnl_pct"] < 0]
        profit_factor = np.mean(winning_pnl) / np.mean(losing_pnl) if winning_pnl and losing_pnl else 0
        
        return BacktestResult(
            strategy_id=self.config.strategy_id,
            initial_capital=self.config.initial_capital,
            final_equity=final_equity,
            total_pnl=total_pnl,
            return_pct=return_pct,
            sharpe_ratio=sharpe,
            max_drawdown=self.max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            trades=self.trades,
            equity_curve=self.equity_curve
        )


# ============================================================================
# 策略服务 (主类)
# ============================================================================

class StrategyService:
    """策略服务 - 统一管理所有策略功能"""
    
    def __init__(self, db_path: str = None):
        self.strategies: Dict[str, Strategy] = {}
        self.scorer = StrategyScorer()
        self.eviction_manager = EvictionManager()
        self.db_path = db_path or ":memory:"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT,
                data TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _save_to_db(self, strategy: Strategy):
        """保存策略到数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO strategies (id, data, updated_at)
            VALUES (?, ?, ?)
        """, (strategy.id, json.dumps(strategy.to_dict()), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """从数据库加载策略"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM strategies")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            data = json.loads(row[0])
            strategy = Strategy.from_dict(data)
            self.strategies[strategy.id] = strategy
    
    # ---- 策略管理 ----
    
    def create_strategy(self, template: str, name: str = None, params: Dict = None) -> Strategy:
        """创建新策略"""
        strategy = StrategyFactory.create_strategy(template, name, params)
        self.strategies[strategy.id] = strategy
        self._save_to_db(strategy)
        logger.info(f"创建策略: {strategy.name} ({strategy.id})")
        return strategy
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """获取策略"""
        return self.strategies.get(strategy_id)
    
    def list_strategies(self, status: StrategyStatus = None) -> List[Strategy]:
        """列出策略"""
        if status:
            return [s for s in self.strategies.values() if s.status == status]
        return list(self.strategies.values())
    
    def update_strategy(self, strategy_id: str, updates: Dict) -> Optional[Strategy]:
        """更新策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        if "name" in updates:
            strategy.name = updates["name"]
        if "params" in updates:
            strategy.params.update(updates["params"])
        if "capital_weight" in updates:
            strategy.capital_weight = updates["capital_weight"]
        if "status" in updates:
            strategy.status = StrategyStatus(updates["status"])
        
        strategy.last_update_at = datetime.now().isoformat()
        self._save_to_db(strategy)
        return strategy
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
            conn.commit()
            conn.close()
            return True
        return False
    
    # ---- 回测 ----
    
    def run_backtest(self, strategy_id: str, prices: List[float], 
                     config: BacktestConfig = None) -> Optional[BacktestResult]:
        """运行回测"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        if not config:
            config = BacktestConfig(strategy_id=strategy_id)
        
        # 根据策略类型选择回测函数
        def strategy_func(price_history, position):
            if len(price_history) < 20:
                return 0
            return self._generate_signal(strategy, price_history)
        
        engine = BacktestEngine(config)
        result = engine.run(prices, strategy_func)
        
        # 更新策略表现
        strategy.metrics.sharpe_ratio = result.sharpe_ratio
        strategy.metrics.max_drawdown = result.max_drawdown
        strategy.metrics.win_rate = result.win_rate
        strategy.metrics.profit_factor = result.profit_factor
        strategy.metrics.total_trades = result.total_trades
        strategy.metrics.total_pnl = result.total_pnl
        strategy.performance.append(result.return_pct)
        strategy.last_update_at = datetime.now().isoformat()
        
        # 保存回测结果
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO backtest_results (strategy_id, data, created_at)
            VALUES (?, ?, ?)
        """, (strategy_id, json.dumps(result.to_dict()), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        self._save_to_db(strategy)
        logger.info(f"回测完成: {strategy.name}, 收益: {result.return_pct:.2f}%, 夏普: {result.sharpe_ratio:.2f}")
        
        return result
    
    def _generate_signal(self, strategy: Strategy, prices: List[float]) -> float:
        """根据策略类型生成信号"""
        if len(prices) < 20:
            return 0
        
        p = np.array(prices)
        
        if strategy.strategy_type == StrategyType.TREND:
            # 均线交叉
            params = strategy.params
            fast = np.mean(p[-params.get("fast_period", 10):])
            slow = np.mean(p[-params.get("slow_period", 30):])
            if fast > slow:
                return 1.0
            elif fast < slow:
                return -1.0
            return 0
        
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            # 布林带
            params = strategy.params
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            if len(p) < period:
                return 0
            middle = np.mean(p[-period:])
            std = np.std(p[-period:])
            current = p[-1]
            
            if current < middle - std_dev * std:
                return 1.0
            elif current > middle + std_dev * std:
                return -1.0
            return 0
        
        elif strategy.strategy_type == StrategyType.MOMENTUM:
            # ROC动量
            params = strategy.params
            period = params.get("roc_period", 10)
            threshold = params.get("threshold", 2.0)
            if len(p) < period + 1:
                return 0
            roc = (p[-1] - p[-period-1]) / p[-period-1] * 100
            if roc > threshold:
                return 1.0
            elif roc < -threshold:
                return -1.0
            return 0
        
        elif strategy.strategy_type == StrategyType.NEMT:
            # NEMT DCI
            params = strategy.params
            period = params.get("dci_period", 24)
            if len(p) < period:
                return 0
            
            # 简化的DCI计算
            returns = np.diff(p[-period:])
            up = np.sum(returns > 0)
            down = np.sum(returns < 0)
            dci = max(up, down) / period
            
            if dci > params.get("dci_threshold", 0.65):
                return 1.0 if np.mean(returns) > 0 else -1.0
            return 0
        
        return 0
    
    # ---- 评分与淘汰 ----
    
    def score_strategy(self, strategy_id: str) -> Optional[StrategyScore]:
        """评分策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        return self.scorer.calculate_score(strategy)
    
    def score_all(self) -> List[StrategyScore]:
        """评分所有策略"""
        return [self.scorer.calculate_score(s) for s in self.strategies.values()]
    
    def evaluate_and_evict(self, strategy_id: str = None) -> List[EvictionEvent]:
        """评估并淘汰策略"""
        events = []
        
        if strategy_id:
            strategy = self.strategies.get(strategy_id)
            if strategy:
                _, event = self.eviction_manager.evaluate_strategy(strategy)
                events.append(event)
                self._save_to_db(strategy)
        else:
            for strategy in self.strategies.values():
                _, event = self.eviction_manager.evaluate_strategy(strategy)
                events.append(event)
                self._save_to_db(strategy)
        
        return events
    
    def get_eviction_events(self, limit: int = 10) -> List[Dict]:
        """获取淘汰事件"""
        return self.eviction_manager.get_recent_events(limit)
    
    # ---- 权重分配 ----
    
    def rebalance_weights(self, mode: str = "equal") -> Dict[str, float]:
        """重新分配权重"""
        active = [s for s in self.strategies.values() if s.status == StrategyStatus.ALIVE]
        if not active:
            return {}
        
        if mode == "equal":
            weight = 100.0 / len(active)
            for s in active:
                s.capital_weight = weight
        elif mode == "score":
            total_score = sum(self.scorer.calculate_score(s).total_score for s in active)
            for s in active:
                score = self.scorer.calculate_score(s).total_score
                s.capital_weight = (score / total_score) * 100 if total_score > 0 else 0
        
        for s in active:
            self._save_to_db(s)
        
        return {s.id: s.capital_weight for s in active}
    
    # ---- 统计 ----
    
    def get_stats(self) -> Dict:
        """获取策略统计"""
        total = len(self.strategies)
        alive = len([s for s in self.strategies.values() if s.status == StrategyStatus.ALIVE])
        testing = len([s for s in self.strategies.values() if s.status == StrategyStatus.TESTING])
        dormant = len([s for s in self.strategies.values() if s.status == StrategyStatus.DORMANT])
        dead = len([s for s in self.strategies.values() if s.status == StrategyStatus.DEAD])
        
        scores = self.score_all()
        avg_score = np.mean([s.total_score for s in scores]) if scores else 0
        
        return {
            "total": total,
            "alive": alive,
            "testing": testing,
            "dormant": dormant,
            "dead": dead,
            "avg_score": avg_score
        }
    
    def get_templates(self) -> List[Dict]:
        """获取策略模板"""
        return StrategyFactory.get_templates()


# ============================================================================
# 便捷函数
# ============================================================================

def create_service(db_path: str = None) -> StrategyService:
    """创建策略服务"""
    return StrategyService(db_path)


if __name__ == "__main__":
    # 测试
    service = create_service("strategy_test.db")
    
    # 创建策略
    s1 = service.create_strategy("nemt_dci", "DCI策略")
    s2 = service.create_strategy("trend_ma", "均线策略")
    s3 = service.create_strategy("momentum_roc", "动量策略")
    
    # 生成模拟数据
    np.random.seed(42)
    prices = 67000 + np.cumsum(np.random.randn(500) * 100)
    
    # 回测
    result = service.run_backtest(s1.id, prices)
    print(f"回测结果: 收益 {result.return_pct:.2f}%, 夏普 {result.sharpe_ratio:.2f}")
    
    # 评分
    scores = service.score_all()
    for score in scores:
        print(f"策略 {score.strategy_id}: 评分 {score.total_score:.1f}")
    
    # 统计
    stats = service.get_stats()
    print(f"统计: {stats}")
