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
模型层服务集成模块 - 支线2
=================================
将NEMT模型节点与API服务集成，提供完整的量化分析API。

功能：
1. 模型推理API - 单次/批量推理
2. 实时分析 - 实时市场分析
3. 历史回测 - 历史数据分析
4. 策略推荐 - 基于相位的策略建议

作者：NEMT Lab
日期：2026-04-19
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入模块
try:
    from nemt_model_node import NEMTModelNode, ModelNodeConfig, ModelInput, ModelOutput
    from enhanced_phase_detector import EnhancedPhaseDetector, Phase, PhaseAnalysisResult
    from high_performance_nls import HighPerformanceNLSSolver, NLSSolverConfig, NLSMethod
    CORE_IMPORTED = True
except ImportError as e:
    logger.warning(f"核心模块导入失败: {e}")
    CORE_IMPORTED = False


class AnalysisMode(Enum):
    """分析模式"""
    FAST = "fast"           # 快速分析
    STANDARD = "standard"    # 标准分析
    COMPREHENSIVE = "comprehensive"  # 全面分析


@dataclass
class AnalysisRequest:
    """分析请求"""
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    
    # 价格数据
    prices: List[float] = None
    
    # 可选数据
    volumes: Optional[List[float]] = None
    oi_values: Optional[List[float]] = None
    funding_rates: Optional[List[float]] = None
    bbw_history: Optional[List[float]] = None
    
    # 链上数据
    mvrv_zscore: Optional[float] = None
    nupl: Optional[float] = None
    lth_ratio: Optional[float] = None
    sth_ratio: Optional[float] = None
    
    # 分析选项
    mode: AnalysisMode = AnalysisMode.STANDARD
    use_cache: bool = True
    
    def __post_init__(self):
        if self.prices is None:
            self.prices = []


@dataclass
class AnalysisResponse:
    """分析响应"""
    success: bool = False
    error: str = ""
    
    # 基本信息
    symbol: str = ""
    interval: str = ""
    timestamp: str = ""
    execution_time: float = 0.0
    
    # 相位分析
    phase: str = ""
    phase_name: str = ""
    phase_confidence: float = 0.0
    phase_distribution: Dict[str, float] = None
    
    # 核心指标
    dci: float = 0.0
    dci_noise_state: str = ""
    spectral_width: float = 0.0
    mean_frequency: float = 0.0
    resonance_peaks: List[Dict] = None
    vortex_score: float = 0.0
    resonance_confidence: float = 0.0
    
    # 链上健康
    onchain_health_score: int = 0
    
    # 策略建议
    strategy: Dict[str, Any] = None
    
    # 预警
    transition_warning: Optional[Dict] = None
    
    # 原始输出
    raw_output: Optional[Dict] = None
    
    def __post_init__(self):
        if self.phase_distribution is None:
            self.phase_distribution = {}
        if self.resonance_peaks is None:
            self.resonance_peaks = []
        if self.strategy is None:
            self.strategy = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'error': self.error,
            'symbol': self.symbol,
            'interval': self.interval,
            'timestamp': self.timestamp,
            'execution_time': self.execution_time,
            'phase': {
                'current': self.phase,
                'name': self.phase_name,
                'confidence': self.phase_confidence,
                'distribution': self.phase_distribution,
            },
            'indicators': {
                'dci': self.dci,
                'dci_noise_state': self.dci_noise_state,
                'spectral_width': self.spectral_width,
                'mean_frequency': self.mean_frequency,
                'resonance_peaks': self.resonance_peaks,
                'vortex_score': self.vortex_score,
                'resonance_confidence': self.resonance_confidence,
            },
            'onchain_health_score': self.onchain_health_score,
            'strategy': self.strategy,
            'transition_warning': self.transition_warning,
        }


@dataclass
class BatchAnalysisResponse:
    """批量分析响应"""
    success: bool = False
    total: int = 0
    successful: int = 0
    failed: int = 0
    total_execution_time: float = 0.0
    results: List[AnalysisResponse] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'total': self.total,
            'successful': self.successful,
            'failed': self.failed,
            'total_execution_time': self.total_execution_time,
            'avg_execution_time': self.total_execution_time / self.total if self.total > 0 else 0,
            'results': [r.to_dict() for r in self.results],
        }


