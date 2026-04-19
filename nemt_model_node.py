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
NEMT模型层 (Model Node) - 支线2
=================================
NEMT量化系统的核心计算引擎，负责市场数据分析和信号生成。

核心功能：
1. NLS方程求解 - 非线性薛定谔方程数值求解
2. 频谱分析 - FFT频谱分析、谱宽计算、共振峰检测
3. 四相位识别 - A/B/C/D四个市场相位自动识别
4. 信号生成 - DCI/涡旋/随机共振等交易信号

模块依赖：
- nemt_core.py: NEMTSimulator核心模拟器
- nls_solver.py: NumPy实现的NLS求解器
- nemt_signals.py: 信号指标计算
- nemt_state_machine.py: 四相位状态机
- nemt_onchain.py: 链上数据计算

作者：NEMT Lab
日期：2026-04-19
版本：v1.0
"""

import time
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import weakref

import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入内部模块
try:
    from nemt_core import NEMTSimulator, NEMTParams
    from nemt_signals import (
        MarketPhase,
        NEMTSignalIndicators,
        DCISignal,
        VortexConditions,
        ResonanceConditions,
        NEMTSignals
    )
    from nemt_state_machine import NEMTStateMachine, StateMachineConfig
    from nemt_onchain import OnchainCalculator, OnchainHealthScore
    CORE_IMPORTED = True
except ImportError as e:
    logger.warning(f"核心模块导入失败: {e}，使用降级模式")
    CORE_IMPORTED = False


# ============================================================================
# 数据结构定义
# ============================================================================

class ModelStatus(Enum):
    """模型节点状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ModelNodeConfig:
    """模型节点配置"""
    # NLS参数
    alpha: float = 0.1
    beta: float = 1.0
    noise_level: float = 0.2
    dt: float = 0.01
    dx: float = 1.0
    steps: int = 200
    
    # 信号参数
    dci_periods: int = 24
    vortex_conditions_required: int = 3
    
    # 性能优化
    use_cache: bool = True
    max_cache_size: int = 100
    enable_parallel: bool = False
    
    # 精度控制
    spectral_samples: int = 100
    resonance_threshold: float = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModelInput:
    """模型输入数据"""
    prices: List[float]
    volumes: Optional[List[float]] = None
    oi_values: Optional[List[float]] = None
    funding_rates: Optional[List[float]] = None
    bbw_history: Optional[List[float]] = None
    
    # 链上数据（可选）
    mvrv_zscore: Optional[float] = None
    nupl: Optional[float] = None
    lth_ratio: Optional[float] = None
    sth_ratio: Optional[float] = None
    
    # 元数据
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ModelOutput:
    """模型输出数据"""
    # 状态
    success: bool = False
    status: ModelStatus = ModelStatus.IDLE
    error: str = ""
    execution_time: float = 0.0
    
    # NLS分析结果
    spectral_width: float = 0.0
    mean_frequency: float = 0.0
    resonance_peaks: List[Dict] = field(default_factory=list)
    frequencies: List[float] = field(default_factory=list)
    spectrum: List[float] = field(default_factory=list)
    
    # 四相位识别
    phase: MarketPhase = MarketPhase.PHASE_A_NOISE
    phase_confidence: float = 0.0
    phase_distribution: Dict[str, float] = field(default_factory=dict)
    
    # 信号指标
    dci_value: float = 0.0
    dci_noise_state: str = "medium"
    vortex_score: float = 0.0
    resonance_confidence: float = 0.0
    
    # 链上健康评分
    onchain_health_score: int = 0
    
    @property
    def phase_name(self) -> str:
        """获取相位名称"""
        names = {
            "A": "高噪声混乱期",
            "B": "涡旋蓄力期",
            "C": "临界爆发前夜",
            "D": "趋势运行期"
        }
        phase_value = self.phase.value if hasattr(self.phase, 'value') else str(self.phase)
        return names.get(phase_value, "未知")
    
    # 策略建议
    strategy_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    symbol: str = ""
    interval: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'success': self.success,
            'status': self.status.value,
            'error': self.error,
            'execution_time': self.execution_time,
            'spectral_width': self.spectral_width,
            'mean_frequency': self.mean_frequency,
            'resonance_peaks': self.resonance_peaks[:10],
            'phase': self.phase.value,
            'phase_name': self._get_phase_name(),
            'phase_confidence': self.phase_confidence,
            'phase_distribution': self.phase_distribution,
            'dci_value': self.dci_value,
            'dci_noise_state': self.dci_noise_state,
            'vortex_score': self.vortex_score,
            'resonance_confidence': self.resonance_confidence,
            'onchain_health_score': self.onchain_health_score,
            'strategy_metrics': self.strategy_metrics,
            'symbol': self.symbol,
            'interval': self.interval,
            'timestamp': self.timestamp,
        }
        return result
    
    def _get_phase_name(self) -> str:
        names = {
            MarketPhase.PHASE_A_NOISE: "高噪声混乱期",
            MarketPhase.PHASE_B_VORTEX: "涡旋蓄力期",
            MarketPhase.PHASE_C_RESONANCE: "临界爆发前夜",
            MarketPhase.PHASE_D_TREND: "趋势运行期"
        }
        return names.get(self.phase, "未知")


