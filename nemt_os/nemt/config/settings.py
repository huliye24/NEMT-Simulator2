"""
NEMT 配置管理模块
使用 dataclasses 和 YAML 进行配置管理
"""

import yaml
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class DataConfig:
    """数据配置"""
    path: str = "data/BTCUSDT-1h.csv"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbol: str = "BTC/USDT"


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 10000.0
    slippage_bps: float = 1.0  # 滑点，单位：基点
    commission_bps: float = 5.0  # 手续费，单位：基点
    random_seed: int = 42  # 随机种子，确保可复现


@dataclass
class RiskConfig:
    """风控配置"""
    max_drawdown_pct: float = 0.30  # 最大回撤 30%
    daily_loss_limit_pct: float = 0.10  # 日亏损限制 10%
    strategy_exposure_cap: float = 0.5  # 单策略最大仓位 50%
    market_exposure_cap: float = 0.8  # 单市场最大仓位 80%

    # 风控状态阈值 - more lenient for testing
    caution_threshold: float = 0.10  # 回撤 > 10% 进入 Caution
    defense_threshold: float = 0.20  # 回撤 > 20% 进入 Defense
    shutdown_threshold: float = 0.30  # 回撤 > 30% 进入 Shutdown


@dataclass
class EvolutionConfig:
    """进化配置"""
    eval_frequency: int = 20  # 每 N 个 bar 评分一次
    keep_best: int = 3  # 保留前 N 名策略
    min_score_threshold: float = 30.0  # 淘汰分数阈值
    mutation_rate: float = 0.1  # 参数变异率


@dataclass
class StrategyWeightConfig:
    """策略权重配置"""
    equal_weight: bool = True  # 是否使用等权重
    lookback_days: int = 20  # 回顾天数


@dataclass
class NEMTConfig:
    """NEMT 主配置"""
    data: DataConfig = field(default_factory=DataConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    strategy_weight: StrategyWeightConfig = field(default_factory=StrategyWeightConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "NEMTConfig":
        """从 YAML 文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: dict) -> "NEMTConfig":
        """从字典创建配置对象"""
        data_config = DataConfig(**config_dict.get('data', {}))
        backtest_config = BacktestConfig(**config_dict.get('backtest', {}))
        risk_config = RiskConfig(**config_dict.get('risk', {}))
        evolution_config = EvolutionConfig(**config_dict.get('evolution', {}))
        strategy_weight_config = StrategyWeightConfig(**config_dict.get('strategy_weight', {}))

        return cls(
            data=data_config,
            backtest=backtest_config,
            risk=risk_config,
            evolution=evolution_config,
            strategy_weight=strategy_weight_config
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'data': self.data.__dict__,
            'backtest': self.backtest.__dict__,
            'risk': self.risk.__dict__,
            'evolution': self.evolution.__dict__,
            'strategy_weight': self.strategy_weight.__dict__
        }


def load_config(path: str = "config/config.yaml") -> NEMTConfig:
    """加载配置文件"""
    if Path(path).exists():
        return NEMTConfig.from_yaml(path)
    else:
        print(f"\n[INFO] Config file {path} not found, using default")
        return NEMTConfig()


def create_default_config(path: str = "config/config.yaml") -> NEMTConfig:
    """创建默认配置文件"""
    config = NEMTConfig()

    # 确保目录存在
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)

    print(f"Default config created: {path}")
    return config