class ModelService:
    """
    模型服务 - 支线2核心服务
    
    提供完整的量化分析功能
    """
    
    def __init__(self, config: Optional[ModelNodeConfig] = None):
        self._config = config or ModelNodeConfig()
        self._model_node: Optional[NEMTModelNode] = None
        self._phase_detector: Optional[EnhancedPhaseDetector] = None
        self._nls_solver: Optional[HighPerformanceNLSSolver] = None
        self._initialized = False
        
        # 初始化组件
        self._initialize()
    
    def _initialize(self):
        """初始化服务组件"""
        if not CORE_IMPORTED:
            logger.warning("核心模块未导入，服务使用降级模式")
            return
        
        try:
            self._model_node = NEMTModelNode(self._config)
            self._phase_detector = EnhancedPhaseDetector()
            self._nls_solver = HighPerformanceNLSSolver(
                NLSSolverConfig(steps=200)
            )
            self._initialized = True
            logger.info("✅ 模型服务初始化完成")
        except Exception as e:
            logger.error(f"模型服务初始化失败: {e}")
            self._initialized = False
    
    @property
    def is_ready(self) -> bool:
        """检查服务是否就绪"""
        return self._initialized and CORE_IMPORTED
    
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        执行市场分析
        
        Args:
            request: 分析请求
            
        Returns:
            AnalysisResponse
        """
        response = AnalysisResponse()
        response.symbol = request.symbol
        response.interval = request.interval
        response.timestamp = datetime.now().isoformat()
        
        start_time = time.time()
        
        # 验证数据
        if not request.prices or len(request.prices) < 10:
            response.error = "数据不足，至少需要10个价格点"
            return response
        
        try:
            if CORE_IMPORTED and self._model_node:
                # 使用完整模型
                response = self._analyze_full(request)
            else:
                # 降级模式
                response = self._analyze_fallback(request)
            
            response.success = True
            
        except Exception as e:
            response.error = str(e)
            logger.error(f"分析失败: {e}")
        
        response.execution_time = time.time() - start_time
        return response
    
    def _analyze_full(self, request: AnalysisRequest) -> AnalysisResponse:
        """完整分析流程"""
        response = AnalysisResponse()
        
        # 1. 模型节点推理
        input_data = ModelInput(
            prices=request.prices,
            volumes=request.volumes,
            oi_values=request.oi_values,
            funding_rates=request.funding_rates,
            bbw_history=request.bbw_history,
            mvrv_zscore=request.mvrv_zscore,
            nupl=request.nupl,
            lth_ratio=request.lth_ratio,
            sth_ratio=request.sth_ratio,
            symbol=request.symbol,
            interval=request.interval,
        )
        
        model_output = self._model_node.run(input_data)
        
        # 填充响应
        response.phase = model_output.phase.value
        response.phase_name = self._get_phase_name(model_output.phase)
        response.phase_confidence = model_output.phase_confidence
        response.phase_distribution = model_output.phase_distribution
        
        response.dci = model_output.dci_value
        response.dci_noise_state = model_output.dci_noise_state
        response.spectral_width = model_output.spectral_width
        response.mean_frequency = model_output.mean_frequency
        response.resonance_peaks = model_output.resonance_peaks
        response.vortex_score = model_output.vortex_score
        response.resonance_confidence = model_output.resonance_confidence
        
        response.onchain_health_score = model_output.onchain_health_score
        response.strategy = model_output.strategy_metrics
        
        response.raw_output = model_output.to_dict()
        
        # 2. 增强相位检测
        phase_result = self._phase_detector.analyze(
            np.array(request.prices),
            np.array(request.volumes) if request.volumes else None,
            model_output.dci_value,
            model_output.spectral_width,
            model_output.vortex_score,
            model_output.resonance_confidence
        )
        
        # 更新预警
        if phase_result.transition_warning:
            response.transition_warning = {
                'current': phase_result.phase.value,
                'likely_next': phase_result.transition_warning.likely_next_phase.value,
                'confidence': phase_result.transition_warning.confidence,
                'time_remaining': phase_result.transition_warning.time_remaining,
            }
        
        return response
    
    def _analyze_fallback(self, request: AnalysisRequest) -> AnalysisResponse:
        """降级分析流程"""
        response = AnalysisResponse()
        prices = np.array(request.prices)
        
        # 简单DCI
        returns = np.diff(prices)
        up_count = np.sum(returns > 0)
        down_count = np.sum(returns < 0)
        response.dci = max(up_count, down_count) / len(returns) if len(returns) > 0 else 0.5
        
        # 简单谱宽
        fft_result = np.fft.fft(returns - np.mean(returns))
        response.spectral_width = float(np.std(np.abs(fft_result)))
        
        # 默认相位
        if response.dci > 0.65:
            response.phase = "D"
            response.phase_name = "趋势运行期"
        elif response.dci < 0.55:
            response.phase = "A"
            response.phase_name = "高噪声混乱期"
        else:
            response.phase = "B"
            response.phase_name = "涡旋蓄力期"
        
        response.phase_confidence = 0.5
        response.strategy = {
            'position_ratio': 0.3,
            'max_position': 0.5,
            'single_risk': 0.02,
            'leverage': 1,
        }
        
        return response
    
    def batch_analyze(self, requests: List[AnalysisRequest]) -> BatchAnalysisResponse:
        """
        批量分析
        
        Args:
            requests: 分析请求列表
            
        Returns:
            BatchAnalysisResponse
        """
        response = BatchAnalysisResponse()
        response.total = len(requests)
        start_time = time.time()
        
        for req in requests:
            result = self.analyze(req)
            response.results.append(result)
            if result.success:
                response.successful += 1
            else:
                response.failed += 1
        
        response.total_execution_time = time.time() - start_time
        response.success = response.failed == 0
        
        return response
    
    def run_backtest(
        self,
        prices: List[float],
        strategy_func=None
    ) -> Dict[str, Any]:
        """
        简单回测
        
        Args:
            prices: 价格序列
            strategy_func: 策略函数 (可选)
            
        Returns:
            回测结果
        """
        if strategy_func is None:
            strategy_func = self._default_strategy
        
        results = []
        positions = []
        capital = 10000  # 初始资金
        position = 0
        
        for i in range(20, len(prices)):
            signal = strategy_func(prices[:i])
            
            if signal == 'buy' and position == 0:
                position = capital / prices[i] * 0.95  # 买入95%资金
                capital = capital * 0.05
                positions.append({'action': 'buy', 'price': prices[i], 'time': i})
            
            elif signal == 'sell' and position > 0:
                capital = position * prices[i] * 0.95  # 卖出95%仓位
                position = 0
                positions.append({'action': 'sell', 'price': prices[i], 'time': i})
        
        # 计算最终价值
        if position > 0:
            final_value = position * prices[-1]
        else:
            final_value = capital
        
        return {
            'initial_capital': 10000,
            'final_value': final_value,
            'return': (final_value - 10000) / 10000,
            'num_trades': len(positions),
            'positions': positions,
        }
    
    def _default_strategy(self, prices: List[float]) -> str:
        """默认策略"""
        if len(prices) < 20:
            return 'hold'
        
        prices_arr = np.array(prices[-20:])
        returns = np.diff(prices_arr)
        up_count = np.sum(returns > 0)
        dci = up_count / len(returns)
        
        if dci > 0.7:
            return 'buy'
        elif dci < 0.4:
            return 'sell'
        else:
            return 'hold'
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            'service': 'NEMT Model Service',
            'version': '1.0',
            'ready': self.is_ready,
            'core_imported': CORE_IMPORTED,
            'timestamp': datetime.now().isoformat(),
        }
        
        if self._model_node and self.is_ready:
            status['metrics'] = self._model_node.metrics.to_dict()
            status['cache'] = self._model_node.cache_stats
        
        return status
    
    def _get_phase_name(self, phase) -> str:
        """获取相位名称"""
        names = {
            'A': '高噪声混乱期',
            'B': '涡旋蓄力期',
            'C': '临界爆发前夜',
            'D': '趋势运行期'
        }
        return names.get(phase.value if hasattr(phase, 'value') else str(phase), '未知')


# ============================================================================
# 全局服务实例
# ============================================================================

_service: Optional[ModelService] = None


def get_service(config: Optional[ModelNodeConfig] = None) -> ModelService:
    """获取模型服务单例"""
    global _service
    if _service is None:
        _service = ModelService(config)
    return _service


def analyze_market(request: AnalysisRequest) -> AnalysisResponse:
    """便捷函数：分析市场"""
    service = get_service()
    return service.analyze(request)


def batch_analyze_market(requests: List[AnalysisRequest]) -> BatchAnalysisResponse:
    """便捷函数：批量分析市场"""
    service = get_service()
    return service.batch_analyze(requests)


# ============================================================================
# API路由
# ============================================================================

def create_api_handlers():
    """创建API处理器（供api_server使用）"""
    
    def handle_analyze(request_data: Dict) -> Dict:
        """处理分析请求"""
        request = AnalysisRequest(
            symbol=request_data.get('symbol', 'BTCUSDT'),
            interval=request_data.get('interval', '1m'),
            prices=request_data.get('prices', []),
            volumes=request_data.get('volumes'),
            oi_values=request_data.get('oi_values'),
            funding_rates=request_data.get('funding_rates'),
            bbw_history=request_data.get('bbw_history'),
            mvrv_zscore=request_data.get('mvrv_zscore'),
            nupl=request_data.get('nupl'),
        )
        
        response = analyze_market(request)
        return response.to_dict()
    
    def handle_batch_analyze(request_data: Dict) -> Dict:
        """处理批量分析请求"""
        requests = [
            AnalysisRequest(**req) for req in request_data.get('requests', [])
        ]
        
        response = batch_analyze_market(requests)
        return response.to_dict()
    
    def handle_status() -> Dict:
        """处理状态查询"""
        service = get_service()
        return service.get_status()
    
    return {
        'analyze': handle_analyze,
        'batch_analyze': handle_batch_analyze,
        'status': handle_status,
    }


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("=" * 70)
    print("NEMT模型服务 - 支线2集成测试")
    print("=" * 70)
    
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
    
    volumes = [1000 + 500 * np.random.randn() for _ in range(500)]
    
    # 创建服务
    service = ModelService()
    
    # 打印状态
    print("\n[1] 服务状态")
    print("-" * 70)
    status = service.get_status()
    print(f"  服务就绪: {'✅' if status['ready'] else '❌'}")
    print(f"  核心模块: {'✅ 已导入' if status['core_imported'] else '❌ 未导入'}")
    
    if status.get('metrics'):
        m = status['metrics']
        print(f"  总调用: {m['total_calls']}")
        print(f"  成功率: {m['success_rate']}")
        print(f"  平均耗时: {float(m['avg_execution_time'])*1000:.1f}ms")
    
    # 单次分析
    print("\n[2] 单次市场分析")
    print("-" * 70)
    
    request = AnalysisRequest(
        symbol="BTCUSDT",
        interval="1m",
        prices=prices,
        volumes=volumes,
        mode=AnalysisMode.STANDARD
    )
    
    response = service.analyze(request)
    
    print(f"状态: {'✅ 成功' if response.success else '❌ 失败'}")
    if response.error:
        print(f"错误: {response.error}")
    else:
        print(f"执行时间: {response.execution_time*1000:.1f}ms")
        print(f"相位: [{response.phase}] {response.phase_name}")
        print(f"置信度: {response.phase_confidence:.1%}")
        print(f"DCI: {response.dci:.3f} ({response.dci_noise_state}噪声)")
        print(f"谱宽: {response.spectral_width:.6f}")
        print(f"共振峰: {len(response.resonance_peaks)}个")
        
        if response.strategy:
            print(f"\n策略建议:")
            print(f"  仓位上限: {response.strategy.get('max_position', 0):.0%}")
            print(f"  单笔风险: {response.strategy.get('single_risk', 0):.1%}")
            print(f"  策略: {response.strategy.get('strategy', 'N/A')[:50]}...")
        
        if response.transition_warning:
            tw = response.transition_warning
            print(f"\n相位预警:")
            print(f"  可能转换: {tw['likely_next']}")
            print(f"  置信度: {tw['confidence']:.1%}")
            print(f"  预计时间: {tw['time_remaining']}根K线")
    
    # 批量分析
    print("\n[3] 批量分析 (3个请求)")
    print("-" * 70)
    
    batch_requests = [
        AnalysisRequest(symbol="BTCUSDT", interval="1m", prices=prices[:400]),
        AnalysisRequest(symbol="ETHUSDT", interval="5m", prices=prices[50:450]),
        AnalysisRequest(symbol="BTCUSDT", interval="15m", prices=prices[100:500]),
    ]
    
    batch_response = service.batch_analyze(batch_requests)
    
    print(f"批量分析结果:")
    print(f"  总数: {batch_response.total}")
    print(f"  成功: {batch_response.successful}")
    print(f"  失败: {batch_response.failed}")
    print(f"  总耗时: {batch_response.total_execution_time*1000:.1f}ms")
    print(f"  平均耗时: {batch_response.total_execution_time/batch_response.total*1000:.1f}ms")
    
    for i, r in enumerate(batch_response.results):
        print(f"  [{i+1}] {r.symbol} ({r.interval}): [{r.phase}] {r.phase_name}")
    
    # 回测
    print("\n[4] 简单回测")
    print("-" * 70)
    
    backtest_result = service.run_backtest(prices)
    print(f"回测结果:")
    print(f"  初始资金: ${backtest_result['initial_capital']:,.2f}")
    print(f"  最终价值: ${backtest_result['final_value']:,.2f}")
    print(f"  收益率: {backtest_result['return']:.2%}")
    print(f"  交易次数: {backtest_result['num_trades']}")
    
    print("\n✅ 测试完成")
    print("=" * 70)