@dataclass
class ModelMetrics:
    """模型性能指标"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    # 统计
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'total_execution_time': self.total_execution_time,
            'avg_execution_time': self.avg_execution_time,
            'min_execution_time': self.min_execution_time,
            'max_execution_time': self.max_execution_time,
            'success_rate': f"{self.success_rate:.1%}",
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': f"{self.cache_hit_rate:.1%}",
        }


# ============================================================================
# 缓存管理
# ============================================================================

class ModelCache:
    """模型结果缓存"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, ModelOutput] = {}
        self._access_order: List[str] = []
    
    def _make_key(self, data: ModelInput, config: ModelNodeConfig) -> str:
        """生成缓存键"""
        data_hash = hashlib.md5(str(data.prices[:50]).encode()).hexdigest()
        param_hash = hashlib.md5(f"{config.alpha}_{config.beta}_{config.noise_level}".encode()).hexdigest()
        return f"{data_hash}_{param_hash}"
    
    def get(self, data: ModelInput, config: ModelNodeConfig) -> Optional[ModelOutput]:
        """获取缓存结果"""
        key = self._make_key(data, config)
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, data: ModelInput, config: ModelNodeConfig, result: ModelOutput):
        """设置缓存"""
        key = self._make_key(data, config)
        
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = result
        self._access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def stats(self) -> Dict[str, int]:
        return {'size': len(self._cache), 'max_size': self.max_size}


# ============================================================================
# NEMT模型节点主类
# ============================================================================

class NEMTModelNode:
    """
    NEMT模型节点 - 支线2核心
    
    整合NLS方程求解、频谱分析、四相位识别和信号生成
    提供统一的模型推理接口
    
    使用示例：
        node = NEMTModelNode()
        result = node.run(input_data)
        print(result.phase.value)  # 'A'/'B'/'C'/'D'
    """
    
    # 类级别的缓存和统计
    _cache = ModelCache(max_size=100)
    _metrics = ModelMetrics()
    
    def __init__(self, config: Optional[ModelNodeConfig] = None):
        """
        初始化模型节点
        
        Args:
            config: 模型配置（可选，使用默认配置）
        """
        self.config = config or ModelNodeConfig()
        self._status = ModelStatus.IDLE
        self._last_error: Optional[str] = None
        
        # 内部组件
        self._simulator = None
        self._signal_indicators = None
        self._state_machine = None
        self._onchain_calculator = None
        
        # 初始化内部组件
        self._initialize_components()
        
        logger.info(f"✅ NEMT模型节点已初始化 (缓存: {self._cache.max_size})")
    
    def _initialize_components(self):
        """初始化内部组件"""
        if CORE_IMPORTED:
            # NLS模拟器
            params = NEMTParams(
                alpha=self.config.alpha,
                beta=self.config.beta,
                noise_level=self.config.noise_level,
                dt=self.config.dt,
                dx=self.config.dx,
                steps=self.config.steps
            )
            self._simulator = NEMTSimulator(params)
            
            # 信号指示器
            self._signal_indicators = NEMTSignalIndicators()
            
            # 状态机
            state_config = StateMachineConfig(
                vortex_conditions_required=self.config.vortex_conditions_required
            )
            self._state_machine = NEMTStateMachine(state_config)
            
            # 链上计算器
            self._onchain_calculator = OnchainCalculator()
        else:
            logger.warning("⚠️ 核心模块未导入，使用降级模式")
    
    @property
    def status(self) -> ModelStatus:
        """获取模型状态"""
        return self._status
    
    @property
    def metrics(self) -> ModelMetrics:
        """获取性能指标"""
        return self._metrics
    
    @property
    def cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return self._cache.stats()
    
    def run(self, input_data: ModelInput) -> ModelOutput:
        """
        运行模型推理
        
        Args:
            input_data: 模型输入数据
            
        Returns:
            ModelOutput: 模型输出结果
        """
        start_time = time.time()
        self._status = ModelStatus.RUNNING
        result = ModelOutput()
        result.symbol = input_data.symbol
        result.interval = input_data.interval
        result.timestamp = input_data.timestamp
        
        # 更新统计
        self._metrics.total_calls += 1
        
        # 检查缓存
        if self.config.use_cache:
            cached = self._cache.get(input_data, self.config)
            if cached is not None:
                self._metrics.cache_hits += 1
                result = cached
                result.execution_time = time.time() - start_time
                self._status = ModelStatus.COMPLETED
                logger.debug("📦 使用缓存结果")
                return result
            self._metrics.cache_misses += 1
        
        try:
            if CORE_IMPORTED:
                result = self._run_full_analysis(input_data)
            else:
                result = self._run_fallback_analysis(input_data)
            
            result.success = True
            self._status = ModelStatus.COMPLETED
            
            # 更新统计
            self._metrics.successful_calls += 1
            self._metrics.total_execution_time += result.execution_time
            self._metrics.avg_execution_time = (
                self._metrics.total_execution_time / self._metrics.successful_calls
            )
            self._metrics.min_execution_time = min(
                self._metrics.min_execution_time,
                result.execution_time
            )
            self._metrics.max_execution_time = max(
                self._metrics.max_execution_time,
                result.execution_time
            )
            
            # 缓存结果
            if self.config.use_cache:
                self._cache.set(input_data, self.config, result)
            
        except Exception as e:
            self._status = ModelStatus.ERROR
            self._last_error = str(e)
            result.status = ModelStatus.ERROR
            result.error = self._last_error
            self._metrics.failed_calls += 1
            logger.error(f"模型推理失败: {e}")
        
        result.execution_time = time.time() - start_time
        return result
    
    def _run_full_analysis(self, input_data: ModelInput) -> ModelOutput:
        """完整分析流程"""
        result = ModelOutput()
        prices = np.array(input_data.prices)
        
        # 1. NLS方程求解
        logger.debug("开始NLS求解...")
        self._simulator.initialize_state(prices)
        self._simulator.evolve(self._simulator.psi, self.config.steps)
        
        # 2. 频谱分析
        freqs, spectrum = self._simulator.spectral_analysis()
        spectral_width = self._simulator.compute_spectral_width()
        resonance_info = self._simulator.detect_resonance()
        
        result.spectral_width = float(spectral_width)
        result.mean_frequency = float(self._simulator.mean_frequency)
        result.frequencies = freqs[:self.config.spectral_samples].tolist()
        result.spectrum = spectrum[:self.config.spectral_samples].tolist()
        result.resonance_peaks = [
            {'frequency': float(f), 'amplitude': float(a)}
            for f, a in zip(
                resonance_info['peak_frequencies'][:10],
                resonance_info['peak_amplitudes'][:10]
            )
        ]
        
        # 3. 信号计算
        logger.debug("计算信号指标...")
        
        # DCI计算
        dci = self._signal_indicators.compute_dci(prices)
        result.dci_value = dci.value
        result.dci_noise_state = dci.noise_state
        
        # 涡旋检测（如果数据充足）
        vortex_score = 0.0
        if all(x is not None for x in [
            input_data.volumes, input_data.oi_values,
            input_data.funding_rates, input_data.bbw_history
        ]):
            vortex = self._signal_indicators.detect_vortex(
                prices,
                np.array(input_data.volumes),
                np.array(input_data.oi_values),
                np.array(input_data.funding_rates),
                np.array(input_data.bbw_history)
            )
            vortex_score = vortex.maturity_score
        
        result.vortex_score = float(vortex_score)
        
        # 随机共振检测
        resonance = self._signal_indicators.detect_resonance(
            mvrv_zscore=input_data.mvrv_zscore,
            nupl=input_data.nupl,
            lth_ratio=input_data.lth_ratio,
            sth_ratio=input_data.sth_ratio,
            dci_volatility=self._signal_indicators.compute_dci_volatility(20)
        )
        result.resonance_confidence = resonance.confidence
        
        # 4. 四相位识别
        logger.debug("识别市场相位...")
        signals = NEMTSignals(
            dci=dci,
            vortex=VortexConditions(is_vortex=vortex_score > 5, maturity_score=vortex_score),
            resonance=resonance,
            phase=MarketPhase.PHASE_A_NOISE,
            phase_confidence=0.0,
            spectral_width=result.spectral_width
        )
        
        phase, confidence = self._signal_indicators.determine_phase(
            signals.dci, signals.vortex, signals.resonance
        )
        
        # 使用状态机更新
        new_phase, transition = self._state_machine.update(signals, prices[-1])
        
        result.phase = new_phase
        result.phase_confidence = float(confidence)
        result.phase_distribution = self._state_machine.get_phase_distribution()
        
        # 5. 链上健康评分
        if input_data.mvrv_zscore is not None:
            health = self._onchain_calculator.calculate_health_score(
                input_data.mvrv_zscore, input_data.nupl
            )
            result.onchain_health_score = health.score
        
        # 6. 策略建议
        result.strategy_metrics = self._signal_indicators.compute_phase_metrics(phase)
        
        return result
    
    def _run_fallback_analysis(self, input_data: ModelInput) -> ModelOutput:
        """降级分析模式（无核心模块）"""
        result = ModelOutput()
        prices = np.array(input_data.prices)
        
        if len(prices) < 10:
            result.error = "数据不足"
            return result
        
        # 简单的统计分析作为fallback
        returns = np.diff(prices)
        
        # 简单DCI
        up_count = np.sum(returns > 0)
        down_count = np.sum(returns < 0)
        max_count = max(up_count, down_count)
        result.dci_value = float(max_count / len(returns)) if len(returns) > 0 else 0.5
        
        # 简单谱宽
        fft_result = np.fft.fft(returns - np.mean(returns))
        spectrum_power = np.abs(fft_result) ** 2
        result.spectral_width = float(np.std(spectrum_power))
        
        # 默认相位
        result.phase = MarketPhase.PHASE_A_NOISE
        result.phase_confidence = 0.5
        
        # 简单策略
        result.strategy_metrics = {
            'position_ratio': 0.2,
            'max_position': 0.2,
            'single_risk': 0.01,
            'leverage': 0,
            'strategy': '仅持有长期底仓，不做短线交易（降级模式）'
        }
        
        return result
    
    def batch_run(self, inputs: List[ModelInput]) -> List[ModelOutput]:
        """
        批量运行模型推理
        
        Args:
            inputs: 模型输入列表
            
        Returns:
            模型输出列表
        """
        results = []
        for inp in inputs:
            result = self.run(inp)
            results.append(result)
        return results
    
    def reset_metrics(self):
        """重置性能指标"""
        self._metrics = ModelMetrics()
        logger.info("性能指标已重置")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("缓存已清空")
    
    def get_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'name': 'NEMT Model Node',
            'version': '1.0',
            'core_imported': CORE_IMPORTED,
            'config': self.config.to_dict(),
            'status': self._status.value,
            'metrics': self._metrics.to_dict(),
            'cache': self.cache_stats,
        }


# ============================================================================
# 便捷函数
# ============================================================================

# 全局单例
_model_node: Optional[NEMTModelNode] = None


def get_model_node(config: Optional[ModelNodeConfig] = None) -> NEMTModelNode:
    """获取模型节点单例"""
    global _model_node
    if _model_node is None:
        _model_node = NEMTModelNode(config)
    return _model_node


def run_model(input_data: ModelInput) -> ModelOutput:
    """便捷函数：运行模型推理"""
    node = get_model_node()
    return node.run(input_data)


def run_batch(inputs: List[ModelInput]) -> List[ModelOutput]:
    """便捷函数：批量运行模型推理"""
    node = get_model_node()
    return node.batch_run(inputs)


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("=" * 60)
    print("NEMT模型节点 - 支线2测试")
    print("=" * 60)
    
    # 生成测试数据
    np.random.seed(42)
    t = np.linspace(0, 20, 500)
    prices = (
        50000
        + 2000 * np.sin(0.5 * t)
        + 1500 * np.sin(1.3 * t + 0.3)
        + 500 * np.sin(2.7 * t + 0.7)
        + 300 * np.random.randn(500)
    ).tolist()
    
    # 创建输入
    input_data = ModelInput(
        prices=prices,
        symbol="BTCUSDT",
        interval="1m"
    )
    
    # 创建模型节点
    node = NEMTModelNode()
    
    # 打印信息
    info = node.get_info()
    print(f"\n模型信息:")
    print(f"  版本: {info['version']}")
    print(f"  核心模块: {'已导入' if info['core_imported'] else '降级模式'}")
    print(f"  配置: α={info['config']['alpha']}, β={info['config']['beta']}, steps={info['config']['steps']}")
    
    # 单次推理
    print("\n[1] 单次模型推理...")
    result = node.run(input_data)
    
    print(f"\n结果:")
    print(f"  状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"  耗时: {result.execution_time*1000:.1f}ms")
    print(f"  相位: [{result.phase.value}] {result.phase_name}")
    print(f"  置信度: {result.phase_confidence:.1%}")
    print(f"  DCI: {result.dci_value:.3f} ({result.dci_noise_state}噪声)")
    print(f"  谱宽: {result.spectral_width:.6f}")
    print(f"  共振峰: {len(result.resonance_peaks)}个")
    
    if result.strategy_metrics:
        print(f"\n策略建议:")
        print(f"  仓位上限: {result.strategy_metrics.get('max_position', 0):.0%}")
        print(f"  单笔风险: {result.strategy_metrics.get('single_risk', 0):.1%}")
        print(f"  策略: {result.strategy_metrics.get('strategy', 'N/A')}")
    
    # 性能统计
    metrics = node.metrics
    print(f"\n性能统计:")
    print(f"  总调用: {metrics.total_calls}")
    print(f"  成功率: {metrics.success_rate:.1%}")
    print(f"  平均耗时: {metrics.avg_execution_time*1000:.1f}ms")
    print(f"  缓存命中率: {metrics.cache_hit_rate:.1%}")
    
    # 批量测试
    print("\n[2] 批量测试 (5次)...")
    batch_inputs = [
        ModelInput(prices=prices[:400], symbol="BTCUSDT", interval="1m"),
        ModelInput(prices=prices[50:450], symbol="ETHUSDT", interval="5m"),
        ModelInput(prices=prices[100:500], symbol="BTCUSDT", interval="15m"),
    ]
    
    for i, inp in enumerate(batch_inputs):
        r = node.run(inp)
        print(f"  [{i+1}] {inp.symbol} ({inp.interval}): 相位={r.phase.value}, 耗时={r.execution_time*1000:.1f}ms")
    
    # 缓存测试
    print("\n[3] 缓存测试...")
    print(f"  缓存大小: {node.cache_stats['size']}/{node.cache_stats['max_size']}")
    print(f"  缓存命中: {metrics.cache_hits}, 未命中: {metrics.cache_misses}")
    
    print("\n✅ 测试完成")
    print("=" * 60)
